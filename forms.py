from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateTimeField, SubmitField
from wtforms.validators import DataRequired

class TaskForm(FlaskForm):
    title = StringField('Tên công việc', validators=[DataRequired()])
    deadline = DateTimeField('Hạn chót', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    status = SelectField('Tình trạng', choices=[('pending', 'Chưa hoàn thành'), ('completed', 'Đã hoàn thành')])
    submit = SubmitField('Thêm công việc')
