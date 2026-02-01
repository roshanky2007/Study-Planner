# 🚀 Quick Start Guide - Smart Study Planner

Get up and running in **5 minutes**!

---

## ⚡ Super Quick Start

### Option 1: Automated Script (Recommended)

**Linux/macOS:**
```bash
cd /home/user/webapp
./start.sh
```

**Windows:**
```cmd
cd C:\path\to\webapp
start.bat
```

The script will:
1. ✅ Check Python installation
2. ✅ Create virtual environment
3. ✅ Install dependencies
4. ✅ Configure .env file
5. ✅ Start the application

Then open: **http://localhost:5000**

---

## 📋 Manual Setup (5 Steps)

### Step 1: Prerequisites

Ensure you have:
- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **MongoDB 4.0+** ([Download](https://www.mongodb.com/try/download/community))
- **pip** (comes with Python)

Verify installations:
```bash
python3 --version  # Should show 3.8 or higher
mongod --version   # Should show 4.0 or higher
```

### Step 2: Start MongoDB

**Linux/macOS:**
```bash
sudo systemctl start mongod
# OR
mongod --dbpath /path/to/data
```

**Windows:**
```cmd
net start MongoDB
# OR
"C:\Program Files\MongoDB\Server\4.4\bin\mongod.exe"
```

### Step 3: Setup Python Environment

```bash
cd /home/user/webapp

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate          # Linux/macOS
venv\Scripts\activate             # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment

The `.env` file is already configured for local development:

```env
SECRET_KEY=dev-secret-key-change-in-production-use-secrets-token-hex
FLASK_ENV=development
MONGO_URI=mongodb://localhost:27017/smart_study_planner
PORT=5000
```

**For MongoDB Atlas (cloud):**
Edit `.env` and change `MONGO_URI`:
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/smart_study_planner?retryWrites=true&w=majority
```

### Step 5: Run Application

```bash
python app.py
```

You should see:
```
============================================================
🎓 Smart Study Planner Starting...
============================================================
📍 URL: http://localhost:5000
🔧 Environment: development
🗄️  Database: localhost:27017/smart_study_planner
============================================================

✓ Database indexes created successfully
 * Running on http://0.0.0.0:5000
```

Open your browser to **http://localhost:5000**

---

## 🎯 First Use Tutorial

### 1. Create Account (30 seconds)

1. Click **"Get Started"** or **"Register"**
2. Fill in:
   - **Name**: Your full name
   - **Email**: your.email@example.com
   - **Password**: At least 6 characters
   - **Confirm Password**: Same as above
3. Click **"Create Account"**

You'll be automatically logged in!

### 2. Add Subjects (2 minutes)

1. Go to **"Subjects"** in navigation
2. Fill the form:
   - **Subject Name**: e.g., "Physics"
   - **Exam Date**: Pick a future date (e.g., March 15, 2026)
   - **Difficulty**: 1-5 (how hard is it?)
   - **Color Tag**: Pick a color (optional)
3. Click **"Add Subject"**

Repeat for all your subjects (Math, Chemistry, History, etc.)

### 3. Add Topics (2 minutes per subject)

1. Click **"Manage Topics"** on a subject card
2. For each topic in that subject:
   - **Topic Title**: e.g., "Ray Optics"
   - **Estimated Minutes**: How long to study it? (default: 60)
3. Click **"Add Topic"**

Example topics for Physics:
- Ray Optics - 90 min
- Electrostatics - 120 min
- Current Electricity - 90 min
- Magnetism - 120 min

### 4. Generate Your Study Plan (1 minute)

1. Go to **"Planner"** in navigation
2. Configure your plan:
   - **Daily Study Time**: e.g., 240 minutes (4 hours)
   - **Start Date**: Today (or tomorrow)
   - **End Date**: Your last exam date
   - **Max Sessions Per Day**: 4 (recommended)
   - **Revision Buffer**: 2 days (recommended)
3. Click **"🚀 Generate My Study Plan"**

The algorithm will create a complete schedule in seconds!

### 5. Follow Your Schedule (Daily)

1. Go to **"Dashboard"** every day
2. You'll see:
   - **Today's Sessions** grouped by time block (Morning/Afternoon/Evening)
   - Each session shows: Subject, Topic, Time, Minutes
3. For each session:
   - ✅ **Complete**: Mark done (optionally log actual time)
   - ⏭ **Skip**: Moves to backlog automatically
   - ↻ **Reschedule**: Move to different day
   - 📝 **Add Note**: Quick reminder

### 6. Track Progress (Weekly)

1. Go to **"Progress"** page
2. View:
   - **Readiness Score**: 0-100% (how exam-ready are you?)
   - **Syllabus Completion**: % of topics covered
   - **Study Streak**: Consecutive days studied
   - **Per-Subject Progress**: Visual breakdown

---

## 🎨 Feature Highlights

### Dashboard (Today-First View)
- ✅ Today's sessions with time blocks
- 📊 Quick stats (progress, streak, backlog)
- 📅 This week overview (7-day strip)
- 🔔 Backlog items (skipped sessions)
- 📆 Upcoming exams

### Timetable (Weekly Planning)
- 📅 **Grid View**: 7 days × 3 blocks matrix
- 📝 **List View**: Detailed day-by-day
- ⬅️ ➡️ Navigate weeks
- 🎨 Color-coded by subject

### Planner Algorithm
- 🎯 Prioritizes urgent exams
- 📚 Weights by difficulty
- 🔄 Ensures variety (no consecutive same subject)
- 📖 Reserves revision days before exams
- ⚡ Handles backlog automatically

### Progress Tracking
- 📊 Readiness score with formula explanation
- 🔥 Study streak tracking
- 📈 Per-subject completion bars
- ⏱ Time tracking (planned vs actual)

---

## 🔧 Troubleshooting

### MongoDB Connection Error

**Error**: `ServerSelectionTimeoutError`

**Solutions:**
1. Ensure MongoDB is running: `mongod`
2. Check MONGO_URI in `.env`
3. For local MongoDB: `mongodb://localhost:27017/smart_study_planner`
4. For Atlas: Use connection string with credentials

### Port Already in Use

**Error**: `Address already in use: 5000`

**Solutions:**
1. Change PORT in `.env` to 5001
2. OR kill process using port 5000:
   ```bash
   lsof -ti:5000 | xargs kill  # Linux/macOS
   netstat -ano | findstr :5000  # Windows (find PID, then taskkill)
   ```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### No Subjects/Topics

**Problem**: Generated plan shows error "No topics found"

**Solution:**
1. Add at least one subject
2. Add at least one topic to that subject
3. Try generating plan again

---

## 📱 Browser Compatibility

Tested and works on:
- ✅ Chrome/Edge (Recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Opera

---

## 🆘 Getting Help

### Documentation
- 📖 **README.md**: Full documentation (setup, features, testing)
- 📋 **IMPLEMENTATION_SUMMARY.md**: Technical details
- 🚀 **QUICKSTART.md**: This guide

### Common Questions

**Q: Can I use this for multiple users?**  
A: Yes! Each user has isolated data. Just register separate accounts.

**Q: Where is my data stored?**  
A: MongoDB database (local or cloud). Completely secure and scoped per-user.

**Q: Can I edit a plan after generating?**  
A: Yes! You can reschedule, skip, or complete sessions individually.

**Q: How accurate is the readiness score?**  
A: It balances syllabus completion (60%) and study consistency (40%). 80%+ means exam-ready.

**Q: Can I delete my account?**  
A: Currently manual. Delete all your subjects, or drop the MongoDB database.

---

## 🎉 You're All Set!

The Smart Study Planner is now running. Here's your study workflow:

1. **Sunday**: Review weekly timetable, adjust if needed
2. **Daily**: Check dashboard, complete sessions, track progress
3. **Weekly**: View progress page, check readiness score
4. **Before exams**: Ensure 80%+ readiness score

**Pro Tips:**
- ⏰ Study at consistent times (helps streak)
- 📝 Use notes to track difficult topics
- 🔄 Reschedule instead of skipping when possible
- 📊 Check progress weekly to stay motivated
- 🎯 Aim for 80%+ readiness before exams

---

## 📞 Support

For issues or questions:
1. Check **README.md** troubleshooting section
2. Review **IMPLEMENTATION_SUMMARY.md** for technical details
3. Verify setup steps in this guide

---

**Version**: 1.0.0  
**Last Updated**: February 2026  
**Status**: ✅ Production Ready

🎓 **Happy Studying!**
