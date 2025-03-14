from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Không còn lỗi
    finished_at = db.Column(db.DateTime, nullable=True)
    deadline = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # Ensure this line exists
    avatar = db.Column(db.LargeBinary, nullable=True)
    avatar_mimetype = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default="user")
    tasks = db.relationship("Task", backref="user", lazy=True)
