# Health In One

**Student:** Hadeed Anser  
**Student ID:** W19826228  
**Module:** 6COSC023W Computer Science Final Project  

Health In One is a Django-based health tracking and recommendation system. The application allows users to log daily health metrics, receive an overall health score, view long-term progress, compare scores with friends, and receive machine-learning-led recommendations for improving their wellbeing.

---

## Project Overview

The aim of Health In One is to provide users with a single integrated platform for tracking health-related behaviours such as sleep, water intake, exercise, calories, steps, screen time, stress, mood, energy, fruit/vegetable intake, and protein intake.

The system calculates a daily health score and uses a machine learning model to recommend the changes predicted to improve the user’s score the most.

---

## Main Features

- User registration and login
- Profile setup with age, height, weight, activity level, and health goal
- Daily health metric logging using sliders
- Automatic health score calculation
- Machine-learning-led recommendations
- Predicted score improvement suggestions
- Dashboard with recent progress chart
- Long-term history page with 7-day, 30-day, 90-day, and all-time filters
- Clickable historical results
- Friends system
- Friends-only leaderboard

---

## Technologies Used

- Python
- Django
- SQLite
- Bootstrap
- Bootstrap Icons
- Chart.js
- Scikit-learn
- Joblib
- NumPy

---

## How To Run The Project

### 1. Clone The Repository

```powershell
git clone https://github.com/HA121104/Health-In-One.git
cd Health-In-One
```

---

### 2. Create And Activate A Virtual Environment

#### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.venv\Scripts\activate
```

#### Mac / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install Requirements

```powershell
pip install -r requirements.txt
```

---

### 4. Apply Database Migrations

```powershell
python manage.py migrate
```

---

### 5. Train The Machine Learning Model

```powershell
python -m tracking.ml.train_model
```

This creates the trained machine learning model used by the recommendation system.

The model is saved inside:

```text
tracking/ml_artifacts/health_score_model.joblib
```

---

### 6. Create Demo Data

```powershell
python manage.py seed_demo_data
```

This creates:

- Demo users
- User profiles
- 60 days of health history
- Daily scores
- ML-generated recommendations
- Accepted friendships
- Leaderboard data

---

### 7. Run The Server

```powershell
python manage.py runserver
```

Open the application in a browser:

```text
http://127.0.0.1:8000/
```

---

## Demo Login Details

After running the seed command, use:

```text
Username: demo_user
Password: demo12345
```

Other demo accounts:

```text
Username: active_friend
Password: demo12345

Username: casual_friend
Password: demo12345
```

---

## Important Pages

```text
/dashboard/             Main dashboard
/log/                   Log today’s health metrics
/history/               View long-term health history
/profile/               Edit user profile
/social/friends/        Manage friends
/social/leaderboard/    Friends-only leaderboard
```

---

## Machine Learning Explanation

Health In One uses a Random Forest Regressor to support the recommendation system.

The model uses features including:

- Age
- Height
- Weight
- Activity level
- Health goal
- Calories
- Water intake
- Sleep duration
- Exercise minutes
- Steps
- Screen time
- Stress level
- Mood level
- Energy level
- Fruit/vegetable servings
- Protein intake
- Recent 7-day average score
- Recent 30-day average score

The system compares the user’s current health data against possible improvement scenarios. It then predicts which changes are likely to increase the user’s health score the most and presents those changes as personalised recommendations.

---

## Scoring System

Each daily health metric is converted into a hidden subscore out of 100. The user does not directly see all individual subscores, but they are used internally by the scoring and recommendation pipeline.

The overall score is calculated using weighted metric scores. This allows the system to consider multiple health areas rather than focusing on only one metric.

---

## Friends And Leaderboard

Users can search for other users, send friend requests, accept or decline requests, and remove friends.

The leaderboard compares the current user with accepted friends only. It uses each user’s recent saved scores to calculate an average, encouraging consistency rather than one-off high scores.

---

## History

The history page allows users to view saved results across:

- 7 days
- 30 days
- 90 days
- All saved results

Users can click previous dates to view the score, logged metrics, recommendations, and predicted improvements for that specific day.

---

## Notes For Assessors

The local database file is not included in the repository. A new database can be created by running:

```powershell
python manage.py migrate
```

Demo data can be regenerated at any time using:

```powershell
python manage.py seed_demo_data
```

If the machine learning model file is missing, it can be recreated using:

```powershell
python -m tracking.ml.train_model
```

---

## Current Final Version Status

Implemented:

- User authentication
- Profile personalisation
- Daily metric logging
- Expanded health tracking metrics
- Health scoring
- Machine-learning-led recommendations
- Predicted improvement comparison
- Long-term history
- Friends system
- Friends-only leaderboard
- Improved user interface with sliders, icons, cards, and charts
