"""
Authentication routes: register, login, logout
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from bson.objectid import ObjectId
from datetime import datetime
from utils.auth import hash_password, verify_password, validate_registration, validate_login

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate inputs
        is_valid, errors = validate_registration(name, email, password, confirm_password)
        
        if not is_valid:
            return render_template('auth/register.html', 
                                 errors=errors,
                                 name=name,
                                 email=email)
        
        # Check if email already exists
        existing_user = current_app.mongo.db.users.find_one({'email': email})
        if existing_user:
            return render_template('auth/register.html',
                                 errors={'email': 'This email is already registered.'},
                                 name=name,
                                 email=email)
        
        # Create user document
        user_doc = {
            'name': name,
            'email': email,
            'password_hash': hash_password(password),
            'created_at': datetime.now()
        }
        
        # Insert user
        result = current_app.mongo.db.users.insert_one(user_doc)
        
        # Log user in automatically
        session['user_id'] = str(result.inserted_id)
        session['user_name'] = name
        session['user_email'] = email
        
        flash(f'Welcome, {name}! Your account has been created successfully.', 'success')
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        # Validate inputs
        is_valid, errors = validate_login(email, password)
        
        if not is_valid:
            return render_template('auth/login.html',
                                 errors=errors,
                                 email=email)
        
        # Find user
        user = current_app.mongo.db.users.find_one({'email': email})
        
        if not user:
            return render_template('auth/login.html',
                                 errors={'email': 'No account found with this email.'},
                                 email=email)
        
        # Verify password
        if not verify_password(user['password_hash'], password):
            return render_template('auth/login.html',
                                 errors={'password': 'Incorrect password.'},
                                 email=email)
        
        # Log user in
        session['user_id'] = str(user['_id'])
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        
        flash(f'Welcome back, {user["name"]}!', 'success')
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """User logout"""
    user_name = session.get('user_name', 'User')
    
    # Clear session
    session.clear()
    
    flash(f'Goodbye, {user_name}! You have been logged out.', 'info')
    return redirect(url_for('landing'))
