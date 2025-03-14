from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
)
from sqlalchemy import false
from models import db, Task, User
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from utils import count_overdue_tasks, allowed_file
from io import BytesIO
from PIL import Image

task_bp = Blueprint("task_bp", __name__)


@task_bp.route("/")
def index():
    user = User.query.get(session.get("user_id"))

    if not user:
        return redirect(url_for("task_bp.login"))

    users = User.query.all()
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template(
        "index.html",
        tasks=tasks,
        users=users,
        user=user,
        overdue=overdue_tasks(user.id),
    )


@task_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate input
        if not username or not password:
            flash("Vui lòng nhập đầy đủ thông tin!", "danger")
            return render_template("login.html")

        # Find user
        user = User.query.filter_by(username=username).first()

        # Check user exists and password is correct
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for("task_bp.index"))
        else:
            flash("Tên đăng nhập hoặc mật khẩu không đúng!", "danger")

    return render_template("login.html")


@task_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Validate input
        if not username or not password or not confirm_password:
            flash("Vui lòng nhập đầy đủ thông tin!", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Mật khẩu nhập lại không khớp!", "danger")
            return render_template("register.html")

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Tên đăng nhập đã tồn tại!", "danger")
            return render_template("register.html")

        # Create new user
        new_user = User(username=username, password=generate_password_hash(password))

        db.session.add(new_user)
        db.session.commit()

        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
        return redirect(url_for("task_bp.login"))

    return render_template("register.html")


@task_bp.route("/upload_avatar", methods=["POST"])
def upload_avatar():
    if "user_id" not in session:
        flash("Bạn cần đăng nhập trước!", "danger")
        return redirect(url_for("task_bp.login"))

    if "avatar" not in request.files:
        flash("Không có file nào được chọn", "danger")
        return redirect(url_for("task_bp.index"))

    file = request.files["avatar"]

    if file.filename == "":
        flash("Không có file nào được chọn", "danger")
        return redirect(url_for("task_bp.index"))

    if file and allowed_file(file.filename):
        try:
            # Determine format from filename extension
            filename = file.filename.lower()
            if filename.endswith(".png"):
                file_format = "PNG"
            elif filename.endswith(".gif"):
                file_format = "GIF"
            else:
                file_format = "JPEG"

            img = Image.open(file)
            img = img.resize((200, 200))

            # Convert to RGB if the image is in RGBA mode (for PNG with transparency)
            if img.mode == "RGBA" and file_format != "PNG":
                img = img.convert("RGB")

            buf = BytesIO()
            img.save(buf, format=file_format)
            image_binary = buf.getvalue()

            # Get the appropriate MIME type
            mime_mapping = {
                "JPEG": "image/jpeg",
                "PNG": "image/png",
                "GIF": "image/gif",
            }

            mime_type = mime_mapping.get(file_format, "image/jpeg")

            # Debug output
            print(
                f"Uploading image: format={file_format}, mime={mime_type}, size={len(image_binary)} bytes"
            )

            # Update the user's avatar
            user = User.query.get(session["user_id"])
            user.avatar = image_binary
            user.avatar_mimetype = mime_type

            db.session.commit()
            flash(f"Avatar đã được cập nhật! (Format: {file_format})", "success")

        except Exception as e:
            import traceback

            traceback.print_exc()
            flash(f"Lỗi khi tải lên avatar: {str(e)}", "danger")
    else:
        flash("Định dạng file không được hỗ trợ", "danger")

    return redirect(url_for("task_bp.index"))


@task_bp.route("/avatar/<int:user_id>")
def get_avatar(user_id):
    user = User.query.get(user_id)

    if user and user.avatar:
        return send_file(BytesIO(user.avatar), mimetype=user.avatar_mimetype)
    else:
        # Return a default avatar
        return send_file("static/img/default.png", mimetype="image/png")


@task_bp.route("/logout")
def logout():
    session.clear()
    flash("Đã đăng xuất!", "info")
    return redirect(url_for("task_bp.login"))


@task_bp.route("/task/add", methods=["POST"])
def add_task():
    title = request.form.get("title")
    deadline_str = request.form.get("deadline")

    # Use a default user_id (the admin user with id=1) if none is provided
    user_id = request.form.get("user_id")
    if not user_id:
        user_id = 1  # Default to admin user

    # Kiểm tra nếu deadline rỗng
    if not deadline_str:
        return "Lỗi: Hạn chót không được để trống!", 400

    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%dT%H:%M")
    except ValueError:
        return "Lỗi: Định dạng ngày không hợp lệ!", 400

    new_task = Task(
        title=title,
        deadline=deadline,
        status="pending",
        user_id=user_id,
        created_at=datetime.utcnow(),
    )
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for("task_bp.index"))


@task_bp.route("/task/delete/<int:task_id>")
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for("task_bp.index"))


@task_bp.route("/task/complete/<int:task_id>")
def complete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        task.status = "completed"
        task.finished_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for("task_bp.index"))


@task_bp.route("/overdue_tasks/<int:user_id>")
def overdue_tasks(user_id):
    overdue_count = count_overdue_tasks(user_id)
    return {"overdue_count": overdue_count}
