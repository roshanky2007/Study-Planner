from datetime import datetime, timedelta
from bson.objectid import ObjectId
import math


class StudyPlanner:
    """
    Intelligent study planner that generates optimized schedules
    """

    BLOCK_ORDER = ['Morning', 'Afternoon', 'Evening']
    DEFAULT_SESSION_MINUTES = 60
    MIN_SESSION_MINUTES = 30
    MAX_SESSION_MINUTES = 120
    SAME_SUBJECT_PENALTY = 0.6
    BACKLOG_PRIORITY_MULTIPLIER = 1.5

    def __init__(self, mongo, user_id):
        self.mongo = mongo
        self.user_id = ObjectId(user_id)
        self.subjects = []
        self.topics = []
        self.sessions = []

    def generate_plan(self, config):
        self._load_data()

        if not self.subjects:
            return {'error': 'No subjects found. Please add subjects first.'}
        if not self.topics:
            return {'error': 'No topics found. Please add topics to your subjects first.'}

        topic_priorities = self._calculate_priorities(config)
        sessions = self._allocate_sessions(config, topic_priorities)
        sessions = self._add_revision_sessions(config, sessions)
        plan_id = self._save_plan(config, sessions)

        study_days = len({session['date'].date() for session in sessions})
        total_minutes = sum(session['planned_minutes'] for session in sessions)

        return {
            'success': True,
            'plan_id': plan_id,
            'sessions': sessions,
            'total_sessions': len(sessions),
            'study_days': study_days,
            'total_minutes': total_minutes,
        }

    def _load_data(self):
        self.subjects = list(self.mongo.db.subjects.find({'user_id': self.user_id}))
        self.topics = list(self.mongo.db.topics.find({'user_id': self.user_id, 'status': 'pending'}))

    def _calculate_priorities(self, config):
        priorities = {}
        now = datetime.now()
        total_remaining = sum(t.get('estimated_minutes', self.DEFAULT_SESSION_MINUTES) for t in self.topics)

        if total_remaining == 0:
            return priorities

        for topic in self.topics:
            subject = next((s for s in self.subjects if s['_id'] == topic['subject_id']), None)
            if not subject:
                continue

            topic_minutes = topic.get('estimated_minutes', self.DEFAULT_SESSION_MINUTES)
            base_priority = topic_minutes / total_remaining

            days_until_exam = max(1, (subject['exam_date'] - now).days) if subject.get('exam_date') else 30
            difficulty = subject.get('difficulty', 3)
            priority_flag = 2 if topic.get('priority_override', 1.0) > 1 else 0
            urgency_bonus = max(0, 30 - days_until_exam) / 5
            size_bonus = topic_minutes / 60
            final_priority = (difficulty * 2) + size_bonus + urgency_bonus + priority_flag + base_priority

            priorities[str(topic['_id'])] = {
                'score': final_priority,
                'subject_id': str(subject['_id']),
                'topic_id': str(topic['_id']),
                'estimated_minutes': topic_minutes,
                'subject_name': subject['name'],
                'topic_title': topic['title'],
            }

        return priorities

    def _allocate_sessions(self, config, topic_priorities):
        sessions = []
        current_date = config['start_date']
        end_date = config['end_date']
        blocks = config.get('blocks', self.BLOCK_ORDER)
        max_sessions = max(1, config.get('max_sessions_per_day', 4))
        daily_target = max(self.MIN_SESSION_MINUTES, config.get('daily_study_minutes', 240))
        session_length = max(
            self.MIN_SESSION_MINUTES,
            min(self.MAX_SESSION_MINUTES, math.ceil(daily_target / max_sessions)),
        )

        sorted_topics = sorted(topic_priorities.items(), key=lambda x: x[1]['score'], reverse=True)
        remaining_minutes = {tid: info['estimated_minutes'] for tid, info in topic_priorities.items()}
        last_subject_id = None

        while current_date <= end_date:
            if sum(remaining_minutes.values()) == 0:
                break

            day_minutes = 0
            day_sessions = []
            subjects_per_block = {block: set() for block in blocks}

            for session_index in range(max_sessions):
                if day_minutes >= daily_target:
                    break

                best_topic = None
                best_score = -1
                block = blocks[session_index % len(blocks)]
                for topic_id, info in sorted_topics:
                    if remaining_minutes.get(topic_id, 0) <= 0:
                        continue
                    if info['subject_id'] in subjects_per_block[block]:
                        continue

                    score = info['score']
                    if last_subject_id and info['subject_id'] == last_subject_id:
                        score *= self.SAME_SUBJECT_PENALTY

                    if score > best_score:
                        best_score = score
                        best_topic = (topic_id, info)

                if not best_topic:
                    break

                topic_id, info = best_topic
                minutes_left_today = daily_target - day_minutes
                session_minutes = min(
                    remaining_minutes[topic_id],
                    session_length,
                    minutes_left_today,
                )

                if session_minutes < self.MIN_SESSION_MINUTES and remaining_minutes[topic_id] > self.MIN_SESSION_MINUTES:
                    break

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
                    'completed_at': None,
                }
                day_sessions.append(session)
                sessions.append(session)
                day_minutes += session_minutes
                remaining_minutes[topic_id] -= session_minutes
                last_subject_id = info['subject_id']
                subjects_per_block[block].add(info['subject_id'])

            current_date += timedelta(days=1)

        return sessions

    def _add_revision_sessions(self, config, sessions):
        revision_buffer = config.get('revision_buffer_days', 2)
        if revision_buffer == 0:
            return sessions

        for subject in self.subjects:
            if not subject.get('exam_date'):
                continue

            exam_date = subject['exam_date']
            subject_topics = [t for t in self.topics if t['subject_id'] == subject['_id']]
            if not subject_topics:
                continue

            for i in range(revision_buffer):
                revision_date = exam_date - timedelta(days=revision_buffer - i)
                if revision_date < config['start_date'] or revision_date > config['end_date']:
                    continue

                existing_day_sessions = [s for s in sessions if s['date'].date() == revision_date.date()]
                if len(existing_day_sessions) >= config.get('max_sessions_per_day', 4):
                    continue

                existing_blocks = [s['block'] for s in existing_day_sessions]
                available_blocks = [b for b in config.get('blocks', self.BLOCK_ORDER) if existing_blocks.count(b) < 2]

                for topic in subject_topics[: max(1, len(available_blocks))]:
                    if not available_blocks:
                        break
                    revision_session = {
                        'user_id': self.user_id,
                        'subject_id': subject['_id'],
                        'topic_id': topic['_id'],
                        'date': revision_date,
                        'block': available_blocks.pop(0),
                        'planned_minutes': 30,
                        'actual_minutes': None,
                        'status': 'pending',
                        'notes': 'Revision session',
                        'completed_at': None,
                    }
                    sessions.append(revision_session)

        sessions.sort(key=lambda s: (s['date'], self.BLOCK_ORDER.index(s['block'])))
        return sessions

    def _save_plan(self, config, sessions):
        self.mongo.db.sessions.delete_many({
            'user_id': self.user_id,
            'status': {'$in': ['pending', 'skipped']},
            'completed_at': None,
        })

        plan_doc = {
            'user_id': self.user_id,
            'daily_study_minutes': config['daily_study_minutes'],
            'start_date': config['start_date'],
            'end_date': config['end_date'],
            'blocks': config.get('blocks', self.BLOCK_ORDER),
            'max_sessions_per_day': config.get('max_sessions_per_day', 4),
            'revision_buffer_days': config.get('revision_buffer_days', 2),
            'created_at': datetime.now(),
            'algorithm_version': '2.0',
        }
        plan_id = self.mongo.db.plans.insert_one(plan_doc).inserted_id
        for session in sessions:
            session['plan_id'] = plan_id
        if sessions:
            self.mongo.db.sessions.insert_many(sessions)
        return str(plan_id)

    def handle_backlog(self, session_id):
        self.mongo.db.sessions.update_one({'_id': ObjectId(session_id)}, {'$set': {'status': 'skipped'}})

    def reschedule_session(self, session_id, new_date, new_block):
        self.mongo.db.sessions.update_one(
            {'_id': ObjectId(session_id)},
            {'$set': {'date': new_date, 'block': new_block, 'status': 'pending'}},
        )


def calculate_readiness_score(mongo, user_id):
    from utils.db_helpers import get_overall_progress, get_study_streak

    progress = get_overall_progress(mongo, user_id)
    syllabus_completion = progress['completion_percentage']
    streak = get_study_streak(mongo, user_id)
    plan = mongo.db.plans.find_one({'user_id': ObjectId(user_id)}, sort=[('created_at', -1)])

    if plan:
        plan_duration = (plan['end_date'] - plan['start_date']).days + 1
        consistency_score = min(100, (streak / plan_duration) * 100) if plan_duration > 0 else 0
    else:
        consistency_score = 0

    readiness = (0.6 * syllabus_completion) + (0.4 * consistency_score)
    return {
        'readiness_score': round(readiness, 1),
        'syllabus_completion': round(syllabus_completion, 1),
        'consistency_score': round(consistency_score, 1),
        'study_streak': streak,
    }


def get_plan_explanation(mongo, user_id):
    return [
        "<strong>Urgent exams first</strong> - subjects with sooner dates get more immediate slots",
        "<strong>Difficulty balance</strong> - harder subjects receive proportionally more time",
        "<strong>Syllabus coverage</strong> - makes sure all topics are scheduled before exam dates",
        "<strong>Daily load control</strong> - keeps each day inside your study-minute target",
        "<strong>Revision buffer</strong> - adds lighter review slots before important exams",
        "<strong>Cleaner resets</strong> - replacing an old plan removes pending duplicates automatically",
    ]
