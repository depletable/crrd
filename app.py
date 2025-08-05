import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")

DATABASE = "database.db"

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
    if request.method == "GET":
        vanity = request.args.get("vanity", "")
        return render_template("register.html", vanity=vanity)

@app.route("/<vanity>")
def profile(vanity):
    db = get_db()
    cur = db.execute("SELECT * FROM users WHERE vanity = ?", (vanity,))
    user = cur.fetchone()
    if user is None:
        return "Vanity not found", 404
    # You can customize this template to show user links, etc.
    return render_template("profile.html", profile=user)


    # POST method: process registration
    vanity = request.form.get("vanity", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not vanity or not email or not password:
        flash("All fields are required.")
        return redirect(url_for("register", vanity=vanity))

    db = get_db()

    # Check if vanity is taken
    cur = db.execute("SELECT * FROM users WHERE vanity = ?", (vanity,))
    if cur.fetchone():
        flash("Vanity is already taken.")
        return redirect(url_for("register"))

    # Check if email is taken
    cur = db.execute("SELECT * FROM users WHERE email = ?", (email,))
    if cur.fetchone():
        flash("Email is already registered.")
        return redirect(url_for("register", vanity=vanity))

    hashed_password = generate_password_hash(password)

    db.execute(
        "INSERT INTO users (vanity, email, password) VALUES (?, ?, ?)",
        (vanity, email, hashed_password),
    )
    db.commit()
    flash("Registration successful. Please log in.")
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Email and password are required.")
        return redirect(url_for("login"))

    db = get_db()
    cur = db.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()

    if user is None or not check_password_hash(user["password"], password):
        flash("Invalid email or password.")
        return redirect(url_for("login"))

    session["user_id"] = user["id"]
    session["vanity"] = user["vanity"]
    flash("Logged in successfully.")
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", vanity=session.get("vanity"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
