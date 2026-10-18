from flask import Flask, request
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import ( JWTManager, create_access_token, jwt_required, get_jwt_identity)
from models import db, User, Note

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///productivity.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# JWT configuration
app.config["JWT_SECRET_KEY"] = "dev-secret-key-change-before-deployment"

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


@app.route("/")
def home():
    return {"message": "Productivity API is running!"}


@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")
    password_confirmation = data.get("password_confirmation", "")

    # Check that all required fields are provided
    if not username or not password or not password_confirmation:
        return {
            "errors": [
                "Username, password, and password confirmation are required."
            ]
        }, 400

    # Check that the passwords match
    if password != password_confirmation:
        return {
            "errors": ["Passwords do not match."]
        }, 400

    # Check whether the username already exists
    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return {
            "errors": ["Username already exists."]
        }, 409

    # Hash the password before saving it
    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    # Create a new user
    new_user = User(
        username=username,
        password_hash=password_hash
    )

    db.session.add(new_user)
    db.session.commit()

    # Generate a JWT token for the new user
    token = create_access_token(identity=str(new_user.id))

    # Return the token and user information
    return {
        "token": token,
        "user": {
            "id": new_user.id,
            "username": new_user.username
        }
    }, 201
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return {
            "errors": ["Username and password are required."]
        }, 400

    user = User.query.filter_by(username=username).first()

    if user is None or not bcrypt.check_password_hash(
        user.password_hash, password
    ):
        return {
            "errors": ["Invalid username or password."]
        }, 401

    token = create_access_token(identity=str(user.id))

    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username
        }
    }, 200
@app.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())

    user = db.session.get(User, user_id)

    if user is None:
        return {"error": "User not found."}, 404

    return {
        "id": user.id,
        "username": user.username
    }, 200
@app.route("/notes", methods=["POST"])
@jwt_required()
def create_note():
    user_id = int(get_jwt_identity())

    data = request.get_json() or {}

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title or not content:
        return {
            "error": "Title and content are required."
        }, 400

    new_note = Note(
        title=title,
        content=content,
        user_id=user_id
    )

    # Save the note to the database
    db.session.add(new_note)
    db.session.commit()

    # Return the newly created note
    return {
        "id": new_note.id,
        "title": new_note.title,
        "content": new_note.content,
        "created_at": new_note.created_at.isoformat(),
        "user_id": new_note.user_id
    }, 201
@app.route("/notes", methods=["GET"])
@jwt_required()
def get_notes():
    # Identify the logged-in user
    user_id = int(get_jwt_identity())

    # Read pagination values from the URL
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # Validate pagination values
    if page < 1 or per_page < 1:
        return {
            "error": "Page and per_page must be positive numbers."
        }, 400

    # Limit the number of notes returned per request
    per_page = min(per_page, 100)

    # Retrieve only notes belonging to the logged-in user
    pagination = (
        Note.query
        .filter_by(user_id=user_id)
        .order_by(Note.id.desc())
        .paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    )

    # Convert the notes into dictionaries
    notes = []

    for note in pagination.items:
        notes.append({
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "created_at": note.created_at.isoformat(),
            "user_id": note.user_id
        })

    # Return notes and pagination information
    return {
        "notes": notes,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_notes": pagination.total,
            "total_pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    }, 200
@app.route("/notes/<int:note_id>", methods=["PATCH"])
@jwt_required()
def update_note(note_id):
    # Identify the logged-in user
    user_id = int(get_jwt_identity())

    # Find the note belonging to this user
    note = Note.query.filter_by(
        id=note_id,
        user_id=user_id
    ).first()

    # Reject the request if the note does not belong to this user
    if note is None:
        return {"error": "Note not found."}, 404

    # Get the information sent by the client
    data = request.get_json()

    if not isinstance(data, dict) or not data:
        return {"error": "Provide at least one field to update."}, 400

    # Update the title if it was provided
    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"].strip():
            return {"error": "Title cannot be empty."}, 400

        note.title = data["title"].strip()

    # Update the content if it was provided
    if "content" in data:
        if not isinstance(data["content"], str) or not data["content"].strip():
            return {"error": "Content cannot be empty."}, 400

        note.content = data["content"].strip()

    # Save the changes
    db.session.commit()

    # Return the updated note
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "created_at": note.created_at.isoformat(),
        "user_id": note.user_id
    }, 200
@app.route("/notes/<int:note_id>", methods=["DELETE"])
@jwt_required()
def delete_note(note_id):
    user_id = int(get_jwt_identity())

    note = Note.query.filter_by(
        id=note_id,
        user_id=user_id
    ).first()

    if note is None:
        return {"error": "Note not found."}, 404

    db.session.delete(note)
    db.session.commit()

    return {
        "message": "Note deleted successfully."
    }, 200

if __name__ == "__main__":
    app.run(port=5555, debug=True)