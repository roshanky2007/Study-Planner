"""
Planner routes: plan generation, timetable view, session actions
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from utils.auth import login_required
from utils.planner import StudyPlanner, get_plan_explanation
from utils.db_helpers import get_subjects_for_user, get_sessions_for_date, get_topic_statistics, get_overall_progress, get_study_streak

planner_bp = Blueprint('planner', __name__)


def _json_session_response(user_id, session_id, status):
    updated_session = current_app.mongo.db.sessions.find_one({'_id': ObjectId(session_id)})
    progress = get_overall_progress(current_app.mongo, user_id)
    streak = get_study_streak(current_app.mongo, user_id)
    today_sessions = get_sessions_for_date(current_app.mongo, user_id, datetime.now())
    return jsonify({
        'success': True,
        'status': status,
        'session_id': session_id,
        'progress_percentage': progress['completion_percentage'],
        'streak': streak,
        'today_count': len(today_sessions),
        'today_minutes': sum(sess.get('planned_minutes', 0) for sess in today_sessions),
        'session': {
            'status': updated_session.get('status') if updated_session else status
        }
    })


@planner_bp.route('/planner')
@login_required
def planner():
    """Planner overview and generation page"""
    user_id = session['user_id']

    latest_plan = current_app.mongo.db.plans.find_one(
        {'user_id': ObjectId(user_id)},
        sort=[('created_at', -1)]
    )

    subjects = get_subjects_for_user(current_app.mongo, user_id)

    default_end_date = None
    if subjects:
        exam_dates = [s['exam_date'] for s in subjects if s.get('exam_date')]
        if exam_dates:
            default_end_date = max(exam_dates)

    if not default_end_date:
        default_end_date = datetime.now() + timedelta(days=30)

    explanations = get_plan_explanation(current_app.mongo, user_id)
    subject_stats = [get_topic_statistics(current_app.mongo, user_id, str(subject['_id'])) for subject in subjects]
    total_topics = sum(item['total_topics'] for item in subject_stats)
    total_minutes = sum(item['total_minutes'] for item in subject_stats)
    available_days = max(1, (default_end_date.date() - datetime.now().date()).days + 1)

    return render_template(
        'planner/generate.html',
        latest_plan=latest_plan,
        subjects=subjects,
        default_end_date=default_end_date,
        explanations=explanations,
        total_topics=total_topics,
        total_minutes=total_minutes,
        available_days=available_days,
    )


@planner_bp.route('/planner/generate', methods=['POST'])
@login_required
def generate_plan():
    """Generate a new study plan"""
    user_id = session['user_id']

    daily_study_minutes = request.form.get('daily_study_minutes', '240')
    start_date_str = request.form.get('start_date', '')
    end_date_str = request.form.get('end_date', '')
    max_sessions_per_day = request.form.get('max_sessions_per_day', '4')
    revision_buffer_days = request.form.get('revision_buffer_days', '2')
    blocks = request.form.getlist('blocks')

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

    valid_blocks = ['Morning', 'Afternoon', 'Evening']
    blocks = [block for block in blocks if block in valid_blocks]
    if not blocks:
        errors['blocks'] = 'Choose at least one study block.'

    if errors:
        for error in errors.values():
            flash(error, 'error')
        return redirect(url_for('planner.planner'))

    planner_instance = StudyPlanner(current_app.mongo, user_id)
    config = {
        'daily_study_minutes': daily_study_minutes,
        'start_date': start_date,
        'end_date': end_date,
        'blocks': blocks,
        'max_sessions_per_day': max_sessions_per_day,
        'revision_buffer_days': revision_buffer_days
    }

    result = planner_instance.generate_plan(config)
    if 'error' in result:
        flash(result['error'], 'error')
        return redirect(url_for('planner.planner'))

    flash(
        f'Study plan generated successfully! {result["total_sessions"]} sessions across '
        f'{result["study_days"]} study days were created.',
        'success'
    )
    return redirect(url_for('planner.timetable'))


@planner_bp.route('/timetable')
@login_required
def timetable():
    """Weekly timetable view"""
    user_id = session['user_id']
    week_offset = request.args.get('week', 0, type=int)
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]

    week_data = []
    for date in week_dates:
        day_sessions = get_sessions_for_date(current_app.mongo, user_id, date)
        sessions_by_block = {'Morning': [], 'Afternoon': [], 'Evening': []}

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

    view_mode = request.args.get('view', 'grid')
    return render_template(
        'planner/timetable.html',
        week_data=week_data,
        week_offset=week_offset,
        view_mode=view_mode,
        start_of_week=start_of_week
    )


@planner_bp.route('/sessions/<session_id>/complete', methods=['POST'])
@login_required
def complete_session(session_id):
    """Mark a session as completed"""
    user_id = session['user_id']
    sess = current_app.mongo.db.sessions.find_one({
        '_id': ObjectId(session_id),
        'user_id': ObjectId(user_id)
    })

    if not sess:
        return jsonify({'error': 'Session not found'}), 404

    actual_minutes = request.form.get('actual_minutes', sess['planned_minutes'])
    try:
        actual_minutes = int(actual_minutes)
    except ValueError:
        actual_minutes = sess['planned_minutes']

    notes = request.form.get('notes', '').strip()

    current_app.mongo.db.sessions.update_one(
        {'_id': ObjectId(session_id)},
        {'$set': {
            'status': 'completed',
            'actual_minutes': actual_minutes,
            'notes': notes,
            'completed_at': datetime.now()
        }}
    )

    current_app.mongo.db.study_logs.insert_one({
        'user_id': ObjectId(user_id),
        'session_id': ObjectId(session_id),
        'subject_id': sess['subject_id'],
        'topic_id': sess['topic_id'],
        'actual_minutes': actual_minutes,
        'notes': notes,
        'logged_at': datetime.now()
    })

    remaining_topic_sessions = current_app.mongo.db.sessions.count_documents({
        'user_id': ObjectId(user_id),
        'topic_id': sess['topic_id'],
        'status': {'$in': ['pending', 'skipped']}
    })
    if remaining_topic_sessions == 0:
        current_app.mongo.db.topics.update_one({'_id': sess['topic_id']}, {'$set': {'status': 'completed'}})

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return _json_session_response(user_id, session_id, 'completed')

    flash('Session marked as completed!', 'success')
    return redirect(request.referrer or url_for('dashboard.dashboard'))


@planner_bp.route('/sessions/<session_id>/skip', methods=['POST'])
@login_required
def skip_session(session_id):
    """Skip a session (moves to backlog)"""
    user_id = session['user_id']
    sess = current_app.mongo.db.sessions.find_one({
        '_id': ObjectId(session_id),
        'user_id': ObjectId(user_id)
    })

    if not sess:
        return jsonify({'error': 'Session not found'}), 404

    current_app.mongo.db.sessions.update_one({'_id': ObjectId(session_id)}, {'$set': {'status': 'skipped'}})
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return _json_session_response(user_id, session_id, 'skipped')
    flash('Session skipped. It has been added to your backlog.', 'info')
    return redirect(request.referrer or url_for('dashboard.dashboard'))


@planner_bp.route('/sessions/<session_id>/reschedule', methods=['POST'])
@login_required
def reschedule_session(session_id):
    """Reschedule a session to a different date/block"""
    user_id = session['user_id']
    sess = current_app.mongo.db.sessions.find_one({
        '_id': ObjectId(session_id),
        'user_id': ObjectId(user_id)
    })

    if not sess:
        flash('Session not found.', 'error')
        return redirect(url_for('dashboard.dashboard'))

    new_date_str = request.form.get('new_date', '')
    new_block = request.form.get('new_block', 'Morning')

    try:
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d')
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(request.referrer or url_for('dashboard.dashboard'))

    current_app.mongo.db.sessions.update_one(
        {'_id': ObjectId(session_id)},
        {'$set': {'date': new_date, 'block': new_block, 'status': 'pending'}}
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return _json_session_response(user_id, session_id, 'pending')

    flash('Session rescheduled successfully!', 'success')
    return redirect(request.referrer or url_for('dashboard.dashboard'))


@planner_bp.route('/sessions/<session_id>/note', methods=['POST'])
@login_required
def add_session_note(session_id):
    """Add a note to a session"""
    user_id = session['user_id']
    sess = current_app.mongo.db.sessions.find_one({
        '_id': ObjectId(session_id),
        'user_id': ObjectId(user_id)
    })

    if not sess:
        return jsonify({'error': 'Session not found'}), 404

    notes = request.form.get('notes', '').strip()
    current_app.mongo.db.sessions.update_one({'_id': ObjectId(session_id)}, {'$set': {'notes': notes}})
    flash('Note added successfully!', 'success')
    return redirect(request.referrer or url_for('dashboard.dashboard'))
