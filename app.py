import os
from datetime import datetime, date, timedelta
from functools import wraps

import click
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func, or_
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-this-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "mysql+pymysql://sevaqueue:change_me@localhost/sevaqueue"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["REMEMBER_COOKIE_HTTPONLY"] = True

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"

SERVICES = [
    "Certificate Service",
    "Application Submission",
    "Document Verification",
    "Complaint / Enquiry",
]
STATUSES = ["Waiting", "Serving", "Completed", "Cancelled", "Skipped"]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="citizen")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    appointments = db.relationship("Appointment", backref="citizen", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    service = db.Column(db.String(80), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False, index=True)
    appointment_time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Waiting", index=True)
    notes = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def make_token():
    # Token is unique in the database; retry in the unlikely event of collision.
    for _ in range(10):
        candidate = f"SQ-{datetime.utcnow():%y%m%d}-{os.urandom(2).hex().upper()}"
        if not Appointment.query.filter_by(token=candidate).first():
            return candidate
    raise RuntimeError("Could not generate a unique appointment token.")


@app.context_processor
def inject_globals():
    return {"now": date.today(), "services": SERVICES, "statuses": STATUSES}


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(name) < 2 or len(name) > 100:
            flash("Please enter a name between 2 and 100 characters.", "danger")
        elif "@" not in email or len(email) > 150:
            flash("Please enter a valid email address.", "danger")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
        else:
            user = User(full_name=name, email=email, role="citizen")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to SevaQueue. Your citizen account is ready.", "success")
            return redirect(url_for("dashboard"))
    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.full_name.split()[0]}.", "success")
            return redirect(url_for("dashboard"))
        flash("Email or password was incorrect.", "danger")
    return render_template("auth.html", mode="login")


@app.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    today = date.today()
    if current_user.role == "citizen":
        base = Appointment.query.filter_by(user_id=current_user.id)
    else:
        base = Appointment.query

    total = base.count()
    waiting = base.filter(Appointment.status == "Waiting").count()
    completed = base.filter(Appointment.status == "Completed").count()
    today_count = base.filter(Appointment.appointment_date == today).count()
    recent = base.order_by(Appointment.created_at.desc()).limit(8).all()

    # Seven-day chart; use local dates and fill missing dates with zero.
    labels, counts = [], []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        labels.append(day.strftime("%d %b"))
        q = db.session.query(func.count(Appointment.id)).filter(
            Appointment.appointment_date == day
        )
        if current_user.role == "citizen":
            q = q.filter(Appointment.user_id == current_user.id)
        counts.append(q.scalar() or 0)

    service_rows = db.session.query(
        Appointment.service, func.count(Appointment.id)
    )
    if current_user.role == "citizen":
        service_rows = service_rows.filter(Appointment.user_id == current_user.id)
    service_rows = service_rows.group_by(Appointment.service).all()

    return render_template(
        "dashboard.html", total=total, waiting=waiting, completed=completed,
        today_count=today_count, recent=recent, chart_labels=labels,
        chart_counts=counts, service_labels=[x[0] for x in service_rows],
        service_counts=[x[1] for x in service_rows],
    )


@app.route("/appointments", methods=["GET", "POST"])
@login_required
def appointments():
    if request.method == "POST":
        service = request.form.get("service", "")
        appointment_date = request.form.get("appointment_date", "")
        appointment_time = request.form.get("appointment_time", "")
        notes = request.form.get("notes", "").strip()
        try:
            parsed_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        except ValueError:
            parsed_date = None
        if service not in SERVICES:
            flash("Please choose a valid service.", "danger")
        elif not parsed_date or parsed_date < date.today():
            flash("Please choose today or a future date.", "danger")
        elif appointment_time not in [
            "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM",
            "12:00 PM", "02:00 PM", "02:30 PM", "03:00 PM"
        ]:
            flash("Please choose a valid time slot.", "danger")
        elif len(notes) > 300:
            flash("Notes must be 300 characters or fewer.", "danger")
        else:
            appointment = Appointment(
                token=make_token(), user_id=current_user.id, service=service,
                appointment_date=parsed_date, appointment_time=appointment_time,
                notes=notes or None,
            )
            db.session.add(appointment)
            db.session.commit()
            flash(f"Appointment created. Your token is {appointment.token}.", "success")
            return redirect(url_for("appointments"))
    query = Appointment.query
    if current_user.role == "citizen":
        query = query.filter_by(user_id=current_user.id)
    if request.args.get("status") in STATUSES:
        query = query.filter_by(status=request.args["status"])
    if request.args.get("q", "").strip():
        search = f"%{request.args['q'].strip()}%"
        if current_user.role != "citizen":
            query = query.join(User).filter(
                or_(Appointment.token.ilike(search), Appointment.service.ilike(search),
                    User.full_name.ilike(search), User.email.ilike(search))
            )
        else:
            query = query.filter(
                or_(Appointment.token.ilike(search), Appointment.service.ilike(search))
            )
    rows = query.order_by(Appointment.appointment_date.desc(), Appointment.created_at.desc()).all()
    return render_template("appointments.html", appointments=rows)


@app.post("/appointments/<int:appointment_id>/cancel")
@login_required
def cancel_appointment(appointment_id):
    appointment = db.get_or_404(Appointment, appointment_id)
    if current_user.role == "citizen" and appointment.user_id != current_user.id:
        abort(403)
    if appointment.status not in ("Waiting",):
        flash("Only waiting appointments can be cancelled.", "warning")
    else:
        appointment.status = "Cancelled"
        db.session.commit()
        flash(f"Appointment {appointment.token} cancelled.", "success")
    return redirect(url_for("appointments"))


@app.post("/appointments/<int:appointment_id>/status")
@roles_required("staff", "admin")
def update_status(appointment_id):
    appointment = db.get_or_404(Appointment, appointment_id)
    new_status = request.form.get("status", "")
    if new_status not in STATUSES:
        flash("Invalid status.", "danger")
    else:
        appointment.status = new_status
        db.session.commit()
        flash(f"{appointment.token} updated to {new_status}.", "success")
    return redirect(request.referrer or url_for("appointments"))


@app.route("/reports")
@roles_required("staff", "admin")
def reports():
    total = Appointment.query.count()
    completed = Appointment.query.filter_by(status="Completed").count()
    waiting = Appointment.query.filter_by(status="Waiting").count()
    cancelled = Appointment.query.filter_by(status="Cancelled").count()
    start = date.today() - timedelta(days=29)
    daily = db.session.query(
        Appointment.appointment_date, func.count(Appointment.id)
    ).filter(Appointment.appointment_date >= start).group_by(
        Appointment.appointment_date
    ).order_by(Appointment.appointment_date).all()
    by_service = db.session.query(
        Appointment.service, func.count(Appointment.id)
    ).group_by(Appointment.service).all()
    by_status = db.session.query(
        Appointment.status, func.count(Appointment.id)
    ).group_by(Appointment.status).all()
    return render_template(
        "reports.html", total=total, completed=completed, waiting=waiting,
        cancelled=cancelled, daily_labels=[x[0].strftime("%d %b") for x in daily],
        daily_counts=[x[1] for x in daily],
        service_labels=[x[0] for x in by_service],
        service_counts=[x[1] for x in by_service],
        status_labels=[x[0] for x in by_status],
        status_counts=[x[1] for x in by_status],
    )


@app.route("/admin/users")
@roles_required("admin")
def users():
    return render_template("users.html", users=User.query.order_by(User.created_at.desc()).all())


@app.post("/admin/users/<int:user_id>/role")
@roles_required("admin")
def change_role(user_id):
    user = db.get_or_404(User, user_id)
    role = request.form.get("role", "")
    if role not in ("citizen", "staff", "admin"):
        flash("Invalid role selected.", "danger")
    elif user.id == current_user.id and role != "admin":
        flash("You cannot remove your own admin role.", "warning")
    else:
        user.role = role
        db.session.commit()
        flash(f"Role updated for {user.full_name}.", "success")
    return redirect(url_for("users"))


@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="You don't have permission to access this page."), 403


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="We couldn't find that page or record."), 404


@app.cli.command("init-db")
def init_db():
    """Create database tables."""
    db.create_all()
    click.echo("Database tables created.")


@app.cli.command("create-admin")
@click.option("--name", prompt="Admin full name")
@click.option("--email", prompt="Admin email")
@click.password_option()
def create_admin(name, email, password):
    """Create an administrator account."""
    email = email.strip().lower()
    if User.query.filter_by(email=email).first():
        click.echo("That email already exists.")
        return
    user = User(full_name=name.strip(), email=email, role="admin")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Admin account created for {email}.")


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
