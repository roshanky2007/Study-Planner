"""
Dashboard routes: main dashboard showing today's sessions and overview
"""

from collections import OrderedDict
from flask import Blueprint, render_template, current_app, session
from datetime import datetime, timedelta
from utils.auth import login_required
from utils.db_helpers import (
    get_sessions_for_date, get_backlog_sessions,
    get_upcoming_exams, get_study_streak, get_overall_progress, get_subjects_for_user
)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - today-first view"""
    user_id = session['user_id']
    today = datetime.now()
    current_hour = today.hour
    current_block = 'Morning' if current_hour < 12 else 'Afternoon' if current_hour < 18 else 'Evening'

    today_sessions = get_sessions_for_date(current_app.mongo, user_id, today)
    backlog = get_backlog_sessions(current_app.mongo, user_id)
    upcoming_exams = get_upcoming_exams(current_app.mongo, user_id, limit=3)
    streak = get_study_streak(current_app.mongo, user_id)
    progress = get_overall_progress(current_app.mongo, user_id)
    subjects = get_subjects_for_user(current_app.mongo, user_id)
    exam_pressure = min([s.get('days_left', 9999) for s in subjects], default=None)

    sessions_by_block = {block: [] for block in ['Morning', 'Afternoon', 'Evening']}
    timeline_blocks = []
    next_session = next((s for s in today_sessions if s.get('status') == 'pending'), today_sessions[0] if today_sessions else None)
    today_minutes = sum(sess.get('planned_minutes', 0) for sess in today_sessions)

    for sess in today_sessions:
        block = sess.get('block', 'Morning')
        if block in sessions_by_block:
            sessions_by_block[block].append(sess)

    for block in ['Morning', 'Afternoon', 'Evening']:
        block_sessions = sessions_by_block[block]
        subject_groups = OrderedDict()
        for sess in block_sessions:
            subject = sess.get('subject') or {}
            subject_id = str(subject.get('_id', sess.get('subject_id')))
            if subject_id not in subject_groups:
                difficulty = subject.get('difficulty', 3)
                difficulty_label = 'Hard' if difficulty >= 4 else 'Medium' if difficulty == 3 else 'Easy'
                subject_groups[subject_id] = {
                    'subject': subject,
                    'sessions': [],
                    'reason': f'Exam in {max(0, subject.get("days_left", 0))} days + {difficulty_label} + Topic pending'
                }
            subject_groups[subject_id]['sessions'].append(sess)

        timeline_blocks.append({
            'name': block,
            'is_current': block == current_block,
            'subject_groups': list(subject_groups.values()),
            'total_sessions': len(block_sessions)
        })

    week_sessions = []
    for i in range(7):
        date = today + timedelta(days=i)
        day_sessions = get_sessions_for_date(current_app.mongo, user_id, date)
        completed_count = sum(1 for s in day_sessions if s['status'] == 'completed')
        total_count = len(day_sessions)
        completion_pct = round((completed_count / total_count) * 100) if total_count else 0
        week_sessions.append({
            'date': date,
            'day_name': date.strftime('%a'),
            'day_number': date.day,
            'is_today': date.date() == today.date(),
            'completed': completed_count,
            'total': total_count,
            'completion_pct': completion_pct,
        })

    return render_template(
        'dashboard.html',
        today=today,
        today_sessions=today_sessions,
        sessions_by_block=sessions_by_block,
        timeline_blocks=timeline_blocks,
        next_session=next_session,
        backlog=backlog,
        upcoming_exams=upcoming_exams,
        streak=streak,
        progress=progress,
        week_sessions=week_sessions,
        subjects=subjects,
        exam_pressure=exam_pressure,
        today_minutes=today_minutes,
        current_block=current_block,
    )
