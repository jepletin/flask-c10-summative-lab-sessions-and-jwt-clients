import os
from datetime import timedelta

# The app needs a secret key when it is imported, so set a test one first.
# (setdefault never overrides a key you already have in your environment.)
TEST_SECRET = "test-secret-key-used-only-by-the-test-suite-123456"
os.environ.setdefault("JWT_SECRET_KEY", TEST_SECRET)

import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from extensions import bcrypt
from models import db, User, Note

PASSWORD = "Password123!"

TEST_CONFIG = {
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "JWT_SECRET_KEY": TEST_SECRET,
}


# ---------------------------------------------------------------------------
# Fixtures: setup code that pytest runs for the tests that ask for it
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    """A fresh app with an empty in-memory database for every test."""
    app = create_app(TEST_CONFIG)

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def signup(client, username="lydia", password=PASSWORD, confirmation=None):
    """Call POST /signup. The confirmation defaults to the password."""
    return client.post("/signup", json={
        "username": username,
        "password": password,
        "password_confirmation": password if confirmation is None else confirmation,
    })


def register(client, username="lydia"):
    """Create a user and return (token, user_id)."""
    data = signup(client, username).get_json()
    return data["token"], data["user"]["id"]


def auth(token):
    """Authorization header for a JWT token."""
    return {"Authorization": f"Bearer {token}"}


def create_note(client, token, title="Learn Flask", content="Practice routes."):
    return client.post(
        "/notes",
        json={"title": title, "content": content},
        headers=auth(token),
    )


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

class TestHome:
    def test_home_route(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.get_json() == {"message": "Productivity API is running!"}


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self, client):
        response = signup(client)
        data = response.get_json()

        assert response.status_code == 201
        assert data["user"]["username"] == "lydia"
        assert "id" in data["user"]
        assert data["token"]

    def test_signup_response_has_no_password(self, client):
        data = signup(client).get_json()

        assert "password" not in data["user"]
        assert "password_hash" not in data["user"]

    def test_password_is_stored_hashed(self, app, client):
        signup(client)

        with app.app_context():
            user = User.query.filter_by(username="lydia").first()
            assert user.password_hash != PASSWORD
            assert bcrypt.check_password_hash(user.password_hash, PASSWORD)

    def test_signup_trims_username(self, client):
        data = signup(client, username="  anna  ").get_json()
        assert data["user"]["username"] == "anna"

    def test_signup_token_works_immediately(self, client):
        token = signup(client).get_json()["token"]
        response = client.get("/me", headers=auth(token))
        assert response.status_code == 200

    def test_signup_duplicate_username(self, client):
        signup(client)
        response = signup(client)

        assert response.status_code == 409
        assert response.get_json()["errors"] == ["Username already exists."]

    def test_signup_missing_fields(self, client):
        response = client.post("/signup", json={"username": "lydia"})
        assert response.status_code == 400
        assert "errors" in response.get_json()

    def test_signup_blank_username(self, client):
        response = signup(client, username="   ")
        assert response.status_code == 400

    def test_signup_short_password(self, client):
        response = signup(client, password="short")
        assert response.status_code == 400
        assert "at least 8" in response.get_json()["errors"][0]

    def test_signup_passwords_do_not_match(self, client):
        response = signup(client, confirmation="Different123!")
        assert response.status_code == 400
        assert response.get_json()["errors"] == ["Passwords do not match."]

    def test_signup_non_text_values(self, client):
        response = client.post("/signup", json={
            "username": 123,
            "password": PASSWORD,
            "password_confirmation": PASSWORD,
        })
        assert response.status_code == 400

    def test_signup_no_body(self, client):
        response = client.post("/signup")
        assert response.status_code == 400

    def test_signup_json_list_body(self, client):
        response = client.post("/signup", json=[1, 2, 3])
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success(self, client):
        signup(client)
        response = client.post("/login", json={
            "username": "lydia",
            "password": PASSWORD,
        })
        data = response.get_json()

        assert response.status_code == 200
        assert data["token"]
        assert data["user"]["username"] == "lydia"

    def test_login_wrong_password(self, client):
        signup(client)
        response = client.post("/login", json={
            "username": "lydia",
            "password": "WrongPassword1!",
        })
        assert response.status_code == 401
        assert response.get_json()["errors"] == ["Invalid username or password."]

    def test_login_unknown_user(self, client):
        response = client.post("/login", json={
            "username": "nobody",
            "password": PASSWORD,
        })
        assert response.status_code == 401

    def test_login_errors_do_not_reveal_which_part_was_wrong(self, client):
        signup(client)
        wrong_password = client.post("/login", json={
            "username": "lydia", "password": "WrongPassword1!",
        })
        unknown_user = client.post("/login", json={
            "username": "nobody", "password": PASSWORD,
        })
        assert wrong_password.get_json() == unknown_user.get_json()

    def test_login_missing_fields(self, client):
        response = client.post("/login", json={"username": "lydia"})
        assert response.status_code == 400

    def test_login_non_text_values(self, client):
        response = client.post("/login", json={
            "username": ["lydia"],
            "password": PASSWORD,
        })
        assert response.status_code == 400

    def test_login_no_body(self, client):
        response = client.post("/login")
        assert response.status_code == 400

    def test_login_token_works(self, client):
        signup(client)
        token = client.post("/login", json={
            "username": "lydia", "password": PASSWORD,
        }).get_json()["token"]

        response = client.get("/me", headers=auth(token))
        assert response.status_code == 200
        assert response.get_json()["username"] == "lydia"


# ---------------------------------------------------------------------------
# /me and JWT protection
# ---------------------------------------------------------------------------

class TestMe:
    def test_me_returns_current_user(self, client):
        token, user_id = register(client)
        response = client.get("/me", headers=auth(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data == {"id": user_id, "username": "lydia"}

    def test_me_without_token(self, client):
        response = client.get("/me")
        assert response.status_code == 401

    def test_me_with_invalid_token(self, client):
        response = client.get("/me", headers=auth("not-a-real-token"))
        assert response.status_code == 422

    def test_me_for_deleted_user(self, app, client):
        token, user_id = register(client)

        with app.app_context():
            db.session.delete(db.session.get(User, user_id))
            db.session.commit()

        response = client.get("/me", headers=auth(token))
        assert response.status_code == 404

    def test_expired_token_is_rejected(self):
        app = create_app({
            **TEST_CONFIG,
            "JWT_ACCESS_TOKEN_EXPIRES": timedelta(seconds=-1),
        })

        with app.app_context():
            db.create_all()

        try:
            client = app.test_client()
            token = signup(client).get_json()["token"]
            response = client.get("/me", headers=auth(token))
            assert response.status_code == 401
        finally:
            with app.app_context():
                db.session.remove()
                db.drop_all()


# ---------------------------------------------------------------------------
# Create note
# ---------------------------------------------------------------------------

class TestCreateNote:
    def test_create_note(self, client):
        token, user_id = register(client)
        response = create_note(client, token, "Study", "Read chapter 4")
        data = response.get_json()

        assert response.status_code == 201
        assert data["title"] == "Study"
        assert data["content"] == "Read chapter 4"
        assert data["user_id"] == user_id
        assert "id" in data
        assert "created_at" in data

    def test_create_note_trims_whitespace(self, client):
        token, _ = register(client)
        data = create_note(client, token, "  Study  ", "  Read  ").get_json()

        assert data["title"] == "Study"
        assert data["content"] == "Read"

    def test_create_note_requires_token(self, client):
        response = client.post("/notes", json={"title": "A", "content": "B"})
        assert response.status_code == 401

    def test_create_note_missing_fields(self, client):
        token, _ = register(client)
        response = client.post(
            "/notes", json={"title": "Only a title"}, headers=auth(token)
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "Title and content are required."

    def test_create_note_blank_title(self, client):
        token, _ = register(client)
        response = create_note(client, token, title="   ", content="Something")
        assert response.status_code == 400

    def test_create_note_non_text_values(self, client):
        token, _ = register(client)
        response = client.post(
            "/notes",
            json={"title": 123, "content": "Something"},
            headers=auth(token),
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "Title and content must be text."

    def test_create_note_json_list_body(self, client):
        token, _ = register(client)
        response = client.post("/notes", json=[1, 2], headers=auth(token))
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Get notes: ownership, order and pagination
# ---------------------------------------------------------------------------

class TestGetNotes:
    def test_get_notes_empty(self, client):
        token, _ = register(client)
        response = client.get("/notes", headers=auth(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data["notes"] == []
        assert data["pagination"]["total_notes"] == 0

    def test_get_notes_requires_token(self, client):
        response = client.get("/notes")
        assert response.status_code == 401

    def test_notes_are_newest_first(self, client):
        token, _ = register(client)
        for title in ["First", "Second", "Third"]:
            create_note(client, token, title)

        notes = client.get("/notes", headers=auth(token)).get_json()["notes"]
        assert [note["title"] for note in notes] == ["Third", "Second", "First"]

    def test_user_only_sees_their_own_notes(self, client):
        lydia_token, _ = register(client, "lydia")
        brian_token, _ = register(client, "brian")
        create_note(client, lydia_token, "Lydia's note")
        create_note(client, brian_token, "Brian's note")

        lydia_notes = client.get(
            "/notes", headers=auth(lydia_token)
        ).get_json()["notes"]
        brian_notes = client.get(
            "/notes", headers=auth(brian_token)
        ).get_json()["notes"]

        assert [n["title"] for n in lydia_notes] == ["Lydia's note"]
        assert [n["title"] for n in brian_notes] == ["Brian's note"]

    def test_pagination_first_page(self, client):
        token, _ = register(client)
        for i in range(12):
            create_note(client, token, f"Note {i}")

        data = client.get(
            "/notes?page=1&per_page=5", headers=auth(token)
        ).get_json()

        assert len(data["notes"]) == 5
        assert data["pagination"] == {
            "page": 1,
            "per_page": 5,
            "total_notes": 12,
            "total_pages": 3,
            "has_next": True,
            "has_previous": False,
        }

    def test_pagination_last_page(self, client):
        token, _ = register(client)
        for i in range(12):
            create_note(client, token, f"Note {i}")

        data = client.get(
            "/notes?page=3&per_page=5", headers=auth(token)
        ).get_json()

        assert len(data["notes"]) == 2
        assert data["pagination"]["has_next"] is False
        assert data["pagination"]["has_previous"] is True

    def test_pagination_page_beyond_the_end_is_empty(self, client):
        token, _ = register(client)
        create_note(client, token)

        response = client.get("/notes?page=99", headers=auth(token))
        assert response.status_code == 200
        assert response.get_json()["notes"] == []

    def test_per_page_is_capped_at_100(self, client):
        token, _ = register(client)
        data = client.get("/notes?per_page=1000", headers=auth(token)).get_json()
        assert data["pagination"]["per_page"] == 100

    def test_default_per_page_is_10(self, client):
        token, _ = register(client)
        data = client.get("/notes", headers=auth(token)).get_json()
        assert data["pagination"]["per_page"] == 10
        assert data["pagination"]["page"] == 1

    @pytest.mark.parametrize("query", [
        "page=0",
        "page=-1",
        "per_page=0",
        "per_page=-5",
    ])
    def test_invalid_pagination_values(self, client, query):
        token, _ = register(client)
        response = client.get(f"/notes?{query}", headers=auth(token))
        assert response.status_code == 400

    def test_non_numeric_page_falls_back_to_page_one(self, client):
        token, _ = register(client)
        response = client.get("/notes?page=abc", headers=auth(token))
        assert response.status_code == 200
        assert response.get_json()["pagination"]["page"] == 1


# ---------------------------------------------------------------------------
# Update note
# ---------------------------------------------------------------------------

class TestUpdateNote:
    def test_update_title_only(self, client):
        token, _ = register(client)
        note = create_note(client, token, "Old", "Keep this").get_json()

        response = client.patch(
            f"/notes/{note['id']}", json={"title": "New"}, headers=auth(token)
        )
        data = response.get_json()

        assert response.status_code == 200
        assert data["title"] == "New"
        assert data["content"] == "Keep this"

    def test_update_content_only(self, client):
        token, _ = register(client)
        note = create_note(client, token, "Keep", "Old").get_json()

        response = client.patch(
            f"/notes/{note['id']}", json={"content": "New"}, headers=auth(token)
        )
        data = response.get_json()

        assert response.status_code == 200
        assert data["title"] == "Keep"
        assert data["content"] == "New"

    def test_update_is_saved(self, client):
        token, _ = register(client)
        note = create_note(client, token, "Old").get_json()
        client.patch(
            f"/notes/{note['id']}", json={"title": "New"}, headers=auth(token)
        )

        notes = client.get("/notes", headers=auth(token)).get_json()["notes"]
        assert notes[0]["title"] == "New"

    def test_update_requires_token(self, client):
        response = client.patch("/notes/1", json={"title": "New"})
        assert response.status_code == 401

    def test_update_note_not_found(self, client):
        token, _ = register(client)
        response = client.patch(
            "/notes/999", json={"title": "New"}, headers=auth(token)
        )
        assert response.status_code == 404
        assert response.get_json()["error"] == "Note not found."

    def test_update_empty_body(self, client):
        token, _ = register(client)
        note = create_note(client, token).get_json()

        response = client.patch(
            f"/notes/{note['id']}", json={}, headers=auth(token)
        )
        assert response.status_code == 400

    def test_update_json_list_body(self, client):
        token, _ = register(client)
        note = create_note(client, token).get_json()

        response = client.patch(
            f"/notes/{note['id']}", json=[1], headers=auth(token)
        )
        assert response.status_code == 400

    def test_update_blank_title(self, client):
        token, _ = register(client)
        note = create_note(client, token).get_json()

        response = client.patch(
            f"/notes/{note['id']}", json={"title": "   "}, headers=auth(token)
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "Title cannot be empty."

    def test_update_blank_content(self, client):
        token, _ = register(client)
        note = create_note(client, token).get_json()

        response = client.patch(
            f"/notes/{note['id']}", json={"content": ""}, headers=auth(token)
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "Content cannot be empty."

    def test_update_non_text_title(self, client):
        token, _ = register(client)
        note = create_note(client, token).get_json()

        response = client.patch(
            f"/notes/{note['id']}", json={"title": 123}, headers=auth(token)
        )
        assert response.status_code == 400

    def test_cannot_update_another_users_note(self, client):
        lydia_token, _ = register(client, "lydia")
        brian_token, _ = register(client, "brian")
        note = create_note(client, lydia_token, "Private").get_json()

        response = client.patch(
            f"/notes/{note['id']}",
            json={"title": "Hacked"},
            headers=auth(brian_token),
        )
        assert response.status_code == 404

        # Lydia's note must be unchanged
        notes = client.get("/notes", headers=auth(lydia_token)).get_json()["notes"]
        assert notes[0]["title"] == "Private"


# ---------------------------------------------------------------------------
# Delete note
# ---------------------------------------------------------------------------

class TestDeleteNote:
    def test_delete_note(self, client):
        token, _ = register(client)
        note = create_note(client, token).get_json()

        response = client.delete(f"/notes/{note['id']}", headers=auth(token))
        assert response.status_code == 200
        assert response.get_json()["message"] == "Note deleted successfully."

        notes = client.get("/notes", headers=auth(token)).get_json()["notes"]
        assert notes == []

    def test_delete_twice_returns_404(self, client):
        token, _ = register(client)
        note = create_note(client, token).get_json()

        client.delete(f"/notes/{note['id']}", headers=auth(token))
        response = client.delete(f"/notes/{note['id']}", headers=auth(token))
        assert response.status_code == 404

    def test_delete_requires_token(self, client):
        response = client.delete("/notes/1")
        assert response.status_code == 401

    def test_delete_note_not_found(self, client):
        token, _ = register(client)
        response = client.delete("/notes/999", headers=auth(token))
        assert response.status_code == 404

    def test_cannot_delete_another_users_note(self, client):
        lydia_token, _ = register(client, "lydia")
        brian_token, _ = register(client, "brian")
        note = create_note(client, lydia_token, "Private").get_json()

        response = client.delete(
            f"/notes/{note['id']}", headers=auth(brian_token)
        )
        assert response.status_code == 404

        # Lydia's note must still exist
        notes = client.get("/notes", headers=auth(lydia_token)).get_json()["notes"]
        assert len(notes) == 1


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestModels:
    def test_deleting_user_deletes_their_notes(self, app, client):
        token, user_id = register(client)
        create_note(client, token, "One")
        create_note(client, token, "Two")

        with app.app_context():
            db.session.delete(db.session.get(User, user_id))
            db.session.commit()

            assert Note.query.count() == 0

    def test_note_gets_created_at_automatically(self, app, client):
        token, _ = register(client)
        create_note(client, token)

        with app.app_context():
            note = Note.query.first()
            assert note.created_at is not None

    def test_token_for_missing_user_is_rejected_by_me(self, app, client):
        with app.app_context():
            token = create_access_token(identity="999")

        response = client.get("/me", headers=auth(token))
        assert response.status_code == 404