from flask import Flask, render_template, request, redirect, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with your own

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return 'Welcome to crrd! Go to /register or /login'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = get_db()
        try:
            conn.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, password))
            conn.commit()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return "Email already registered"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            return redirect('/dashboard')
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (session['user_id'],)).fetchone()

    if request.method == 'POST':
        vanity = request.form['vanity']
        if profile:
            return "You already claimed a vanity name"
        try:
            conn.execute("INSERT INTO profiles (user_id, vanity) VALUES (?, ?)", (session['user_id'], vanity))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Vanity already taken"
        return redirect('/dashboard')

    return render_template('dashboard.html', profile=profile)

@app.route('/<vanity>')
def view_profile(vanity):
    conn = get_db()
    profile = conn.execute("SELECT * FROM profiles WHERE vanity = ?", (vanity,)).fetchone()
    if not profile:
        abort(404)
    return render_template('index.html', profile=profile)
