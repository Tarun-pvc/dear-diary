from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from ..db import mongo

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Please provide both username and password', 'error')
            return redirect(url_for('auth.signup'))
        # Check if user already exists
        user = mongo.db.users.find_one({'username': username})
        if user:
            flash('Username already exists', 'error')
            return redirect(url_for('auth.signup'))
        # Hash the password for security
        hashed_pw = generate_password_hash(password)
        mongo.db.users.insert_one({'username': username, 'password': hashed_pw})
        flash('Signup successful, please login', 'success')
        return redirect(url_for('auth.login'))
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = mongo.db.users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            flash('Logged in successfully', 'success')
            return redirect(url_for('diary.dashboard'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))
