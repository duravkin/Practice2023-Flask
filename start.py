from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_admin import Admin as F_Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


app = Flask(__name__, static_folder="static")
app.secret_key = '([супер секретная фраза, которую никто не сможет отгадать])'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/practice2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
manager = LoginManager(app)


# ======== Модели БД ========


# Определяем модель Weekday
class Weekday(db.Model):
    __tablename__ = 'weekdays'
    id_weekday = db.Column(db.Integer, primary_key=True)
    weekday = db.Column(db.String(20), unique=True, nullable=False)


# Определяем модель Schedule
class Schedule(db.Model):
    __tablename__ = 'schedules'
    id_schedule = db.Column(db.Integer, primary_key=True)
    weekday_id = db.Column(db.Integer, db.ForeignKey('weekdays.id_weekday'), nullable=False)
    start_time_day = db.Column(db.Time, nullable=False)
    end_time_day = db.Column(db.Time, nullable=False)

    weekday = db.relationship('Weekday', backref=db.backref('schedules', lazy=True))


# Определяем модель Job
class Job(db.Model):
    __tablename__ = 'jobs'
    id_job = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.String(20), unique=True, nullable=False)


# Определяем модель StudentGroup
class StudentGroup(db.Model):
    __tablename__ = 'student_groups'
    id_group = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(100), nullable=False)


# Определяем модель ScheduleJob
class ScheduleJob(db.Model):
    __tablename__ = 'schedule_jobs'
    id_schedule_job = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id_schedule'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id_job'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('student_groups.id_group'))

    schedule = db.relationship('Schedule', backref=db.backref('schedule_jobs', lazy=True))
    job = db.relationship('Job', backref=db.backref('schedule_jobs', lazy=True))
    group = db.relationship('StudentGroup')


# Определяем модель Person
class Person(db.Model):
    __tablename__ = 'people'
    id_person = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(20), nullable=False)
    firstname = db.Column(db.String(20), nullable=False)
    patronymic = db.Column(db.String(20))
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id_job'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('student_groups.id_group'))

    job = db.relationship('Job')
    group = db.relationship('StudentGroup')


# Определяем модель Pass
class Pass(db.Model):
    __tablename__ = 'passes'
    id_pass = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('people.id_person'), nullable=False)
    start_date = db.Column(db.Date, nullable=False, server_default=db.func.current_date())
    end_date = db.Column(db.Date, nullable=False)

    person = db.relationship('Person', backref=db.backref('passes', lazy=True))


# Определяем модель Admin
class Admin(db.Model, UserMixin):
    __tablename__ = 'admins'
    id_admin = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def get_id(self):
        return (self.id_admin)


# Определяем модель Log
class Log(db.Model):
    __tablename__ = 'logs'
    id_log = db.Column(db.Integer, primary_key=True)
    inside_status = db.Column(db.Boolean, nullable=False)
    pass_id = db.Column(db.Integer, db.ForeignKey('passes.id_pass'), nullable=False)
    log_time = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    delay_time = db.Column(db.Time)

    pass_ = db.relationship('Pass', backref=db.backref('logs', lazy=True))


# ======== Админка ========


admin = F_Admin(app, name='pass control', template_mode='bootstrap3')


# Создаем класс представления для Schedule
class ScheduleView(ModelView):
    column_list = ('id_schedule', 'weekday.weekday', 'start_time_day', 'end_time_day')
    column_labels = {'id_schedule': 'Schedule ID', 'weekday.weekday': 'Weekday', 'start_time_day': 'Start Time', 'end_time_day': 'End Time'}


# Создаем класс представления для Person
class PersonView(ModelView):
    column_list = ('id_person', 'surname', 'firstname', 'patronymic', 'job.job', 'group.group_name')
    column_labels = {'id_person': 'Person ID', 'surname': 'Surname', 'firstname': 'First Name', 'patronymic': 'Patronymic', 'job.job': 'Job', 'group.group_name': 'Group'}


# Класс представления для Job
class JobView(ModelView):
    column_list = ('id_job', 'job')
    column_labels = {'id_job': 'Job ID', 'job': 'Job'}


# Класс представления для StudentGroup
class StudentGroupView(ModelView):
    column_list = ('id_group', 'group_name')
    column_labels = {'id_group': 'Group ID', 'group_name': 'Group Name'}


# Класс представления для ScheduleJob
class ScheduleJobView(ModelView):
    column_list = ('id_schedule_job', 'schedule.start_time_day', 'schedule.end_time_day', 'job.job', 'group.group_name')
    column_labels = {'id_schedule_job': 'Schedule Job ID', 'schedule.start_time_day': 'Start Time', 'schedule.end_time_day': 'End Time', 'job.job': 'Job', 'group.group_name': 'Group'}


# Класс представления для Pass
class PassView(ModelView):
    column_list = ('id_pass', 'person.surname', 'person.firstname', 'start_date', 'end_date')
    column_labels = {'id_pass': 'Pass ID', 'person.surname': 'Surname', 'person.firstname': 'First Name', 'start_date': 'Start Date', 'end_date': 'End Date'}


# Класс представления для Admin
class AdminView(ModelView):
    column_list = ('id_admin', 'login')
    column_labels = {'id_admin': 'Admin ID', 'login': 'Login'}


# Класс представления для Log
class LogView(ModelView):
    column_list = ('id_log', 'inside_status', 'pass.person.surname', 'pass.person.firstname', 'log_time', 'delay_time')
    column_labels = {'id_log': 'Log ID', 'inside_status': 'Inside Status', 'pass.person.surname': 'Surname', 'pass.person.firstname': 'First Name', 'log_time': 'Log Time', 'delay_time': 'Delay Time'}


admin.add_view(ModelView(Weekday, db.session))
admin.add_view(ScheduleView(Schedule, db.session))
admin.add_view(ModelView(Job, db.session))
admin.add_view(ModelView(StudentGroup, db.session))
admin.add_view(ModelView(ScheduleJob, db.session))
admin.add_view(PersonView(Person, db.session))
admin.add_view(ModelView(Pass, db.session))
admin.add_view(ModelView(Log, db.session))


# ======== Роуты ========


@app.route("/", methods=["GET", "POST"])
def start_page():
    query = text("SELECT (SELECT count(*) from passes) as pass_count, \
                 (SELECT count(*) from logs) as logs_count, \
                 (SELECT count(*) from logs where delay_time is not null) as delay_count, \
                 (SELECT count(*) from logs where log_time::date = CURRENT_DATE) as today_logs_count, \
                 (SELECT count(*) from logs where delay_time is not null and log_time::date = NOW()::date) as today_delay_count")
    result = db.session.execute(query).fetchone()

    if request.method == "POST":
        id_pass = request.form["id"]
        if id_pass.isdigit():
            pass_info = Pass.query.filter(Pass.id_pass == id_pass).first()
        else:
            pass_info = None
        return render_template("index.html", out=result, res=True, out2=pass_info, old_id=id_pass)
    return render_template("index.html", out=result, res=False)


@app.before_request
def before_request():
    g.user = current_user


@app.route("/auth")
def auth_page():
    return render_template("auth.html")


@app.route("/auth/login", methods=["POST"])
def user_login():
    if request.method == "POST":
        login = request.form["inputLogin"]
        password = request.form["inputPass"]

        if login.strip() and password.strip():
            now_admin = Admin.query.filter_by(login=login).first()
            if now_admin and check_password_hash(now_admin.password, password):
                login_user(now_admin)
                return redirect(url_for("work_page"))
            else:
                flash('Неправильный логин или пароль!')
        else:
            flash('Пожалуйста, заполните все поля!')
    return redirect(url_for('auth_page'))


@app.route("/auth/logout")
@login_required
def user_logout():
    logout_user()
    return redirect(url_for("start_page"))


@app.route('/my_admin')
@login_required
# @login_required
def admin_page():
    return render_template('my_admin.html')


@app.route('/my_admin/change_password', methods=['GET', 'POST'])
@login_required
def admin_change_password():
    if request.method == "POST":
        now_admin = Admin.query.get(g.user.get_id())
        old_pass = request.form['old_password'].strip()
        new_1 = request.form['password1'].strip()
        new_2 = request.form['password2'].strip()

        if old_pass == '':
            flash('Введите текущий пароль!')
        elif not check_password_hash(now_admin.password, old_pass):
            flash('Текущий пароль с ошибкой!')
        elif new_1 == '' or new_2 == '':
            flash('Введите новый пароль!')
        elif new_1 != new_2:
            flash('Поля с новым паролем не совпадают!')
        else:
            hash_pwd = generate_password_hash(new_1)
            now_admin.password = hash_pwd
            db.session.commit()
            flash('Пароль обновлён!')

    return redirect(url_for('admin_page'))


@app.route('/my_admin/add')
@login_required
def reg_page():
    return render_template('add_admin.html')


@app.route('/my_admin/add/register', methods=['GET', 'POST'])
@login_required
def register():
    if request.method == "POST":
        login = request.form['login']
        password = request.form['password']
        password2 = request.form['password2']

        if login.strip() == '':
            flash('Заполните поле "Логин"!')
        elif password.strip() == '' or password2.strip() == '':
            flash('Заполните поле "Пароль"!')
        elif password != password2:
            flash('Пароли не совпадают!')
        elif Admin.query.filter_by(login=login).first():
            flash('Логин уже существует!')
        else:
            hash_pwd = generate_password_hash(password)
            new_user = Admin()
            new_user.login = login
            new_user.password = hash_pwd
            db.session.add(new_user)
            db.session.commit()
            flash(f'Пользователь "{login}" успешно добавлен в систему!')

    return redirect(url_for('reg_page'))


@app.route("/work")
@login_required
def work_page():
    result = Log.query.order_by(Log.id_log.desc()).limit(3).all()

    return render_template("work.html", logs=result)


@app.route("/journal")
@login_required
def journal_page():
    query = text("SELECT * FROM journal_view where log_date = NOW()::date")
    result = db.session.execute(query)
    table_html = render_template('journal_table.html', jurnal=result)
    return render_template('journal.html', content=table_html)


@app.route("/journal_table", methods=["GET"])
async def journal_table_generate():
    if request.method == "GET":
        rb_day = request.args.get('rb_day')
        query = text(f"SELECT * FROM journal_view where log_date = NOW()::date - '{rb_day} day'::interval")
        result = db.session.execute(query)

        table_html = render_template('journal_table.html', jurnal=result)
        return jsonify({'html': table_html})


@app.route("/new_log", methods=["POST"])
@login_required
def new_log():
    if request.method == "POST":
        status = request.form["btn"]
        id_pass = request.form["id"]
        if not id_pass.isdigit():
            flash("Введите номер удостоверения!")
        elif db.session.query(Pass.id_pass).filter(Pass.id_pass == id_pass).scalar() is not None:
            log = Log(
                inside_status=bool(int(status)),
                pass_id=id_pass
            )
            db.session.add(log)
            db.session.commit()
        else:
            flash(f"Удостоверение №{id_pass} не существует!")
        return redirect(url_for("work_page"))


@app.route("/delete_log/<int:id>")
@login_required
def delete_log(id):
    print(id)
    return redirect(url_for("journal_page"))


@app.route("/stats", methods=["GET", "POST"])
@login_required
def stats_page():
    if request.method == "POST":
        id_pass = request.form["id"]
        if id_pass.isdigit():
            result = db.session.query(Person). \
                join(Pass, Person.id_person == Pass.person_id). \
                join(Job, Job.id_job == Person.job_id). \
                outerjoin(StudentGroup, Person.group_id == StudentGroup.id_group). \
                filter(Pass.id_pass == id_pass).first()
            if result:
                logs = Log.query.filter_by(pass_id=id_pass).all()
                return render_template("stats.html", res=result, old=id_pass, logs=logs)
            else:
                flash("Не найдено!")
        else:
            flash("Некорректный ввод!")
    return render_template("stats.html")


@manager.user_loader
def load_user(admin_id):
    return Admin.query.get(admin_id)


@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(url_for('auth_page'))

    return response


if __name__ == "__main__":
    app.debug = True
    # app.run(host='0.0.0.0')
    app.run()
