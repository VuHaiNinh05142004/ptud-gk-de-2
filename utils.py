from models import Task
from datetime import datetime

def count_overdue_tasks(user_id):
    return Task.query.filter(
        Task.user_id == user_id,
        Task.status == 'pending',
        Task.deadline < datetime.utcnow()
    ).count()

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
