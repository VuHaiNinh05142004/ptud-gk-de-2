from flask import Flask
from models import db
from routes import task_bp
import os
import sqlite3
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "your_secret_key"

db.init_app(app)

# Đăng ký blueprint cho routes
app.register_blueprint(task_bp)


def recreate_database():
    try:
        # Delete the existing database file if it exists
        db_path = os.path.join(app.instance_path, "database.db")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print("Database file deleted successfully.")
            except PermissionError:
                print(
                    "Cannot delete database file - it's in use. Creating new schema instead."
                )
                # If we can't delete, we'll modify the existing database instead
                # Check if the database has the required structure
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    # Check if user table exists with password column
                    cursor.execute("PRAGMA table_info(user)")
                    columns = [info[1] for info in cursor.fetchall()]
                    if "password" not in columns:
                        print("Adding missing password column to user table")
                        cursor.execute(
                            "ALTER TABLE user ADD COLUMN password TEXT NOT NULL DEFAULT 'admin123'"
                        )
                    conn.commit()
                    conn.close()
                    return  # Skip remaining database creation steps
                except Exception as e:
                    print(f"Error modifying database: {e}")
                    # Continue with normal startup without recreating database
                    return

        # Create the database directory if it doesn't exist
        os.makedirs(app.instance_path, exist_ok=True)

        # Create all tables
        db.create_all()

        # Add a default user
        from models import User

        default_user = User(
            username="admin", password=generate_password_hash("admin123")
        )
        db.session.add(default_user)
        db.session.commit()
        print("New database created with default user 'admin'")

    except Exception as e:
        print(f"Error during database setup: {e}")
        # Continue without failing


if __name__ == "__main__":
    with app.app_context():
        recreate_database()

    app.run(debug=True)
