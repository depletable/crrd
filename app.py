import os
import sqlite3
import secrets
from flask import Flask, g, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")  # Change for prod!

# Setup serializer
serializer = URLSafeTimedSerializer(app.secret_key)

def init_db():
    if not os.path.exists(DATABASE):
        with app.app_context():
            db = get_db()
            with open("schema.sql", "r") as f:
                db.executescript(f.read())
            db.commit()


@app.before_request
def initialize():
    try:
        init_db()
    except Exception as e:
        app.logger.error("init_db failed", exc_info=e)
        raise

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

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    db = get_db()

    if request.method == "POST":
        display_name = request.form.get("display_name")
        avatar_url = request.form.get("avatar_url")
        bio = request.form.get("bio")
        card_size = request.form.get("card_size")
        twitter = request.form.get("twitter")
        github = request.form.get("github")
        website = request.form.get("website")

        db.execute("""
            UPDATE users SET
                display_name = ?, avatar_url = ?, bio = ?, card_size = ?,
                twitter = ?, github = ?, website = ?
            WHERE id = ?
        """, (display_name, avatar_url, bio, card_size, twitter, github, website, session["user_id"]))
        db.commit()

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

# Setup serializer
serializer = URLSafeTimedSerializer(app.secret_key)

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user:
            token = serializer.dumps(email, salt="password-reset-salt")
            reset_url = url_for("reset_password", token=token, _external=True)

            # In production, you'd email this. For now, display it:
            return f"Password reset link: <a href='{reset_url}'>{reset_url}</a>"

        return "If that email exists, a reset link was generated."

    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)
    except Exception:
        return "Reset link is invalid or expired."

    if request.method == "POST":
        new_password = request.form.get("password")
        hashed_pw = generate_password_hash(new_password)

        db = get_db()
        db.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_pw, email))
        db.commit()

        return redirect(url_for("login"))

    return render_template("reset_password.html")

@app.route("/migration")
def migrate():
    db = get_db()
    db.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
    db.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
    db.execute("ALTER TABLE users ADD COLUMN bio TEXT")
    db.execute("ALTER TABLE users ADD COLUMN card_size TEXT")
    db.execute("ALTER TABLE users ADD COLUMN twitter TEXT")
    db.execute("ALTER TABLE users ADD COLUMN github TEXT")
    db.execute("ALTER TABLE users ADD COLUMN website TEXT")
    db.commit()
    return "Migration complete."

if __name__ == "__main__":
    app.run(debug=True)
