"""
Progress tracking routes: readiness score, statistics, completion tracking
"""

from flask import Blueprint, render_template, current_app, session
from utils.auth import login_required
from utils.db_helpers import (
    get_subjects_for_user, get_topic_statistics, 
    get_study_streak, get_overall_progress
)
from utils.planner import calculate_readiness_score

progress_bp = Blueprint('progress', __name__)


@progress_bp.route('/progress')
@login_required
def progress():
    """Progress tracking and readiness score page"""
    user_id = session['user_id']
    
    # Get overall progress
    overall = get_overall_progress(current_app.mongo, user_id)
    
    # Get study streak
    streak = get_study_streak(current_app.mongo, user_id)
    
    # Get readiness score
    readiness = calculate_readiness_score(current_app.mongo, user_id)
    
    # Get per-subject progress
    subjects = get_subjects_for_user(current_app.mongo, user_id)
    
    subject_progress = []
    for subject in subjects:
        stats = get_topic_statistics(current_app.mongo, user_id, str(subject['_id']))
        
        subject_progress.append({
            'subject': subject,
            'stats': stats
        })
    
    # Sort by completion percentage (ascending, so incomplete subjects appear first)
    subject_progress.sort(key=lambda x: x['stats']['completion_percentage'])
    
    # Determine readiness status
    readiness_status = 'Not Ready'
    readiness_class = 'text-red-600'
    
    if readiness['readiness_score'] >= 80:
        readiness_status = 'Exam Ready'
        readiness_class = 'text-green-600'
    elif readiness['readiness_score'] >= 60:
        readiness_status = 'Making Progress'
        readiness_class = 'text-yellow-600'
    elif readiness['readiness_score'] >= 40:
        readiness_status = 'Needs Work'
        readiness_class = 'text-orange-600'
    
    return render_template('progress.html',
                         overall=overall,
                         streak=streak,
                         readiness=readiness,
                         readiness_status=readiness_status,
                         readiness_class=readiness_class,
                         subject_progress=subject_progress)
