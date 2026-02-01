"""
Smart Study Planner - Main Application Entry Point
Flask application with MongoDB backend for intelligent exam preparation planning
"""

import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for
from flask_pymongo import PyMongo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/smart_study_planner')

# Initialize MongoDB
mongo = PyMongo(app)

# Make mongo available to all routes
app.mongo = mongo

# Create database indexes for performance
def create_indexes():
    """Create database indexes on application startup"""
    try:
        # Users collection
        mongo.db.users.create_index('email', unique=True)
        
        # Subjects collection
        mongo.db.subjects.create_index('user_id')
        mongo.db.subjects.create_index('exam_date')
        
        # Topics collection
        mongo.db.topics.create_index('user_id')
        mongo.db.topics.create_index('subject_id')
        mongo.db.topics.create_index([('user_id', 1), ('subject_id', 1)])
        
        # Sessions collection
        mongo.db.sessions.create_index('user_id')
        mongo.db.sessions.create_index('date')
        mongo.db.sessions.create_index('status')
        mongo.db.sessions.create_index([('user_id', 1), ('date', 1)])
        mongo.db.sessions.create_index([('user_id', 1), ('status', 1)])
        
        # Study logs collection
        mongo.db.study_logs.create_index('user_id')
        mongo.db.study_logs.create_index('logged_at')
        mongo.db.study_logs.create_index([('user_id', 1), ('logged_at', -1)])
        
        print("✓ Database indexes created successfully")
    except Exception as e:
        print(f"⚠ Warning: Could not create indexes - {e}")

# Import routes
from routes.auth_routes import auth_bp
from routes.subject_routes import subjects_bp
from routes.planner_routes import planner_bp
from routes.dashboard_routes import dashboard_bp
from routes.progress_routes import progress_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(subjects_bp)
app.register_blueprint(planner_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(progress_bp)

# Landing page route
@app.route('/')
def landing():
    """Landing page - public"""
    return render_template('landing.html')

# Context processor for global template variables
@app.context_processor
def inject_globals():
    """Make common variables available to all templates"""
    return {
        'now': datetime.now(),
        'current_year': datetime.now().year
    }

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('errors/500.html'), 500

# Application entry point
if __name__ == '__main__':
    # Create indexes on startup
    with app.app_context():
        create_indexes()
    
    # Run the application
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"\n{'='*60}")
    print(f"🎓 Smart Study Planner Starting...")
    print(f"{'='*60}")
    print(f"📍 URL: http://localhost:{port}")
    print(f"🔧 Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"🗄️  Database: {app.config['MONGO_URI'].split('@')[-1] if '@' in app.config['MONGO_URI'] else app.config['MONGO_URI']}")
    print(f"{'='*60}\n")
    
    app.run(host=host, port=port, debug=debug)
