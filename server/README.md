# Productivity API (Flask + JWT)

A REST API where users sign up, log in, and manage their own private notes.
Authentication uses JWT (Flask-JWT-Extended), passwords are hashed with bcrypt,
and data is stored in SQLite.

## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # then set JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"   # use this as the secret

export FLASK_APP=app.py
flask db init                     # first time only
flask db migrate -m "initial"
flask db upgrade

python app.py                     # runs on http://localhost:5555
```

## Authentication

Protected routes need this header:

```
Authorization: Bearer <token>
```

Tokens come from `/signup` and `/login` and expire after 1 hour.
A missing, invalid, or expired token returns `401`.

## Routes

| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/signup` | No | Create a user and return a token |
| POST | `/login` | No | Return a token for valid credentials |
| GET | `/me` | Yes | Return the logged-in user |
| POST | `/notes` | Yes | Create a note |
| GET | `/notes?page=1&per_page=10` | Yes | List your notes (newest first, paginated) |
| PATCH | `/notes/<id>` | Yes | Update the title and/or content of your note |
| DELETE | `/notes/<id>` | Yes | Delete your note |

A note that belongs to another user returns `404`, the same as a note that
does not exist.

### POST /signup

Body:
```json
{ "username": "lydia", "password": "password123", "password_confirmation": "password123" }
```
Returns `201`:
```json
{ "token": "<JWT>", "user": { "id": 1, "username": "lydia" } }
```
Errors return `{ "errors": ["..."] }` with `400` (invalid input) or `409` (username taken).
Passwords must be at least 8 characters.

### POST /login

Body: `{ "username": "lydia", "password": "password123" }`

Returns `200` with the same shape as signup. Bad credentials return `401`
with `{ "errors": ["Invalid username or password."] }`.

### GET /me

Returns `200`: `{ "id": 1, "username": "lydia" }`

### POST /notes

Body: `{ "title": "Buy milk", "content": "2 litres" }`

Returns `201`:
```json
{ "id": 1, "title": "Buy milk", "content": "2 litres",
  "created_at": "2026-10-19T07:40:00.000000", "user_id": 1 }
```

### GET /notes

Query params: `page` (default 1), `per_page` (default 10, max 100).

Returns `200`:
```json
{
  "notes": [ { "id": 1, "title": "...", "content": "...", "created_at": "...", "user_id": 1 } ],
  "pagination": {
    "page": 1, "per_page": 10, "total_notes": 1,
    "total_pages": 1, "has_next": false, "has_previous": false
  }
}
```

### PATCH /notes/<id>

Body: any of `title` and `content`. Returns `200` with the updated note.
Empty or non-string values return `400`.

### DELETE /notes/<id>

Returns `200`: `{ "message": "Note deleted successfully." }`

## Error format

- `/signup` and `/login` errors: `{ "errors": ["message"] }`
- All other route errors: `{ "error": "message" }`
- JWT failures (from Flask-JWT-Extended): `{ "msg": "message" }` with `401` or `422`