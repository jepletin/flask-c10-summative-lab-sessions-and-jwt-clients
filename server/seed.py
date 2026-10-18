from app import app, bcrypt
from models import db, User, Note


def seed_database():
    with app.app_context():
        db.create_all()

        lydia = User.query.filter_by(username="lydia").first()

        if lydia is None:
            lydia = User(
                username="lydia",
                password_hash=bcrypt.generate_password_hash(
                    "Password123!"
                ).decode("utf-8")
            )
            db.session.add(lydia)
            db.session.flush()

        # Find Brian or create his account
        brian = User.query.filter_by(username="brian").first()

        if brian is None:
            brian = User(
                username="brian",
                password_hash=bcrypt.generate_password_hash(
                    "Password123!"
                ).decode("utf-8")
            )
            db.session.add(brian)
            db.session.flush()

        # Give Lydia two sample notes if she has none
        if not lydia.notes:
            db.session.add_all([
                Note(
                    title="Learn Flask",
                    content="Practice Flask authentication and routes.",
                    user_id=lydia.id
                ),
                Note(
                    title="Practice SQL",
                    content="Learn queries, joins, and subqueries.",
                    user_id=lydia.id
                )
            ])

        # Give Brian two sample notes if he has none
        if not brian.notes:
            db.session.add_all([
                Note(
                    title="Complete project",
                    content="Finish the Productivity API.",
                    user_id=brian.id
                ),
                Note(
                    title="Review Python",
                    content="Practice Python classes and functions.",
                    user_id=brian.id
                )
            ])

        # Save everything
        db.session.commit()

        print("Database seeding completed successfully!")
        print("Sample users: lydia and brian")
        print("Sample password: Password123!")


if __name__ == "__main__":
    seed_database()