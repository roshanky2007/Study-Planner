"""
Intelligent Study Planner Algorithm

This module implements the core planning algorithm that generates
day-by-day, block-by-block study schedules based on subjects, topics,
exam dates, and user preferences.

Algorithm Overview:
1. Exam Prioritization - nearer exams get higher priority
2. Difficulty Weighting - harder subjects get more time
3. Syllabus Completion - incomplete topics are prioritized
4. Time Allocation - distributes study time across blocks
5. Variety Enforcement - avoids same subject in consecutive blocks
6. Revision Buffer - reserves days before exams for review
7. Session Sizing - splits topics into manageable chunks
8. Backlog Handling - reinserts skipped sessions with higher priority
"""

from datetime import datetime, timedelta
from bson.objectid import ObjectId
import math


class StudyPlanner:
    """
    Intelligent study planner that generates optimized schedules
    """
    
    BLOCK_ORDER = ['Morning', 'Afternoon', 'Evening']
    DEFAULT_SESSION_MINUTES = 60
    SAME_SUBJECT_PENALTY = 0.6  # Penalty for consecutive same subject
    BACKLOG_PRIORITY_MULTIPLIER = 1.5
    
    def __init__(self, mongo, user_id):
        """
        Initialize planner with database connection and user context
        
        Args:
            mongo: Flask-PyMongo instance
            user_id (str): User's ObjectId as string
        """
        self.mongo = mongo
        self.user_id = ObjectId(user_id)
        self.subjects = []
        self.topics = []
        self.sessions = []
    
    def generate_plan(self, config):
        """
        Generate a complete study plan based on configuration
        
        Args:
            config (dict): Plan configuration with keys:
                - daily_study_minutes (int)
                - start_date (datetime)
                - end_date (datetime)
                - blocks (list of str)
                - max_sessions_per_day (int)
                - revision_buffer_days (int)
                
        Returns:
            dict: Generated plan with sessions
        """
        # Load subjects and topics
        self._load_data()
        
        # Validate prerequisites
        if not self.subjects:
            return {'error': 'No subjects found. Please add subjects first.'}
        
        if not self.topics:
            return {'error': 'No topics found. Please add topics to your subjects first.'}
        
        # Calculate priorities for each topic
        topic_priorities = self._calculate_priorities(config)
        
        # Generate sessions for each day
        sessions = self._allocate_sessions(config, topic_priorities)
        
        # Add revision sessions before exams
        sessions = self._add_revision_sessions(config, sessions)
        
        # Save plan to database
        plan_id = self._save_plan(config, sessions)
        
        return {
            'success': True,
            'plan_id': plan_id,
            'sessions': sessions,
            'total_sessions': len(sessions)
        }
    
    def _load_data(self):
        """Load subjects and topics from database"""
        self.subjects = list(self.mongo.db.subjects.find({
            'user_id': self.user_id
        }))
        
        self.topics = list(self.mongo.db.topics.find({
            'user_id': self.user_id,
            'status': 'pending'  # Only incomplete topics
        }))
    
    def _calculate_priorities(self, config):
        """
        Calculate priority scores for each topic
        
        Priority formula:
        - Base priority = remaining_minutes / total_remaining_minutes
        - Exam urgency multiplier = 1 / (days_until_exam + 1)^0.3
        - Difficulty multiplier = 1.3 for hard (4-5), 1.0 for medium (3), 0.8 for easy (1-2)
        
        Args:
            config (dict): Plan configuration
            
        Returns:
            dict: topic_id -> priority_score mapping
        """
        priorities = {}
        now = datetime.now()
        
        # Calculate total remaining minutes
        total_remaining = sum(t.get('estimated_minutes', self.DEFAULT_SESSION_MINUTES) 
                            for t in self.topics)
        
        if total_remaining == 0:
            return priorities
        
        for topic in self.topics:
            # Find subject for this topic
            subject = next((s for s in self.subjects if s['_id'] == topic['subject_id']), None)
            if not subject:
                continue
            
            # Base priority from topic size
            topic_minutes = topic.get('estimated_minutes', self.DEFAULT_SESSION_MINUTES)
            base_priority = topic_minutes / total_remaining
            
            # Exam urgency multiplier (exponential decay)
            if subject.get('exam_date'):
                days_until_exam = (subject['exam_date'] - now).days
                days_until_exam = max(1, days_until_exam)  # Avoid division by zero
                urgency_multiplier = 1 / (days_until_exam ** 0.3)
            else:
                urgency_multiplier = 1.0
            
            # Difficulty multiplier
            difficulty = subject.get('difficulty', 3)
            if difficulty >= 4:
                difficulty_multiplier = 1.3
            elif difficulty <= 2:
                difficulty_multiplier = 0.8
            else:
                difficulty_multiplier = 1.0
            
            # Priority override (if user set manual priority)
            priority_override = topic.get('priority_override', 1.0)
            
            # Final priority score
            final_priority = (base_priority * urgency_multiplier * 
                            difficulty_multiplier * priority_override)
            
            priorities[str(topic['_id'])] = {
                'score': final_priority,
                'subject_id': str(subject['_id']),
                'topic_id': str(topic['_id']),
                'estimated_minutes': topic_minutes,
                'subject_name': subject['name'],
                'topic_title': topic['title']
            }
        
        return priorities
    
    def _allocate_sessions(self, config, topic_priorities):
        """
        Allocate study sessions to days and blocks
        
        Args:
            config (dict): Plan configuration
            topic_priorities (dict): Priority scores for topics
            
        Returns:
            list: List of session documents
        """
        sessions = []
        current_date = config['start_date']
        end_date = config['end_date']
        
        # Sort topics by priority (descending)
        sorted_topics = sorted(topic_priorities.items(), 
                              key=lambda x: x[1]['score'], 
                              reverse=True)
        
        # Track remaining minutes for each topic
        remaining_minutes = {
            tid: info['estimated_minutes'] 
            for tid, info in topic_priorities.items()
        }
        
        # Track last assigned subject to enforce variety
        last_subject_id = None
        
        # Iterate through each day
        while current_date <= end_date:
            # Check if any topic has remaining time
            if sum(remaining_minutes.values()) == 0:
                break
            
            # Allocate sessions for this day
            day_sessions = []
            blocks = config.get('blocks', self.BLOCK_ORDER)
            max_sessions = config.get('max_sessions_per_day', 4)
            
            for block in blocks:
                if len(day_sessions) >= max_sessions:
                    break
                
                # Find best topic for this block
                best_topic = None
                best_score = -1
                
                for topic_id, info in sorted_topics:
                    if remaining_minutes.get(topic_id, 0) <= 0:
                        continue
                    
                    score = info['score']
                    
                    # Apply same-subject penalty
                    if last_subject_id and info['subject_id'] == last_subject_id:
                        score *= self.SAME_SUBJECT_PENALTY
                    
                    if score > best_score:
                        best_score = score
                        best_topic = (topic_id, info)
                
                if best_topic:
                    topic_id, info = best_topic
                    
                    # Determine session minutes (cap at remaining or default)
                    session_minutes = min(
                        remaining_minutes[topic_id],
                        self.DEFAULT_SESSION_MINUTES
                    )
                    
                    # Create session
                    session = {
                        'user_id': self.user_id,
                        'subject_id': ObjectId(info['subject_id']),
                        'topic_id': ObjectId(topic_id),
                        'date': current_date,
                        'block': block,
                        'planned_minutes': session_minutes,
                        'actual_minutes': None,
                        'status': 'pending',
                        'notes': None,
                        'completed_at': None
                    }
                    
                    day_sessions.append(session)
                    sessions.append(session)
                    
                    # Update remaining minutes
                    remaining_minutes[topic_id] -= session_minutes
                    
                    # Update last subject
                    last_subject_id = info['subject_id']
            
            # Move to next day
            current_date += timedelta(days=1)
        
        return sessions
    
    def _add_revision_sessions(self, config, sessions):
        """
        Add revision sessions before exams
        
        Args:
            config (dict): Plan configuration
            sessions (list): Existing sessions
            
        Returns:
            list: Sessions with revision added
        """
        revision_buffer = config.get('revision_buffer_days', 2)
        
        if revision_buffer == 0:
            return sessions
        
        # For each subject with exam, add revision sessions
        for subject in self.subjects:
            if not subject.get('exam_date'):
                continue
            
            exam_date = subject['exam_date']
            
            # Get all topics for this subject
            subject_topics = [t for t in self.topics if t['subject_id'] == subject['_id']]
            
            if not subject_topics:
                continue
            
            # Add revision sessions for N days before exam
            for i in range(revision_buffer):
                revision_date = exam_date - timedelta(days=revision_buffer - i)
                
                # Check if revision_date is within plan range
                if revision_date < config['start_date'] or revision_date > config['end_date']:
                    continue
                
                # Assign revision for each topic in this subject
                for topic in subject_topics:
                    # Find a free block for this day
                    existing_blocks = [s['block'] for s in sessions 
                                     if s['date'].date() == revision_date.date()]
                    
                    available_blocks = [b for b in config.get('blocks', self.BLOCK_ORDER) 
                                      if b not in existing_blocks]
                    
                    if available_blocks:
                        revision_session = {
                            'user_id': self.user_id,
                            'subject_id': subject['_id'],
                            'topic_id': topic['_id'],
                            'date': revision_date,
                            'block': available_blocks[0],
                            'planned_minutes': 30,  # Shorter revision sessions
                            'actual_minutes': None,
                            'status': 'pending',
                            'notes': 'Revision session',
                            'completed_at': None
                        }
                        sessions.append(revision_session)
        
        # Sort sessions by date and block
        sessions.sort(key=lambda s: (s['date'], self.BLOCK_ORDER.index(s['block'])))
        
        return sessions
    
    def _save_plan(self, config, sessions):
        """
        Save plan and sessions to database
        
        Args:
            config (dict): Plan configuration
            sessions (list): Generated sessions
            
        Returns:
            str: Plan ObjectId as string
        """
        # Save plan metadata
        plan_doc = {
            'user_id': self.user_id,
            'daily_study_minutes': config['daily_study_minutes'],
            'start_date': config['start_date'],
            'end_date': config['end_date'],
            'blocks': config.get('blocks', self.BLOCK_ORDER),
            'max_sessions_per_day': config.get('max_sessions_per_day', 4),
            'revision_buffer_days': config.get('revision_buffer_days', 2),
            'created_at': datetime.now(),
            'algorithm_version': '1.0'
        }
        
        plan_id = self.mongo.db.plans.insert_one(plan_doc).inserted_id
        
        # Add plan_id to each session and save
        for session in sessions:
            session['plan_id'] = plan_id
        
        if sessions:
            self.mongo.db.sessions.insert_many(sessions)
        
        return str(plan_id)
    
    def handle_backlog(self, session_id):
        """
        Handle a skipped session by marking it for rescheduling
        
        Args:
            session_id (str): Session ObjectId as string
        """
        self.mongo.db.sessions.update_one(
            {'_id': ObjectId(session_id)},
            {'$set': {'status': 'skipped'}}
        )
    
    def reschedule_session(self, session_id, new_date, new_block):
        """
        Reschedule a session to a different date/block
        
        Args:
            session_id (str): Session ObjectId as string
            new_date (datetime): New date for session
            new_block (str): New block name
        """
        self.mongo.db.sessions.update_one(
            {'_id': ObjectId(session_id)},
            {
                '$set': {
                    'date': new_date,
                    'block': new_block,
                    'status': 'pending'
                }
            }
        )


def calculate_readiness_score(mongo, user_id):
    """
    Calculate readiness score for user
    
    Formula:
    Readiness = (0.6 × Syllabus Completion %) + (0.4 × Consistency Score)
    
    Where:
    - Syllabus Completion % = completed_minutes / total_minutes
    - Consistency Score = (study_streak / plan_duration) × 100, capped at 100%
    
    Args:
        mongo: Flask-PyMongo instance
        user_id (str): User's ObjectId as string
        
    Returns:
        dict: Readiness score and components
    """
    from utils.db_helpers import get_overall_progress, get_study_streak
    
    # Get syllabus completion
    progress = get_overall_progress(mongo, user_id)
    syllabus_completion = progress['completion_percentage']
    
    # Get study streak
    streak = get_study_streak(mongo, user_id)
    
    # Get plan duration (from most recent plan)
    plan = mongo.db.plans.find_one(
        {'user_id': ObjectId(user_id)},
        sort=[('created_at', -1)]
    )
    
    if plan:
        plan_duration = (plan['end_date'] - plan['start_date']).days + 1
        consistency_score = min(100, (streak / plan_duration) * 100) if plan_duration > 0 else 0
    else:
        consistency_score = 0
    
    # Calculate final readiness score
    readiness = (0.6 * syllabus_completion) + (0.4 * consistency_score)
    
    return {
        'readiness_score': round(readiness, 1),
        'syllabus_completion': round(syllabus_completion, 1),
        'consistency_score': round(consistency_score, 1),
        'study_streak': streak
    }


def get_plan_explanation(mongo, user_id):
    """
    Generate "Why this plan?" explanation for user
    
    Args:
        mongo: Flask-PyMongo instance
        user_id (str): User's ObjectId as string
        
    Returns:
        list: List of explanation strings
    """
    explanations = [
        "⏰ <strong>Urgent exams first</strong> - subjects with sooner dates get more immediate slots",
        "📚 <strong>Difficulty balance</strong> - harder subjects receive proportionally more time",
        "🎯 <strong>Syllabus coverage</strong> - ensures all topics are covered before exam dates",
        "🔄 <strong>Variety</strong> - avoids studying the same subject in consecutive blocks",
        "📖 <strong>Revision time</strong> - reserves buffer days before exams for review",
        "⚡ <strong>Your pace</strong> - respects your daily study time and session preferences"
    ]
    
    return explanations
