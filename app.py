from flask import Flask, render_template, request, redirect, session, g
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = '07d97cdea578a2936f2701ae3da4b325'  # <-- Replace with something random and secure

DATABASE = 'database.db'

# Connect to the database
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

# Close database connection
@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Homepage
@app.route('/')
def index():
    return render_template('index.html', profile=None)

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        db = get_db()
        try:
            db.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            db.commit()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return "That email is already registered."
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect('/dashboard')
        else:
            return "Invalid login."
    return render_template('login.html')

# Dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()

    if request.method == 'POST':
        vanity = request.form['vanity']
        try:
            db.execute("INSERT INTO profiles (user_id, vanity) VALUES (?, ?)", (user['id'], vanity))
            db.commit()
        except sqlite3.IntegrityError:
            return "That vanity is already taken."

    profile = db.execute("SELECT * FROM profiles WHERE user_id = ?", (user['id'],)).fetchone()
    return render_template('dashboard.html', profile=profile)

# Public vanity page
@app.route('/<vanity>')
def vanity_profile(vanity):
    db = get_db()
    profile = db.execute("SELECT * FROM profiles WHERE vanity = ?", (vanity,)).fetchone()

    if not profile:
        return "Profile not found.", 404

    user = db.execute("SELECT * FROM users WHERE id = ?", (profile['user_id'],)).fetchone()

    return render_template("vanity.html", profile=profile, user=user)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
