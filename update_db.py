from app import app, db
from sqlalchemy import inspect


with app.app_context():

    inspector = inspect(db.engine)

    # Check existing columns
    columns = [
        column["name"]
        for column in inspector.get_columns("chat_message")
    ]

    if "order_id" not in columns:

        db.session.execute(
            db.text(
                "ALTER TABLE chat_message "
                "ADD COLUMN order_id INTEGER"
            )
        )

        db.session.commit()

        print("order_id added successfully!")

    else:

        print("order_id already exists!")