"""
Planner routes: plan generation, timetable view, session actions
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from utils.auth import login_required
from utils.planner import StudyPlanner, get_plan_explanation
from utils.db_helpers import get_subjects_for_user, get_sessions_for_date

planner_bp = Blueprint('planner', __name__)


@planner_bp.route('/planner')
@login_required
def planner():
    """Planner overview and generation page"""
    user_id = session['user_id']
    
    # Get latest plan
    latest_plan = current_app.mongo.db.plans.find_one(
        {'user_id': ObjectId(user_id)},
        sort=[('created_at', -1)]
    )
    
    # Get subjects for form defaults
    subjects = get_subjects_for_user(current_app.mongo, user_id)
    
    # Calculate default end date (latest exam date)
    default_end_date = None
    if subjects:
        exam_dates = [s['exam_date'] for s in subjects if s.get('exam_date')]
        if exam_dates:
            default_end_date = max(exam_dates)
    
    if not default_end_date:
        default_end_date = datetime.now() + timedelta(days=30)
    
    # Get plan explanation
    explanations = get_plan_explanation(current_app.mongo, user_id)
    
    return render_template('planner/generate.html',
                         latest_plan=latest_plan,
                         subjects=subjects,
                         default_end_date=default_end_date,
                         explanations=explanations)


@planner_bp.route('/planner/generate', methods=['POST'])
@login_required
def generate_plan():
    """Generate a new study plan"""
    user_id = session['user_id']
    
    # Get form data
    daily_study_minutes = request.form.get('daily_study_minutes', '240')
    start_date_str = request.form.get('start_date', '')
    end_date_str = request.form.get('end_date', '')
    max_sessions_per_day = request.form.get('max_sessions_per_day', '4')
    revision_buffer_days = request.form.get('revision_buffer_days', '2')
    
    # Validation
    errors = {}
    
    try:
        daily_study_minutes = int(daily_study_minutes)
        if daily_study_minutes < 30 or daily_study_minutes > 720:
            errors['daily_study_minutes'] = 'Daily study time must be between 30 and 720 minutes.'
    except ValueError:
        errors['daily_study_minutes'] = 'Daily study time must be a number.'
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    except ValueError:
        errors['start_date'] = 'Invalid start date format.'
        start_date = datetime.now()
    
    try:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except ValueError:
        errors['end_date'] = 'Invalid end date format.'
        end_date = datetime.now() + timedelta(days=30)
    
    try:
        max_sessions_per_day = int(max_sessions_per_day)
        if max_sessions_per_day < 1 or max_sessions_per_day > 10:
            errors['max_sessions_per_day'] = 'Max sessions per day must be between 1 and 10.'
    except ValueError:
        errors['max_sessions_per_day'] = 'Max sessions per day must be a number.'
    
    try:
        revision_buffer_days = int(revision_buffer_days)
        if revision_buffer_days < 0 or revision_buffer_days > 7:
            errors['revision_buffer_days'] = 'Revision buffer must be between 0 and 7 days.'
    except ValueError:
        errors['revision_buffer_days'] = 'Revision buffer must be a number.'
    
    if start_date >= end_date:
        errors['date_range'] = 'End date must be after start date.'
    
    if errors:
        for error in errors.values():
            flash(error, 'error')
        return redirect(url_for('planner.planner'))
    
    # Generate plan
    planner_instance = StudyPlanner(current_app.mongo, user_id)
    
    config = {
        'daily_study_minutes': daily_study_minutes,
        'start_date': start_date,
        'end_date': end_date,
        'blocks': ['Morning', 'Afternoon', 'Evening'],
        'max_sessions_per_day': max_sessions_per_day,
        'revision_buffer_days': revision_buffer_days
    }
    
    result = planner_instance.generate_plan(config)
    
    if 'error' in result:
        flash(result['error'], 'error')
        return redirect(url_for('planner.planner'))
    
    flash(f'Study plan generated successfully! {result["total_sessions"]} sessions created.', 'success')
    return redirect(url_for('planner.timetable'))


@planner_bp.route('/timetable')
@login_required
def timetable():
    """Weekly timetable view"""
    user_id = session['user_id']
    
    # Get week offset from query param (default: current week)
    week_offset = request.args.get('week', 0, type=int)
    
    # Calculate week start (Monday)
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    
    # Get 7 days starting from Monday
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    
    # Get sessions for each day
    week_data = []
    for date in week_dates:
        day_sessions = get_sessions_for_date(current_app.mongo, user_id, date)
        
        # Group by block
        sessions_by_block = {
            'Morning': [],
            'Afternoon': [],
            'Evening': []
        }
        
        for sess in day_sessions:
            block = sess.get('block', 'Morning')
            if block in sessions_by_block:
                sessions_by_block[block].append(sess)
        
        week_data.append({
            'date': date,
            'day_name': date.strftime('%A'),
            'day_number': date.day,
            'is_today': date.date() == today.date(),
            'sessions_by_block': sessions_by_block
        })
    
    # Get view mode (grid or list)
    view_mode = request.args.get('view', 'grid')
    
    return render_template('planner/timetable.html',
                         week_data=week_data,
                         week_offset=week_offset,
                         view_mode=view_mode,
                         start_of_week=start_of_week)


@planner_bp.route('/sessions/<session_id>/complete', methods=['POST'])
@login_required
def complete_session(session_id):
    """Mark a session as completed"""
    user_id = session['user_id']
    
    # Get session
    sess = current_app.mongo.db.sessions.find_one({
        '_id': ObjectId(session_id),
        'user_id': ObjectId(user_id)
    })
    
    if not sess:
        return jsonify({'error': 'Session not found'}), 404
    
    # Get actual minutes from form (optional)
    actual_minutes = request.form.get('actual_minutes', sess['planned_minutes'])
    
    try:
        actual_minutes = int(actual_minutes)
    except ValueError:
        actual_minutes = sess['planned_minutes']
    
    notes = request.form.get('notes', '').strip()
    
    # Update session
    current_app.mongo.db.sessions.update_one(
        {'_id': ObjectId(session_id)},
        {
            '$set': {
                'status': 'completed',
                'actual_minutes': actual_minutes,
                'notes': notes,
                'completed_at': datetime.now()
            }
        }
    )
    
    # Create study log
    log_doc = {
        'user_id': ObjectId(user_id),
        'session_id': ObjectId(session_id),
        'subject_id': sess['subject_id'],
        'topic_id': sess['topic_id'],
        'actual_minutes': actual_minutes,
        'notes': notes,
        'logged_at': datetime.now()
    }
    
    current_app.mongo.db.study_logs.insert_one(log_doc)
    
    flash('Session marked as completed!', 'success')
    return redirect(request.referrer or url_for('dashboard.dashboard'))


@planner_bp.route('/sessions/<session_id>/skip', methods=['POST'])
@login_required
def skip_session(session_id):
    """Skip a session (moves to backlog)"""
    user_id = session['user_id']
    
    # Get session
    sess = current_app.mongo.db.sessions.find_one({
        '_id': ObjectId(session_id),
        'user_id': ObjectId(user_id)
    })
    
    if not sess:
        return jsonify({'error': 'Session not found'}), 404
    
    # Update status to skipped
    current_app.mongo.db.sessions.update_one(
        {'_id': ObjectId(session_id)},
        {'$set': {'status': 'skipped'}}
    )
    
    flash('Session skipped. It has been added to your backlog.', 'info')
    return redirect(request.referrer or url_for('dashboard.dashboard'))


@planner_bp.route('/sessions/<session_id>/reschedule', methods=['POST'])
@login_required
def reschedule_session(session_id):
    """Reschedule a session to a different date/block"""
    user_id = session['user_id']
    
    # Get session
    sess = current_app.mongo.db.sessions.find_one({
        '_id': ObjectId(session_id),
        'user_id': ObjectId(user_id)
    })
    
    if not sess:
        flash('Session not found.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    # Get new date and block
    new_date_str = request.form.get('new_date', '')
    new_block = request.form.get('new_block', 'Morning')
    
    try:
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d')
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(request.referrer or url_for('dashboard.dashboard'))
    
    # Update session
    current_app.mongo.db.sessions.update_one(
        {'_id': ObjectId(session_id)},
        {
            '$set': {
                'date': new_date,
                'block': new_block,
                'status': 'pending'
            }
        }
    )
    
    flash('Session rescheduled successfully!', 'success')
    return redirect(request.referrer or url_for('dashboard.dashboard'))


@planner_bp.route('/sessions/<session_id>/note', methods=['POST'])
@login_required
def add_session_note(session_id):
    """Add a note to a session"""
    user_id = session['user_id']
    
    # Get session
    sess = current_app.mongo.db.sessions.find_one({
        '_id': ObjectId(session_id),
        'user_id': ObjectId(user_id)
    })
    
    if not sess:
        return jsonify({'error': 'Session not found'}), 404
    
    notes = request.form.get('notes', '').strip()
    
    # Update session
    current_app.mongo.db.sessions.update_one(
        {'_id': ObjectId(session_id)},
        {'$set': {'notes': notes}}
    )
    
    flash('Note added successfully!', 'success')
    return redirect(request.referrer or url_for('dashboard.dashboard'))
