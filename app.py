import os
import sqlite3
from flask import Flask, g, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

def init_db():
    if not os.path.exists(DATABASE):
        with app.app_context():
            db = get_db()
            with open("schema.sql", "r") as f:
                db.executescript(f.read())
            db.commit()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")  # Change for prod!

init_db()

DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database.db")

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        vanity = request.form.get("vanity")

        if not email or not password or not vanity:
            return "Email, password, and vanity are required.", 400

        db = get_db()

        # Check if vanity or email already exists
        user_check = db.execute("SELECT * FROM users WHERE email = ? OR vanity = ?", (email, vanity)).fetchone()
        if user_check:
            return "Email or vanity already taken.", 400

        hashed_pw = generate_password_hash(password)
        db.execute(
            "INSERT INTO users (email, password, vanity) VALUES (?, ?, ?)",
            (email, hashed_pw, vanity)
        )
        db.commit()

        return redirect(url_for("login"))

    # GET method: get vanity from query params to prefill form
    vanity = request.args.get("vanity", "")
    return render_template("register.html", vanity=vanity)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["vanity"] = user["vanity"]
            return redirect(url_for("dashboard"))
        else:
            return "Invalid email or password.", 400

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    return render_template("dashboard.html", profile=user)

@app.route("/<vanity>")
def profile(vanity):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE vanity = ?", (vanity,)).fetchone()
    if user is None:
        return "Vanity not found", 404
    return render_template("profile.html", profile=user)

@app.route("/claim", methods=["POST"])
def claim():
    vanity = request.form.get("vanity")
    if not vanity:
        return redirect(url_for("index"))
    # redirect to register with vanity prefilled as query param
    return redirect(url_for("register") + f"?vanity={vanity}")

if __name__ == "__main__":
    app.run(debug=True)
