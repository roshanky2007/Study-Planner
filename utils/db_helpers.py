"""
Database query helpers and data retrieval utilities
"""

from datetime import datetime, timedelta
from bson.objectid import ObjectId


def get_subjects_for_user(mongo, user_id):
    """
    Get all subjects for a user, sorted by exam date
    
    Args:
        mongo: Flask-PyMongo instance
        user_id (str): User's ObjectId as string
        
    Returns:
        list: List of subject documents with days_left calculated
    """
    subjects = list(mongo.db.subjects.find(
        {'user_id': ObjectId(user_id)}
    ).sort('exam_date', 1))
    
    # Calculate days left for each subject
    now = datetime.now()
    for subject in subjects:
        if subject.get('exam_date'):
            days_left = (subject['exam_date'] - now).days
            subject['days_left'] = days_left
        else:
            subject['days_left'] = None
    
    return subjects


def get_topics_for_subject(mongo, user_id, subject_id):
    """
    Get all topics for a specific subject
    
    Args:
        mongo: Flask-PyMongo instance
        user_id (str): User's ObjectId as string
        subject_id (str): Subject's ObjectId as string
        
    Returns:
        list: List of topic documents
    """
    topics = list(mongo.db.topics.find({
        'user_id': ObjectId(user_id),
        'subject_id': ObjectId(subject_id)
    }).sort('created_at', 1))
    
    return topics


def get_topic_statistics(mongo, user_id, subject_id):
    """
    Calculate topic completion statistics for a subject
    
    Args:
        mongo: Flask-PyMongo instance
        user_id (str): User's ObjectId as string
        subject_id (str): Subject's ObjectId as string
        
    Returns:
        dict: Statistics including total topics, completed topics, total minutes, completed minutes
    """
    topics = get_topics_for_subject(mongo, user_id, subject_id)
    
    total_topics = len(topics)
    completed_topics = sum(1 for t in topics if t.get('status') == 'completed')
    total_minutes = sum(t.get('estimated_minutes', 0) for t in topics)
    completed_minutes = sum(t.get('estimated_minutes', 0) for t in topics if t.get('status') == 'completed')
    
    completion_percentage = (completed_minutes / total_minutes * 100) if total_minutes > 0 else 0
    
    return {
        'total_topics': total_topics,
        'completed_topics': completed_topics,
        'total_minutes': total_minutes,
        'completed_minutes': completed_minutes,
        'completion_percentage': round(completion_percentage, 1)
    }


def get_sessions_for_date(mongo, user_id, date):
    """
    Get all sessions for a specific date
    
    Args:
        mongo: Flask-PyMongo instance
        user_id (str): User's ObjectId as string
        date (datetime): Target date
        
    Returns:
        list: List of session documents with subject and topic details
    """
    # Query sessions for the date
    start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0)
    end_of_day = datetime(date.year, date.month, date.day, 23, 59, 59)
    
    sessions = list(mongo.db.sessions.find({
        'user_id': ObjectId(user_id),
        'date': {'$gte': start_of_day, '$lte': end_of_day}
    }).sort('block', 1))
    
    # Enrich sessions with subject and topic details
    for session in sessions:
        subject = mongo.db.subjects.find_one({'_id': session['subject_id']})
        topic = mongo.db.topics.find_one({'_id': session['topic_id']})
        
        session['subject'] = subject
        session['topic'] = topic
    
    return sessions


def get_backlog_sessions(mongo, user_id):
    """
    Get all skipped sessions (backlog) for a user
    
    Args:
        mongo: Flask-PyMongo instance
        user_id (str): User's ObjectId as string
        
    Returns:
        list: List of skipped session documents
    """
    sessions = list(mongo.db.sessions.find({
        'user_id': ObjectId(user_id),
        'status': 'skipped'
    }).sort('date', 1))
    
    # Enrich with subject and topic details
    for session in sessions:
        subject = mongo.db.subjects.find_one({'_id': session['subject_id']})
        topic = mongo.db.topics.find_one({'_id': session['topic_id']})
        
        session['subject'] = subject
        session['topic'] = topic
    
    return sessions


def get_study_streak(mongo, user_id):
    """
    Calculate the current study streak (consecutive days with completed sessions)
    
    Args:
        mongo: Flask-PyMongo instance
        user_id (str): User's ObjectId as string
        
    Returns:
        int: Number of consecutive days with study activity
    """
    # Get all completed sessions sorted by date descending
    sessions = list(mongo.db.sessions.find({
        'user_id': ObjectId(user_id),
        'status': 'completed'
    }).sort('completed_at', -1))
    
    if not sessions:
        return 0
    
    # Get unique dates with completed sessions
    completed_dates = set()
    for session in sessions:
        if session.get('completed_at'):
            date = session['completed_at'].date()
            completed_dates.add(date)
    
    # Sort dates descending
    sorted_dates = sorted(completed_dates, reverse=True)
    
    if not sorted_dates:
        return 0
    
    # Check if today or yesterday has activity
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    if sorted_dates[0] not in [today, yesterday]:
        return 0  # Streak broken
    
    # Count consecutive days
    streak = 1
    current_date = sorted_dates[0]
    
    for i in range(1, len(sorted_dates)):
        expected_date = current_date - timedelta(days=1)
        if sorted_dates[i] == expected_date:
            streak += 1
            current_date = sorted_dates[i]
        else:
            break
    
    return streak


def get_overall_progress(mongo, user_id):
    """
    Calculate overall progress across all subjects
    
    Args:
        mongo: Flask-PyMongo instance
        user_id (str): User's ObjectId as string
        
    Returns:
        dict: Overall statistics including completion percentage, total topics, etc.
    """
    subjects = get_subjects_for_user(mongo, user_id)
    
    total_topics = 0
    completed_topics = 0
    total_minutes = 0
    completed_minutes = 0
    
    for subject in subjects:
        stats = get_topic_statistics(mongo, user_id, str(subject['_id']))
        total_topics += stats['total_topics']
        completed_topics += stats['completed_topics']
        total_minutes += stats['total_minutes']
        completed_minutes += stats['completed_minutes']
    
    completion_percentage = (completed_minutes / total_minutes * 100) if total_minutes > 0 else 0
    
    return {
        'total_subjects': len(subjects),
        'total_topics': total_topics,
        'completed_topics': completed_topics,
        'total_minutes': total_minutes,
        'completed_minutes': completed_minutes,
        'completion_percentage': round(completion_percentage, 1)
    }


def get_upcoming_exams(mongo, user_id, limit=5):
    """
    Get upcoming exams sorted by date
    
    Args:
        mongo: Flask-PyMongo instance
        user_id (str): User's ObjectId as string
        limit (int): Maximum number of exams to return
        
    Returns:
        list: List of subjects with upcoming exams
    """
    now = datetime.now()
    subjects = list(mongo.db.subjects.find({
        'user_id': ObjectId(user_id),
        'exam_date': {'$gte': now}
    }).sort('exam_date', 1).limit(limit))
    
    # Calculate days left
    for subject in subjects:
        days_left = (subject['exam_date'] - now).days
        subject['days_left'] = days_left
    
    return subjects
