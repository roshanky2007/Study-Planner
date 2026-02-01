"""
Dashboard routes: main dashboard showing today's sessions and overview
"""

from flask import Blueprint, render_template, current_app, session
from datetime import datetime, timedelta
from utils.auth import login_required
from utils.db_helpers import (
    get_sessions_for_date, get_backlog_sessions, 
    get_upcoming_exams, get_study_streak, get_overall_progress
)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - today-first view"""
    user_id = session['user_id']
    today = datetime.now()
    
    # Get today's sessions
    today_sessions = get_sessions_for_date(current_app.mongo, user_id, today)
    
    # Group sessions by block
    sessions_by_block = {}
    for sess in today_sessions:
        block = sess.get('block', 'Unscheduled')
        if block not in sessions_by_block:
            sessions_by_block[block] = []
        sessions_by_block[block].append(sess)
    
    # Get backlog (skipped sessions)
    backlog = get_backlog_sessions(current_app.mongo, user_id)
    
    # Get upcoming exams
    upcoming_exams = get_upcoming_exams(current_app.mongo, user_id, limit=3)
    
    # Get study streak
    streak = get_study_streak(current_app.mongo, user_id)
    
    # Get overall progress
    progress = get_overall_progress(current_app.mongo, user_id)
    
    # Get this week's sessions (7-day strip)
    week_sessions = []
    for i in range(7):
        date = today + timedelta(days=i)
        day_sessions = get_sessions_for_date(current_app.mongo, user_id, date)
        
        completed_count = sum(1 for s in day_sessions if s['status'] == 'completed')
        total_count = len(day_sessions)
        
        week_sessions.append({
            'date': date,
            'day_name': date.strftime('%a'),
            'day_number': date.day,
            'is_today': date.date() == today.date(),
            'completed': completed_count,
            'total': total_count
        })
    
    return render_template('dashboard.html',
                         today=today,
                         today_sessions=today_sessions,
                         sessions_by_block=sessions_by_block,
                         backlog=backlog,
                         upcoming_exams=upcoming_exams,
                         streak=streak,
                         progress=progress,
                         week_sessions=week_sessions)
