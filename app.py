from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import os
from datetime import datetime

# ---- Configuration ----
APP_SECRET = "dreamroute_secret_key_change_this"
ADMIN_PASSWORD = "admin123"
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "responses.csv")

app = Flask(__name__)
app.secret_key = APP_SECRET

# ---- Question flow (Adaptive Tree) ----
QUESTION_FLOW = {
    "q1": {
        "text": "I enjoy solving logic or math problems.",
        "options": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
        "next": {
            "Strongly Agree": "q2_cs",
            "Agree": "q2_cs",
            "Neutral": "q2_business",
            "Disagree": "q2_creative",
            "Strongly Disagree": "q2_creative"
        }
    },
    "q2_cs": {
        "text": "Do you like learning programming languages?",
        "options": ["No", "Maybe", "Yes"],
        "next": {
            "Yes": "q3_ai",
            "Maybe": "q3_data",
            "No": "q2_creative"
        }
    },
    "q3_ai": {
        "text": "Would you enjoy working with AI or automation?",
        "options": ["Yes", "No"],
        "next": {
            "Yes": "end",
            "No": "end"
        }
    },
    "q2_business": {
        "text": "Do you like organizing or managing things?",
        "options": ["Yes", "No"],
        "next": {
            "Yes": "q3_leadership",
            "No": "q2_creative"
        }
    },
    "q3_leadership": {
        "text": "Would you enjoy leading a team or planning a project?",
        "options": ["Yes", "No"],
        "next": {
            "Yes": "end",
            "No": "end"
        }
    },
    "q2_creative": {
        "text": "Do you enjoy creative activities like designing or writing?",
        "options": ["Yes", "No"],
        "next": {
            "Yes": "q3_design",
            "No": "end"
        }
    },
    "q3_design": {
        "text": "Do you like creating visuals or working on aesthetics?",
        "options": ["Yes", "No"],
        "next": {
            "Yes": "end",
            "No": "end"
        }
    }
}

# ---- Ensure data dir exists ----
os.makedirs(DATA_DIR, exist_ok=True)

# ---- Helper: Save responses to CSV ----
def save_response(data_row: dict):
    df = pd.DataFrame([data_row])
    if not os.path.exists(DATA_FILE):
        df.to_csv(DATA_FILE, index=False)
    else:
        df.to_csv(DATA_FILE, mode='a', header=False, index=False)

# ---- Simple field prediction ----
def predict_field(answers):
    # basic scoring rules
    answers_text = " ".join(answers.values()).lower()
    if "ai" in answers_text or "programming" in answers_text or "logic" in answers_text:
        return "Computer Science / AI"
    elif "team" in answers_text or "manage" in answers_text:
        return "Business / Management"
    elif "creative" in answers_text or "design" in answers_text or "visual" in answers_text:
        return "Design / Arts"
    else:
        return "General Studies / Exploration"

# ---- Routes ----
@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    """Start the adaptive quiz"""
    name = request.form.get('student_name', 'Anonymous')
    email = request.form.get('student_email', '')
    session['student_name'] = name
    session['student_email'] = email
    session['answers'] = {}
    session['current_q'] = 'q1'
    return redirect(url_for('quiz'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        answer = request.form.get('answer')
        current_q = session['current_q']
        session['answers'][current_q] = answer

        # Determine next question
        next_q = QUESTION_FLOW[current_q]['next'].get(answer, 'end')
        session['current_q'] = next_q

        if next_q == 'end':
            return redirect(url_for('result'))

    current_q = session.get('current_q', 'q1')
    if current_q == 'end':
        return redirect(url_for('result'))

    q_data = QUESTION_FLOW[current_q]
    return render_template('quiz_dynamic.html', qid=current_q, qtext=q_data['text'], options=q_data['options'])

@app.route('/result')
def result():
    name = session.get('student_name', 'Anonymous')
    email = session.get('student_email', '')
    answers = session.get('answers', {})

    field = predict_field(answers)

    # save to CSV
    row = {"student_name": name, "student_email": email, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    row.update(answers)
    row['predicted_field'] = field
    save_response(row)

    return render_template('result.html', name=name, predicted=field, answers=answers)

# ---- Admin login & view ----
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pwd = request.form.get('password', '')
        if pwd == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash("Incorrect admin password.", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        table_html = df.to_html(classes='table table-striped table-bordered', index=False)
    else:
        table_html = "<p>No responses yet.</p>"
    return render_template('admin.html', table_html=table_html)

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash("Logged out.", "info")
    return redirect(url_for('index'))

# ---- Run ----
if __name__ == "__main__":
    app.run(debug=True)
