# -*- coding: utf8 -*-
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import Flask, redirect, render_template, request, abort
from data import db_session, users, jobs, departments
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = StringField("Почта", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class RegisterForm(FlaskForm):
    login = StringField("Login / email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    password_again = PasswordField("Repeat password", validators=[DataRequired()])
    surname = StringField("Surname", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    age = StringField("Age", validators=[DataRequired()])
    position = StringField("Position", validators=[DataRequired()])
    speciality = StringField("Speciality", validators=[DataRequired()])
    address = StringField("Address", validators=[DataRequired()])
    submit = SubmitField("Submit")


class AddJob(FlaskForm):
    job_title = StringField("Job Title", validators=[DataRequired()])
    team_leader = IntegerField("Team Leader ID", validators=[DataRequired()])
    work_size = IntegerField("Work Size", validators=[DataRequired()])
    collaborators = StringField("Collaborators", validators=[DataRequired()])
    is_finished = BooleanField("Is job finished?")
    submit = SubmitField("Submit")


class AddDepartment(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    chief = IntegerField("Chief", validators=[DataRequired()])
    members = StringField("Members", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    submit = SubmitField("Submit")


app = Flask(__name__)
app.config["SECRET_KEY"] = "yandexlyceum_secret_key"

login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init("db/mars.sqlite")


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(users.User).get(user_id)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(users.User).filter(users.User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template("login.html", message="Неправильный логин или пароль", form=form,
                               current_user=current_user)
    return render_template("login.html", form=form, current_user=current_user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template("register.html", form=form, message="Пароли не совпадают", current_user=current_user)
        session = db_session.create_session()
        if session.query(users.User).filter(users.User.email == form.login.data).first():
            return render_template("register.html", form=form, message="Такой пользователь уже есть",
                                   current_user=current_user)
        user = users.User(
            email=form.login.data,
            surname=form.surname.data,
            name=form.name.data,
            age=int(form.age.data),
            position=form.position.data,
            speciality=form.speciality.data,
            address=form.address.data
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template("register.html", form=form, current_user=current_user)


@app.route("/add_job", methods=["GET", "POST"])
@login_required
def add_job():
    form = AddJob()
    if form.validate_on_submit():
        session = db_session.create_session()
        if session.query(users.User).filter(users.User.id == form.team_leader.data).first():
            job = jobs.Jobs(
                team_leader=form.team_leader.data,
                job=form.job_title.data,
                work_size=form.work_size.data,
                collaborators=form.collaborators.data,
                is_finished=form.is_finished.data
            )
            session.add(job)
            session.commit()
            return redirect('/')
        return render_template("addjob.html", form=form, message="Несуществующий лидер", current_user=current_user,
                               title="Adding a Job")
    return render_template("addjob.html", form=form, current_user=current_user, title="Adding a Job")


@app.route("/edit_job/<int:id>", methods=["GET", "POST"])
@login_required
def edit_job(id):
    form = AddJob()
    if request.method == "GET":
        session = db_session.create_session()
        job = session.query(jobs.Jobs).filter(jobs.Jobs.id == id,
                                              (jobs.Jobs.user == current_user) | (current_user.id == 1)).first()
        if job:
            form.job_title.data = job.job
            form.team_leader.data = job.team_leader
            form.work_size.data = job.work_size
            form.collaborators.data = job.collaborators
            form.is_finished.data = job.is_finished
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        job = session.query(jobs.Jobs).filter(jobs.Jobs.id == id,
                                              (jobs.Jobs.user == current_user) | (current_user.id == 1)).first()
        if job:
            job.job = form.job_title.data
            job.team_leader = form.team_leader.data
            job.work_size = form.work_size.data
            job.collaborators = form.collaborators.data
            job.is_finished = form.is_finished.data
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template("addjob.html", title="Edit Job", form=form)


@app.route("/job_delete/<int:id>", methods=["POST", "GET"])
@login_required
def job_delete(id):
    session = db_session.create_session()
    job = session.query(jobs.Jobs).filter(jobs.Jobs.id == id,
                                          (jobs.Jobs.user == current_user) | (current_user.id == 1)).first()
    if job:
        session.delete(job)
        session.commit()
    else:
        abort(404)
    return redirect('/')


@app.route("/add_department", methods=["POST", "GET"])
@login_required
def add_department():
    form = AddDepartment()
    if form.validate_on_submit():
        session = db_session.create_session()
        if session.query(users.User).filter(users.User.id == form.chief.data).first():
            department = departments.Department(
                title=form.title.data,
                chief=form.chief.data,
                members=form.members.data,
                email=form.email.data
            )
            session.add(department)
            session.commit()
            return redirect('/departments')
        return render_template("add_department.html", form=form, title="Add a Department",
                               message="Несуществующий лидер")
    return render_template("add_department.html", form=form, title="Add a Department")


@app.route("/edit_department/<int:id>", methods=["GET", "POST"])
@login_required
def edit_department(id):
    form = AddDepartment()
    if request.method == "GET":
        session = db_session.create_session()
        department = session.query(departments.Department).filter(departments.Department.id == id,
                                                                  (departments.Department.user == current_user) | (
                                                                          current_user.id == 1)).first()
        if department:
            form.title.data = department.title
            form.chief.data = department.chief
            form.members.data = department.members
            form.email.data = department.email
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        department = session.query(departments.Department).filter(departments.Department.id == id,
                                                                  (departments.Department.user == current_user) | (
                                                                          current_user.id == 1)).first()
        if department:
            department.title = form.title.data
            department.chief = form.chief.data
            department.members = form.members.data
            department.email = form.email.data
            print(1)
            print(department.title, department.chief, department.members, department.email)
            session.commit()
            print(2)
            return redirect("/departments")
        else:
            abort(404)
    return render_template("add_department.html", title="Edit Department", form=form)


@app.route("/department_delete/<int:id>")
@login_required
def department_delete(id):
    session = db_session.create_session()
    department = session.query(departments.Department).filter(departments.Department.id == id,
                                                              (departments.Department.user == current_user) | (
                                                                          current_user.id == 1)).first()
    if department:
        session.delete(department)
        session.commit()
    else:
        abort(404)
    return redirect("/departments")


@app.route('/')
def table():
    session = db_session.create_session()
    jobs_ = session.query(jobs.Jobs).all()
    return render_template("tables.html", jobs=jobs_, current_user=current_user)


@app.route("/departments")
def dprt_table():
    session = db_session.create_session()
    departments_ = session.query(departments.Department).all()
    return render_template("departments.html", departments=departments_, current_user=current_user)


if __name__ == "__main__":
    app.run(port=8080, host="127.0.0.1")
