"""
Authentication utilities and decorators
"""

from functools import wraps
from flask import session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password):
    """
    Hash a password using Werkzeug's secure PBKDF2 SHA256 method
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Hashed password
    """
    return generate_password_hash(password, method='pbkdf2:sha256')


def verify_password(password_hash, password):
    """
    Verify a password against its hash
    
    Args:
        password_hash (str): Stored password hash
        password (str): Plain text password to verify
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return check_password_hash(password_hash, password)


def login_required(f):
    """
    Decorator to protect routes that require authentication
    Redirects to login page if user is not authenticated
    
    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            return "This is protected"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user(mongo):
    """
    Get current logged-in user from database
    
    Args:
        mongo: Flask-PyMongo instance
        
    Returns:
        dict: User document or None
    """
    if 'user_id' not in session:
        return None
    
    from bson.objectid import ObjectId
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    return user


def validate_registration(name, email, password, confirm_password):
    """
    Validate registration form inputs
    
    Args:
        name (str): User's name
        email (str): User's email
        password (str): User's password
        confirm_password (str): Password confirmation
        
    Returns:
        tuple: (is_valid: bool, errors: dict)
    """
    errors = {}
    
    # Name validation
    if not name or len(name.strip()) < 2:
        errors['name'] = 'Name must be at least 2 characters long.'
    
    # Email validation (basic)
    if not email or '@' not in email or '.' not in email:
        errors['email'] = 'Please enter a valid email address.'
    
    # Password validation
    if not password or len(password) < 6:
        errors['password'] = 'Password must be at least 6 characters long.'
    
    # Confirm password validation
    if password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match.'
    
    return len(errors) == 0, errors


def validate_login(email, password):
    """
    Validate login form inputs
    
    Args:
        email (str): User's email
        password (str): User's password
        
    Returns:
        tuple: (is_valid: bool, errors: dict)
    """
    errors = {}
    
    if not email:
        errors['email'] = 'Email is required.'
    
    if not password:
        errors['password'] = 'Password is required.'
    
    return len(errors) == 0, errors
