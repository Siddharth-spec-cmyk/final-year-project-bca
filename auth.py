import json
import os
from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

auth_app = Blueprint('auth_app', __name__)

USERS_FILE = 'users.json'

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

@auth_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

        if username in users and check_password_hash(users[username]['password'], password):
            session['user'] = username
            return redirect(url_for('tool_app.tools'))
        else:
            return render_template('login.html', error='Invalid credentials.')

    return render_template('login.html')

@auth_app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

        if username in users:
            return render_template('register.html', error='User already exists. Please log in.')

        # Hash the password before storing
        hashed_password = generate_password_hash(password)
        users[username] = {'password': hashed_password, 'stocks': []}
        save_users(users)

        return redirect(url_for('auth_app.login'))

    return render_template('register.html')

@auth_app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('auth_app.login'))

@auth_app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('auth_app.login'))

    users = load_users()
    username = session['user']
    user_data = users.get(username, {})

    return render_template('user.html', username=username, stocks=user_data.get("stocks", []))
