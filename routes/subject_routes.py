"""
Subject and topic management routes
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from datetime import datetime
from bson.objectid import ObjectId
from utils.auth import login_required
from utils.db_helpers import get_subjects_for_user, get_topics_for_subject, get_topic_statistics

subjects_bp = Blueprint('subjects', __name__)


@subjects_bp.route('/subjects')
@login_required
def list_subjects():
    """List all subjects for the user"""
    user_id = session['user_id']
    subjects = get_subjects_for_user(current_app.mongo, user_id)
    
    # Get statistics for each subject
    for subject in subjects:
        stats = get_topic_statistics(current_app.mongo, user_id, str(subject['_id']))
        subject['stats'] = stats
    
    return render_template('subjects/list.html', subjects=subjects)


@subjects_bp.route('/subjects/add', methods=['POST'])
@login_required
def add_subject():
    """Add a new subject"""
    user_id = session['user_id']
    
    # Get form data
    name = request.form.get('name', '').strip()
    exam_date_str = request.form.get('exam_date', '').strip()
    difficulty = request.form.get('difficulty', '3')
    color = request.form.get('color', '#3B82F6')
    
    # Validation
    errors = {}
    if not name:
        errors['name'] = 'Subject name is required.'
    
    if not exam_date_str:
        errors['exam_date'] = 'Exam date is required.'
    
    try:
        difficulty = int(difficulty)
        if difficulty < 1 or difficulty > 5:
            errors['difficulty'] = 'Difficulty must be between 1 and 5.'
    except ValueError:
        errors['difficulty'] = 'Difficulty must be a number between 1 and 5.'
    
    # Parse exam date
    try:
        exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d')
    except ValueError:
        errors['exam_date'] = 'Invalid date format. Use YYYY-MM-DD.'
    
    if errors:
        flash('Please correct the errors in the form.', 'error')
        return redirect(url_for('subjects.list_subjects'))
    
    # Create subject document
    subject_doc = {
        'user_id': ObjectId(user_id),
        'name': name,
        'exam_date': exam_date,
        'difficulty': difficulty,
        'color': color,
        'created_at': datetime.now()
    }
    
    current_app.mongo.db.subjects.insert_one(subject_doc)
    
    flash(f'Subject "{name}" added successfully!', 'success')
    return redirect(url_for('subjects.list_subjects'))


@subjects_bp.route('/subjects/<subject_id>/edit', methods=['POST'])
@login_required
def edit_subject(subject_id):
    """Edit an existing subject"""
    user_id = session['user_id']
    
    # Verify ownership
    subject = current_app.mongo.db.subjects.find_one({
        '_id': ObjectId(subject_id),
        'user_id': ObjectId(user_id)
    })
    
    if not subject:
        flash('Subject not found.', 'error')
        return redirect(url_for('subjects.list_subjects'))
    
    # Get form data
    name = request.form.get('name', '').strip()
    exam_date_str = request.form.get('exam_date', '').strip()
    difficulty = request.form.get('difficulty', '3')
    color = request.form.get('color', '#3B82F6')
    
    # Validation
    if not name:
        flash('Subject name is required.', 'error')
        return redirect(url_for('subjects.list_subjects'))
    
    try:
        difficulty = int(difficulty)
        if difficulty < 1 or difficulty > 5:
            flash('Difficulty must be between 1 and 5.', 'error')
            return redirect(url_for('subjects.list_subjects'))
    except ValueError:
        flash('Difficulty must be a number.', 'error')
        return redirect(url_for('subjects.list_subjects'))
    
    try:
        exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d')
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('subjects.list_subjects'))
    
    # Update subject
    current_app.mongo.db.subjects.update_one(
        {'_id': ObjectId(subject_id)},
        {'$set': {
            'name': name,
            'exam_date': exam_date,
            'difficulty': difficulty,
            'color': color
        }}
    )
    
    flash(f'Subject "{name}" updated successfully!', 'success')
    return redirect(url_for('subjects.list_subjects'))


@subjects_bp.route('/subjects/<subject_id>/delete', methods=['POST'])
@login_required
def delete_subject(subject_id):
    """Delete a subject and all its topics and sessions"""
    user_id = session['user_id']
    
    # Verify ownership
    subject = current_app.mongo.db.subjects.find_one({
        '_id': ObjectId(subject_id),
        'user_id': ObjectId(user_id)
    })
    
    if not subject:
        flash('Subject not found.', 'error')
        return redirect(url_for('subjects.list_subjects'))
    
    subject_name = subject['name']
    
    # Delete related topics
    current_app.mongo.db.topics.delete_many({
        'user_id': ObjectId(user_id),
        'subject_id': ObjectId(subject_id)
    })
    
    # Delete related sessions
    current_app.mongo.db.sessions.delete_many({
        'user_id': ObjectId(user_id),
        'subject_id': ObjectId(subject_id)
    })
    
    # Delete subject
    current_app.mongo.db.subjects.delete_one({'_id': ObjectId(subject_id)})
    
    flash(f'Subject "{subject_name}" and all related data deleted successfully.', 'success')
    return redirect(url_for('subjects.list_subjects'))


@subjects_bp.route('/subjects/<subject_id>/topics')
@login_required
def manage_topics(subject_id):
    """Manage topics for a specific subject"""
    user_id = session['user_id']
    
    # Get subject
    subject = current_app.mongo.db.subjects.find_one({
        '_id': ObjectId(subject_id),
        'user_id': ObjectId(user_id)
    })
    
    if not subject:
        flash('Subject not found.', 'error')
        return redirect(url_for('subjects.list_subjects'))
    
    # Get topics
    topics = get_topics_for_subject(current_app.mongo, user_id, subject_id)
    
    # Get statistics
    stats = get_topic_statistics(current_app.mongo, user_id, subject_id)
    
    return render_template('subjects/topics.html',
                         subject=subject,
                         topics=topics,
                         stats=stats)


@subjects_bp.route('/subjects/<subject_id>/topics/add', methods=['POST'])
@login_required
def add_topic(subject_id):
    """Add a new topic to a subject"""
    user_id = session['user_id']
    
    # Verify subject ownership
    subject = current_app.mongo.db.subjects.find_one({
        '_id': ObjectId(subject_id),
        'user_id': ObjectId(user_id)
    })
    
    if not subject:
        flash('Subject not found.', 'error')
        return redirect(url_for('subjects.list_subjects'))
    
    # Get form data
    title = request.form.get('title', '').strip()
    estimated_minutes = request.form.get('estimated_minutes', '60')
    
    # Validation
    if not title:
        flash('Topic title is required.', 'error')
        return redirect(url_for('subjects.manage_topics', subject_id=subject_id))
    
    try:
        estimated_minutes = int(estimated_minutes)
        if estimated_minutes < 1:
            flash('Estimated minutes must be at least 1.', 'error')
            return redirect(url_for('subjects.manage_topics', subject_id=subject_id))
    except ValueError:
        flash('Estimated minutes must be a number.', 'error')
        return redirect(url_for('subjects.manage_topics', subject_id=subject_id))
    
    # Create topic document
    topic_doc = {
        'user_id': ObjectId(user_id),
        'subject_id': ObjectId(subject_id),
        'title': title,
        'estimated_minutes': estimated_minutes,
        'status': 'pending',
        'created_at': datetime.now()
    }
    
    current_app.mongo.db.topics.insert_one(topic_doc)
    
    flash(f'Topic "{title}" added successfully!', 'success')
    return redirect(url_for('subjects.manage_topics', subject_id=subject_id))


@subjects_bp.route('/topics/<topic_id>/toggle', methods=['POST'])
@login_required
def toggle_topic(topic_id):
    """Toggle topic completion status"""
    user_id = session['user_id']
    
    # Get topic
    topic = current_app.mongo.db.topics.find_one({
        '_id': ObjectId(topic_id),
        'user_id': ObjectId(user_id)
    })
    
    if not topic:
        return jsonify({'error': 'Topic not found'}), 404
    
    # Toggle status
    new_status = 'completed' if topic['status'] == 'pending' else 'pending'
    
    current_app.mongo.db.topics.update_one(
        {'_id': ObjectId(topic_id)},
        {'$set': {'status': new_status}}
    )
    
    return jsonify({
        'success': True,
        'new_status': new_status
    })


@subjects_bp.route('/topics/<topic_id>/delete', methods=['POST'])
@login_required
def delete_topic(topic_id):
    """Delete a topic"""
    user_id = session['user_id']
    
    # Get topic
    topic = current_app.mongo.db.topics.find_one({
        '_id': ObjectId(topic_id),
        'user_id': ObjectId(user_id)
    })
    
    if not topic:
        flash('Topic not found.', 'error')
        return redirect(url_for('subjects.list_subjects'))
    
    subject_id = str(topic['subject_id'])
    topic_title = topic['title']
    
    # Delete related sessions
    current_app.mongo.db.sessions.delete_many({
        'user_id': ObjectId(user_id),
        'topic_id': ObjectId(topic_id)
    })
    
    # Delete topic
    current_app.mongo.db.topics.delete_one({'_id': ObjectId(topic_id)})
    
    flash(f'Topic "{topic_title}" deleted successfully.', 'success')
    return redirect(url_for('subjects.manage_topics', subject_id=subject_id))
