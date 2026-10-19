from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,timezone

db = SQLAlchemy()
def utc_now():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    notes = db.relationship(
        "Note",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __rep__(self):
        return f"<user{self.id}{self.username}>"


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime,nullable=False, default=utc_now)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    user = db.relationship("User", back_populates="notes")


    def __rep__(self):
        return f"<Note{self.id}{self.title}>"