from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy.exc import IntegrityError

from extensions import bcrypt
from models import db, User, Note

# A Blueprint is a group of routes that app.py registers on the Flask app.
api = Blueprint("api", __name__)

MIN_PASSWORD_LENGTH = 8


def is_text(value):
    """True only if value is a string."""
    return isinstance(value, str)


def get_json_body():
    """Return the JSON body as a dict, or an empty dict if it is
    missing, invalid, or not a JSON object (for example a list)."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def note_to_dict(note):
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "created_at": note.created_at.isoformat(),
        "user_id": note.user_id,
    }


@api.route("/")
def home():
    return {"message": "Productivity API is running!"}


@api.route("/signup", methods=["POST"])
def signup():
    data = get_json_body()

    username = data.get("username", "")
    password = data.get("password", "")
    password_confirmation = data.get("password_confirmation", "")

    # All three fields must be text
    if not (
        is_text(username) and is_text(password) and is_text(password_confirmation)
    ):
        return {"errors": ["Username and passwords must be text."]}, 400

    username = username.strip()

    # Check that all required fields are provided
    if not username or not password or not password_confirmation:
        return {
            "errors": [
                "Username, password, and password confirmation are required."
            ]
        }, 400

    # Check password length
    if len(password) < MIN_PASSWORD_LENGTH:
        return {
            "errors": [
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            ]
        }, 400

    # Check that the passwords match
    if password != password_confirmation:
        return {"errors": ["Passwords do not match."]}, 400

    # Check whether the username already exists
    if User.query.filter_by(username=username).first():
        return {"errors": ["Username already exists."]}, 409

    # Hash the password before saving it
    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    new_user = User(username=username, password_hash=password_hash)

    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"errors": ["Username already exists."]}, 409

    # Generate a JWT token for the new user
    token = create_access_token(identity=str(new_user.id))

    return {
        "token": token,
        "user": {"id": new_user.id, "username": new_user.username},
    }, 201


@api.route("/login", methods=["POST"])
def login():
    data = get_json_body()

    username = data.get("username", "")
    password = data.get("password", "")

    if not (is_text(username) and is_text(password)):
        return {"errors": ["Username and password must be text."]}, 400

    username = username.strip()

    if not username or not password:
        return {"errors": ["Username and password are required."]}, 400

    user = User.query.filter_by(username=username).first()

    if user is None or not bcrypt.check_password_hash(user.password_hash, password):
        return {"errors": ["Invalid username or password."]}, 401

    token = create_access_token(identity=str(user.id))

    return {
        "token": token,
        "user": {"id": user.id, "username": user.username},
    }, 200


@api.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())

    user = db.session.get(User, user_id)

    if user is None:
        return {"error": "User not found."}, 404

    return {"id": user.id, "username": user.username}, 200


@api.route("/notes", methods=["POST"])
@jwt_required()
def create_note():
    user_id = int(get_jwt_identity())

    data = get_json_body()

    title = data.get("title", "")
    content = data.get("content", "")

    if not (is_text(title) and is_text(content)):
        return {"error": "Title and content must be text."}, 400

    title = title.strip()
    content = content.strip()

    if not title or not content:
        return {"error": "Title and content are required."}, 400

    new_note = Note(title=title, content=content, user_id=user_id)

    db.session.add(new_note)
    db.session.commit()

    return note_to_dict(new_note), 201


@api.route("/notes", methods=["GET"])
@jwt_required()
def get_notes():
    # Identify the logged-in user
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    if page < 1 or per_page < 1:
        return {"error": "Page and per_page must be positive numbers."}, 400

    per_page = min(per_page, 100)

    pagination = (
        Note.query
        .filter_by(user_id=user_id)
        .order_by(Note.id.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return {
        "notes": [note_to_dict(note) for note in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_notes": pagination.total,
            "total_pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev,
        },
    }, 200


@api.route("/notes/<int:note_id>", methods=["PATCH"])
@jwt_required()
def update_note(note_id):
    user_id = int(get_jwt_identity())

    # Only look in the logged-in user's own notes
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()

    if note is None:
        return {"error": "Note not found."}, 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return {"error": "Provide at least one field to update."}, 400

    if "title" in data:
        if not is_text(data["title"]) or not data["title"].strip():
            return {"error": "Title cannot be empty."}, 400
        note.title = data["title"].strip()

    if "content" in data:
        if not is_text(data["content"]) or not data["content"].strip():
            return {"error": "Content cannot be empty."}, 400
        note.content = data["content"].strip()

    db.session.commit()

    return note_to_dict(note), 200


@api.route("/notes/<int:note_id>", methods=["DELETE"])
@jwt_required()
def delete_note(note_id):
    user_id = int(get_jwt_identity())

    note = Note.query.filter_by(id=note_id, user_id=user_id).first()

    if note is None:
        return {"error": "Note not found."}, 404

    db.session.delete(note)
    db.session.commit()

    return {"message": "Note deleted successfully."}, 200