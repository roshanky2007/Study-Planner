# Smart Study Planner

A complete Flask-based web application for intelligent exam preparation planning with MongoDB backend.

## Features

- **Authentication**: Secure registration, login, and session management with password hashing
- **Subject Management**: Track subjects with exam dates, difficulty levels, and color tags
- **Topic Management**: Break down subjects into topics with estimated study time
- **Intelligent Planner**: AI-driven algorithm that generates day-by-day, block-by-block study schedules
- **Daily Execution**: Mark sessions complete, skip, reschedule, or add notes
- **Progress Tracking**: Real-time completion percentages, streaks, and readiness scores
- **Visual Timetable**: Weekly grid view showing time blocks and study sessions
- **Backlog Management**: Automatically handles missed sessions with prioritized catch-up

## Prerequisites

- Python 3.8 or higher
- MongoDB 4.0 or higher (local or Atlas)
- pip (Python package manager)

## Setup Instructions

### 1. Clone/Download the Project

```bash
cd /home/user/webapp
```

### 2. Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file:

**Windows:**
```cmd
copy .env.example .env
```

**Linux/macOS:**
```bash
cp .env.example .env
```

Edit `.env` and configure:

```env
SECRET_KEY=your-secret-key-here-change-in-production
MONGO_URI=mongodb://localhost:27017/smart_study_planner
FLASK_ENV=development
```

**For MongoDB Atlas** (cloud database):
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/smart_study_planner?retryWrites=true&w=majority
```

### 5. Start MongoDB (if running locally)

**Windows:**
```cmd
mongod
```

**Linux/macOS:**
```bash
sudo systemctl start mongod
# OR
mongod --dbpath /path/to/data/directory
```

### 6. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Usage Guide

### First Time Setup

1. **Register an Account**
   - Navigate to `http://localhost:5000`
   - Click "Get Started" or "Register"
   - Fill in name, email, password
   - Login with your credentials

2. **Add Subjects**
   - Go to "Subjects" page
   - Click "Add Subject"
   - Enter: name, exam date, difficulty (1-5), optional color
   - Example: "Physics", "2026-03-15", difficulty 4

3. **Add Topics to Each Subject**
   - Click on a subject card
   - Add topics one by one or multiple at once
   - For each topic: title, estimated minutes (default 60)
   - Example: "Ray Optics - 90 min", "Electrostatics - 120 min"

4. **Generate Your Study Plan**
   - Go to "Planner" page
   - Click "Generate New Plan"
   - Configure:
     - Daily study time (e.g., 240 minutes)
     - Start date (default: today)
     - End date (default: latest exam date)
     - Time blocks: Morning (6-12), Afternoon (12-18), Evening (18-24)
     - Max sessions per day (e.g., 4)
     - Revision buffer days before exam (e.g., 2)
   - Click "Generate Plan"

5. **Follow Your Daily Schedule**
   - Dashboard shows today's sessions with time blocks
   - Each session shows: subject, topic, time block, planned minutes
   - Actions:
     - ✓ Mark Complete (optionally log actual minutes)
     - ⏭ Skip (moves to backlog automatically)
     - ↻ Reschedule to another day
     - 📝 Add quick note

6. **Track Progress**
   - View completion % per subject
   - Monitor study streak (consecutive days)
   - Check readiness score with explanation
   - View weekly/monthly statistics

## Database Structure

### Collections

**users**
```javascript
{
  _id: ObjectId,
  name: String,
  email: String (unique, indexed),
  password_hash: String,
  created_at: DateTime
}
```

**subjects**
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (indexed),
  name: String,
  difficulty: Integer (1-5),
  exam_date: DateTime,
  color: String (hex),
  created_at: DateTime
}
```

**topics**
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (indexed),
  subject_id: ObjectId (indexed),
  title: String,
  estimated_minutes: Integer,
  status: String (pending/completed),
  priority_override: Integer (optional),
  created_at: DateTime
}
```

**plans**
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (indexed),
  daily_study_minutes: Integer,
  start_date: DateTime,
  end_date: DateTime,
  blocks: Array of Strings,
  max_sessions_per_day: Integer,
  revision_buffer_days: Integer,
  created_at: DateTime,
  algorithm_version: String
}
```

**sessions**
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (indexed),
  plan_id: ObjectId,
  subject_id: ObjectId (indexed),
  topic_id: ObjectId (indexed),
  date: DateTime (indexed),
  block: String,
  planned_minutes: Integer,
  actual_minutes: Integer (optional),
  status: String (pending/completed/skipped),
  notes: String (optional),
  completed_at: DateTime (optional)
}
```

**study_logs**
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (indexed),
  session_id: ObjectId,
  subject_id: ObjectId,
  topic_id: ObjectId,
  actual_minutes: Integer,
  notes: String,
  logged_at: DateTime (indexed)
}
```

### Indexes Created

```python
users: email (unique)
subjects: user_id, exam_date
topics: user_id, subject_id, status
sessions: user_id, date, status, subject_id
study_logs: user_id, logged_at
```

## Planner Algorithm Explanation

### Core Logic (8-12 bullet points)

1. **Exam Prioritization**: Subjects with nearer exam dates receive higher priority using exponential decay formula: `priority = base_priority * (1 / (days_until_exam + 1)^0.3)`

2. **Difficulty Weighting**: Harder subjects (difficulty 4-5) get 1.3x priority boost; easier subjects (1-2) get 0.8x to balance effort distribution

3. **Syllabus Completion**: Remaining topic minutes are calculated; subjects with more incomplete work get proportionally more time slots

4. **Time Allocation**: Total available study time = (end_date - start_date) × daily_study_minutes, distributed across all incomplete topics

5. **Block Distribution**: Each day's study time is divided into blocks (Morning/Afternoon/Evening), with sessions assigned to blocks based on priority scores

6. **Variety Enforcement**: Algorithm tracks last assigned subject and applies a 0.6x penalty to prevent same subject in consecutive blocks (improves retention via interleaving)

7. **Revision Buffer**: Last N days before each exam are reserved for revision sessions covering all topics of that subject (default: 2 days)

8. **Session Sizing**: Topics are split into sessions (default 60 min chunks) to fit block constraints; longer topics span multiple sessions

9. **Backlog Handling**: Skipped sessions receive 1.5x priority multiplier and are automatically reinserted into next available slots

10. **Completion Tracking**: Algorithm skips already-completed topics and adjusts remaining time allocations dynamically

11. **Deterministic Output**: Given same inputs (subjects, topics, dates), algorithm produces identical plan for reproducibility

12. **Edge Cases**: Handles scenarios like insufficient time, no topics, all topics complete, and past exam dates with graceful fallbacks

### Why This Plan? (Shown to Users)

The generated plan considers:
- ⏰ **Urgent exams first** - subjects with sooner dates get more immediate slots
- 📚 **Difficulty balance** - harder subjects receive proportionally more time
- 🎯 **Syllabus coverage** - ensures all topics are covered before exam dates
- 🔄 **Variety** - avoids studying the same subject in consecutive blocks
- 📖 **Revision time** - reserves buffer days before exams for review
- ⚡ **Your pace** - respects your daily study time and session preferences

## Readiness Score Formula

```
Readiness Score = (0.6 × Syllabus Completion %) + (0.4 × Consistency Score)

Where:
- Syllabus Completion % = (completed topic minutes / total topic minutes) × 100
- Consistency Score = (study streak / plan duration) × 100, capped at 100%
```

**Explanation**: 
- 60% weight on syllabus completion ensures you've covered the material
- 40% weight on consistency rewards regular study habits (streak tracking)
- Score ranges from 0-100%, where 80%+ indicates "Exam Ready" status

## Manual Test Checklist

### Authentication
- [ ] Register new user with valid details
- [ ] Attempt register with duplicate email (should fail)
- [ ] Login with correct credentials
- [ ] Login with wrong password (should fail)
- [ ] Logout and verify redirect to landing page
- [ ] Access protected page without login (should redirect to login)

### Subject Management
- [ ] Add subject with all fields
- [ ] Add subject with only required fields (name, exam date, difficulty)
- [ ] Edit subject and verify changes persist
- [ ] Delete subject (verify topics also deleted)
- [ ] Verify "days left" calculation is correct
- [ ] Add multiple subjects with different exam dates

### Topic Management
- [ ] Add topic to a subject
- [ ] Add multiple topics quickly
- [ ] Mark topic as completed
- [ ] Edit topic estimated minutes
- [ ] Delete topic
- [ ] Verify totals show correctly (X/Y topics, X/Y minutes)
- [ ] Try accessing topics page without subjects (should guide user)

### Planner Generation
- [ ] Generate plan with default settings
- [ ] Generate plan with custom daily minutes (120, 360)
- [ ] Generate plan with custom date range
- [ ] Generate plan with revision buffer (0, 3, 5 days)
- [ ] Verify plan respects exam dates (no sessions after exam)
- [ ] Verify plan shows readable timetable (Date → Block → Topic)
- [ ] Verify "Why this plan?" section displays

### Session Execution
- [ ] Mark session as complete from dashboard
- [ ] Log actual minutes (different from planned)
- [ ] Skip session and verify it appears in backlog
- [ ] Reschedule session to different day
- [ ] Add note to session
- [ ] Verify completed session shows checkmark
- [ ] Verify skipped session shows in backlog with reschedule option

### Progress Tracking
- [ ] Complete some sessions and verify progress % updates
- [ ] Study on consecutive days and verify streak increments
- [ ] Miss a day and verify streak resets
- [ ] Check readiness score calculation
- [ ] Verify per-subject completion percentages
- [ ] View weekly summary on dashboard

### Timetable Views
- [ ] Switch between weekly grid and list view
- [ ] Verify weekly grid shows correct days and blocks
- [ ] Verify sessions appear in correct cells with color tags
- [ ] Navigate between weeks
- [ ] Verify today is highlighted

### Edge Cases
- [ ] Generate plan with no topics (should show error/guide)
- [ ] Generate plan with all topics completed (should notify)
- [ ] Set exam date in the past (should warn)
- [ ] Set insufficient study time for syllabus (should adjust/warn)
- [ ] Delete subject that has active plan sessions (should cascade properly)

## Security Features

- ✅ Passwords hashed with Werkzeug's `pbkdf2:sha256` (NEVER stored plain text)
- ✅ Session-based authentication with secure session cookies
- ✅ `login_required` decorator protects all private routes
- ✅ User data scoped by `user_id` (users can't access others' data)
- ✅ Input validation on all forms (server-side)
- ✅ Date/number sanitization to prevent injection
- ✅ SECRET_KEY for session encryption (must be changed in production)
- ✅ CSRF protection via Flask session management

## Project Structure

```
webapp/
├── app.py                      # Main Flask application entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .env                       # Environment variables (DO NOT COMMIT)
├── README.md                  # This file
│
├── utils/
│   ├── __init__.py
│   ├── auth.py                # Authentication helpers, decorators
│   ├── planner.py             # Planner algorithm implementation
│   └── db_helpers.py          # Database query helpers
│
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py         # /register, /login, /logout
│   ├── subject_routes.py      # /subjects, /subjects/<id>/topics
│   ├── planner_routes.py      # /planner, /timetable
│   ├── dashboard_routes.py    # /dashboard
│   └── progress_routes.py     # /progress
│
├── static/
│   ├── css/
│   │   └── style.css          # Main stylesheet
│   ├── js/
│   │   └── main.js            # Client-side interactivity
│   └── images/
│       └── logo.png           # (Optional) logo
│
└── templates/
    ├── base.html              # Base layout with navbar
    ├── landing.html           # Landing page (/)
    ├── auth/
    │   ├── register.html      # Registration form
    │   └── login.html         # Login form
    ├── subjects/
    │   ├── list.html          # Subjects list
    │   └── topics.html        # Topics management for a subject
    ├── planner/
    │   ├── generate.html      # Plan generation form
    │   ├── list.html          # Generated plan overview
    │   └── timetable.html     # Weekly grid view
    ├── dashboard.html         # Main dashboard (today-first)
    └── progress.html          # Progress & readiness tracking
```

## Troubleshooting

### MongoDB Connection Errors

**Error**: `ServerSelectionTimeoutError`
- Ensure MongoDB is running: `mongod` (local) or check Atlas connection string
- Verify `MONGO_URI` in `.env` is correct
- Check firewall/network settings

### Port Already in Use

**Error**: `Address already in use`
```bash
# Find process using port 5000
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# Kill the process or change port in app.py
```

### Import Errors

**Error**: `ModuleNotFoundError`
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate      # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Session/Login Issues

- Clear browser cookies
- Verify `SECRET_KEY` is set in `.env`
- Check that Flask app is in debug mode during development

## Production Deployment Notes

1. **Change SECRET_KEY**: Generate a strong random key
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```

2. **Set FLASK_ENV**: Change to `production` in `.env`

3. **Use Production WSGI Server**: Gunicorn (Linux) or Waitress (Windows)
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

4. **Enable HTTPS**: Use reverse proxy (Nginx) with SSL certificate

5. **Database Indexes**: Ensure all indexes are created (run app once to auto-create)

6. **Backup Strategy**: Implement MongoDB backup/restore procedures

## License

MIT License - Free to use and modify

## Support

For issues, questions, or contributions, please open an issue on the project repository.

---

**Version**: 1.0.0  
**Last Updated**: February 2026  
**Author**: Senior Full-Stack Engineering Team
