from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__, static_folder="static")
app.secret_key = 'some secret salt'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/practice2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
manager = LoginManager(app)


class Weekday(db.Model):
    __tablename__ = 'weekdays'
    id_weekday = db.Column(db.Integer, primary_key=True)
    weekday = db.Column(db.String(20), unique=True, nullable=False)


class Schedule(db.Model):
    __tablename__ = 'schedules'
    id_schedule = db.Column(db.Integer, primary_key=True)
    weekday_id = db.Column(db.Integer, db.ForeignKey('weekdays.id_weekday'), nullable=False)
    start_time_day = db.Column(db.Time, nullable=False)
    end_time_day = db.Column(db.Time, nullable=False)


class Job(db.Model):
    __tablename__ = 'jobs'
    id_job = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.String(20), unique=True, nullable=False)


class StudentGroup(db.Model):
    __tablename__ = 'student_groups'
    id_group = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(100), nullable=False)


class ScheduleJob(db.Model):
    __tablename__ = 'schedule_jobs'
    id_schedule_job = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id_schedule', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id_job', ondelete='CASCADE'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('student_groups.id_group'))


class Person(db.Model):
    __tablename__ = 'people'
    id_person = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(20), nullable=False)
    firstname = db.Column(db.String(20), nullable=False)
    patronymic = db.Column(db.String(20))
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id_job'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('student_groups.id_group'))


class Pass(db.Model):
    __tablename__ = 'passes'
    id_pass = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('people.id_person'), nullable=False)
    start_date = db.Column(db.Date, nullable=False, server_default=db.func.current_date())
    end_date = db.Column(db.Date, nullable=False)


class Admin(db.Model, UserMixin):
    __tablename__ = 'admins'
    id_admin = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Log(db.Model):
    __tablename__ = 'logs'
    id_log = db.Column(db.Integer, primary_key=True)
    inside_status = db.Column(db.Boolean, nullable=False)
    pass_id = db.Column(db.Integer, db.ForeignKey('passes.id_pass', ondelete='CASCADE'), nullable=False)
    log_time = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())
    delay_time = db.Column(db.Time)


# db.create_all()


@app.route("/", methods=["GET", "POST"])
def start_page():
    result = db.session.query(db.func.count(db.func.distinct(Pass.id_pass)).label('count_pass'),
                              db.func.count(Log.id_log).label('count_logs')).join(Log).first()

    if request.method == "POST":
        id_pass = request.form["id"]
        if id_pass.isdigit():
            pass_info = Pass.query.filter(Pass.id_pass == id_pass).first()
        else:
            pass_info = None
        return render_template("main.html", out=result, res=True, out2=pass_info, old_id=id_pass)
    return render_template("main.html", out=result, res=False)


@app.route("/login", methods=["POST"])
def user_login():
    if request.method == "POST":
        login = request.form["login"]
        password = request.form["pass"]
        login_user(Admin)

        return redirect(url_for("work_page"))


@app.route("/work")
def work_page():
    result = Log.query.order_by(Log.id_log.desc()).limit(3).all()

    return render_template("work.html", logs=result)


@app.route("/journal")
def journal_page():
    query = text("SELECT * FROM journal_view")
    result = db.session.execute(query)
    return render_template("journal.html", jurnal=result)


@app.route("/new_log", methods=["POST"])
def new_log():
    if request.method == "POST":
        status = request.form["btn"]
        id_pass = request.form["id"]
        if db.session.query(Pass.id_pass).filter(Pass.id_pass == id_pass).scalar() is not None:
            log = Log(inside_status=status, pass_id=id_pass)
            db.session.add(log)
            db.session.commit()
        else:
            pass  # https://habr.com/ru/companies/otus/articles/692820/
        return redirect(url_for("work_page"))


@app.route("/delete_log/<int:id>")
def delete_log(id):
    print(id)
    return redirect(url_for("journal_page"))


@manager.user_loader
def load_user(admin_id):
    return Admin.query.get(admin_id)


if __name__ == "__main__":
    app.debug = True
    # app.run(host='0.0.0.0')
    app.run()