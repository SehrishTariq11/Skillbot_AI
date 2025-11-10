import streamlit as st
import pandas as pd
import auth
# -------------------- PAGE SETUP --------------------
st.set_page_config(page_title="SkillBot Interest Profile", layout="centered")
# -------------------- LOGIN / SIGNUP --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 SkillBot Login / Signup")

    option = st.radio("Choose an option:", ["Login", "Signup"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Login":
        if st.button("Login"):
            if auth.login(username, password):
                st.rerun()

    elif option == "Signup":
        if st.button("Sign Up"):
            auth.signup(username, password)

    st.stop()  # Stop app until login


# -------------------- LOAD DATA --------------------
questions = pd.read_csv("questions.csv")
careers = pd.read_csv("careers.csv")

# -------------------- SESSION STATE --------------------
if "page" not in st.session_state:
    st.session_state.page = "intro"
if "index" not in st.session_state:
    st.session_state.index = 0
if "answers" not in st.session_state:
    st.session_state.answers = []

# -------------------- FUNCTIONS --------------------
def restart():
    st.session_state.page = "intro"
    st.session_state.index = 0
    st.session_state.answers = []

def next_question(selected):
    st.session_state.answers.append(selected)
    st.session_state.index += 1
    if st.session_state.index >= len(questions):
        st.session_state.page = "results"

# -------------------- INTRO PAGE --------------------
if st.session_state.page == "intro":
    st.title("Welcome to the SkillBot Interest Profiler!")
    st.write("""
    Discover your work-related interests and explore career options that are a good fit for you.

    The process is super easy, but take your time — the results can help guide your future!
    """)
    st.markdown("""
    **Here’s how it works:**
    1. Think about how much you’d like to do various activities if they were part of your job.  
    2. See what your answers reveal about your work interests.  
    3. Explore careers matching your interest profile.  
    4. Have fun learning and exploring!
    """)
    st.divider()
    st.subheader("💭 What would you enjoy doing at your dream job?")
    st.write("""
    You’ll read 30 short work activity descriptions.  
    Picture yourself doing each one and select how much you’d like it.

    There are **no right or wrong answers**, and **no need to think about pay or education**—just interest!
    """)
    if st.button("Start the Profiler"):
        st.session_state.page = "quiz"

# -------------------- QUIZ PAGE --------------------
elif st.session_state.page == "quiz":
    q_idx = st.session_state.index
    q = questions.iloc[q_idx]

    st.markdown(f"### Question {q_idx + 1} of {len(questions)}")
    st.markdown(f"**{q['question']}**")

    st.write("How much would you enjoy this activity?")
    options = {
        "Strongly Disagree": "😠",
        "Disagree": "🙁",
        "Neutral": "😐",
        "Agree": "🙂",
        "Strongly Agree": "🤩"
    }

    cols = st.columns(len(options))
    for i, (label, icon) in enumerate(options.items()):
        if cols[i].button(f"{icon} {label}"):
            next_question(label)

# -------------------- RESULTS PAGE --------------------
elif st.session_state.page == "results":
    st.title("Your Interest Profile")

    # Calculate RIASEC scores
    df = questions.copy()
    df["answer"] = st.session_state.answers

    # Rating map (fixed indentation)
    rating_map = {
        "Strongly Disagree": 1,
        "Disagree": 2,
        "Neutral": 3,
        "Agree": 4,
        "Strongly Agree": 5
    }

    df["score"] = df["answer"].map(rating_map)

    # Handle missing scores safely
    df["score"].fillna(0, inplace=True)

    riasec_scores = df.groupby("category")["score"].mean().sort_values(ascending=False)
    top = riasec_scores.head(3).index.tolist()

    st.subheader("What is RIASEC?")
    st.write("RIASEC stands for **Realistic, Investigative, Artistic, Social, Enterprising, Conventional** — six types of work interests defined by psychologist John Holland.")

    st.write("### Your Profile Scores:")
    cols = st.columns(len(riasec_scores))
    for i, (cat, val) in enumerate(riasec_scores.items()):
        cols[i].metric(cat, f"{val:.1f}")

    st.markdown(f"**Your top interests are:** {', '.join(top)}")

    st.divider()
    st.write("Next, plan your career training and preparation—or skip ahead to see all your options!")

    if st.button("Explore Careers"):
        st.session_state.page = "careers"
        st.session_state.top_interests = top
    if st.button("🔁 Restart"):
        restart()

# -------------------- CAREER PAGE --------------------
elif st.session_state.page == "careers":
    st.title("💼 Career Suggestions")

    top_interests = st.session_state.get("top_interests", [])
    if not top_interests:
        st.warning("Please complete the test first.")
    else:
        st.write("Based on your top RIASEC interests, here are some careers you might explore:")
        for cat in top_interests:
            row = careers[careers["category"] == cat]
            if not row.empty:
                st.markdown(f"### {cat} — {row.iloc[0]['careers']}")
        st.divider()
        st.info("These careers are just starting points — explore more based on your interests and skills!")

    if st.button("🏠 Back to Start"):
        restart()

