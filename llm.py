#Merge both marksheet csv files which are gernerated by OCR

import pandas as pd
m1 = pd.read_csv('/content/marksheet_marks (5).csv')
m2 = pd.read_csv('/content/marksheet_marks (7).csv')

# Assign a unique student ID to each marksheet before merging
m1['id'] = 1 # Assuming this marksheet is for student_id 1
m2['id'] = 2 # Assuming this marksheet is for student_id 2

# Concatenate the dataframes. Now both have an 'id' column.
merged = pd.concat([m1, m2], axis=0, ignore_index=True)
merged.to_csv('marksheet_merged.csv', index=False)



#LLM Model


import pandas as pd

# ----------------------------------------------
# SUBFIELDS FOR EACH FIELD
# ----------------------------------------------
SUBFIELDS = {
    "Engineering": [
        "Mechanical Engineering",
        "Electrical Engineering",
        "Civil Engineering",
        "Software Engineering",
        "Chemical Engineering"
    ],
    "Medical": [
        "MBBS",
        "Pharmacy",
        "Physiotherapy",
        "Nursing",
        "Biotechnology"
    ],
    "Computer Science": [
        "Artificial Intelligence",
        "Data Science",
        "Cyber Security",
        "Software Development",
        "IT Management"
    ],
    "Business": [
        "BBA",
        "Marketing",
        "Finance",
        "HR Management",
        "Supply Chain"
    ],
    "Arts": [
        "Psychology",
        "Fine Arts",
        "Mass Communication",
        "English Literature",
        "Sociology"
    ],
    "Commerce": [
        "B.Com",
        "Accounting",
        "Banking",
        "Economics",
        "Business Administration"
    ]
}

# ----------------------------------------------
# LOAD PERSONALITY TEST (RIASEC + TCI)
# ----------------------------------------------
def load_personality(csv_path):
    df = pd.read_csv(csv_path)
    df = df.rename(columns={"user_id": "student_id"})
    return df


# ----------------------------------------------
# LOAD MARKSHEET & CONVERT TO WIDE FORMAT
# ----------------------------------------------
def load_marksheet(csv_path):
    df = pd.read_csv(csv_path)
    df = df.rename(columns={"Obtained": "marks", "Subject": "subject"})
    df = df[["subject", "marks"]]    # Only two columns needed
    df = df[~df["subject"].str.contains("TOTAL", case=False)]  # remove TOTAL rows
    df["subject"] = df["subject"].str.upper().str.strip()
    df = df.groupby("subject")["marks"].max().reset_index()   # handle duplicates
    return df


# ----------------------------------------------
# EXTRACT SUBJECT SCORES (MATH / PHY / ENG etc.)
# ----------------------------------------------
def extract_subject_scores(df):
    subjects = {
        "math": ["MATH", "MATHEMATICS"],
        "physics": ["PHYSICS"],
        "chemistry": ["CHEMISTRY"],
        "biology": ["BIOLOGY"],
        "computer": ["COMPUTER"],
        "english": ["ENGLISH"],
        "urdu": ["URDU"],
        "islamiat": ["ISLAM", "ISLAMIYAT"],
        "pakstudies": ["PAKISTAN"]
    }

    extracted = {}

    for key, keywords in subjects.items():
        extracted[key] = 0  # default
        for kw in keywords:
            row = df[df["subject"].str.contains(kw, case=False)]
            if len(row) > 0:
                extracted[key] = int(row.iloc[0]["marks"])
                break

    return extracted


# ----------------------------------------------
# RULE-BASED SCORING SYSTEM
# ----------------------------------------------
def calculate_best_fit(marks, personality):
    """
    marks: dict, e.g. {"math": 147, "physics":147, "biology":147, "chemistry":138, "english":137, "urdu":131, "computer":130}
    personality: dict, RIASEC + TCI scores scaled 0-5 or 0-100
    Returns: dict of normalized probabilities for each field
    """

    # Initialize raw scores
    scores = {
        "Medical": 0,
        "Engineering": 0,
        "Computer Science": 0,
        "Arts": 0,
        "Business": 0,
        "Commerce": 0
    }

    # -------------------------
    # MARKS WEIGHTS (field relevance)
    # -------------------------
    scores["Medical"] += (marks["biology"]/150)*0.35 + (marks["chemistry"]/150)*0.35 + (marks["physics"]/150)*0.1 + (marks["math"]/150)*0.1 + (marks["english"]/150)*0.05 + (marks["urdu"]/150)*0.05
    scores["Engineering"] += (marks["math"]/150)*0.35 + (marks["physics"]/150)*0.35 + (marks["chemistry"]/150)*0.1 + (marks["biology"]/150)*0.05 + (marks["english"]/150)*0.05 + (marks["urdu"]/150)*0.1
    scores["Computer Science"] += (marks["math"]/150)*0.3 + (marks["physics"]/150)*0.2 + (marks["computer"]/150)*0.25 + (marks["english"]/150)*0.1 + (marks["biology"]/150)*0.05 + (marks["urdu"]/150)*0.1
    scores["Arts"] += (marks["english"]/150)*0.4 + (marks["urdu"]/150)*0.3 + (marks["biology"]/150)*0.05 + (marks["chemistry"]/150)*0.05 + (marks["math"]/150)*0.1 + (marks["physics"]/150)*0.1
    scores["Business"] += (marks["math"]/150)*0.2 + (marks["english"]/150)*0.3 + (marks["urdu"]/150)*0.2 + (marks["biology"]/150)*0.05 + (marks["chemistry"]/150)*0.05 + (marks["physics"]/150)*0.2
    scores["Commerce"] += (marks["math"]/150)*0.3 + (marks["english"]/150)*0.25 + (marks["urdu"]/150)*0.2 + (marks["biology"]/150)*0.05 + (marks["chemistry"]/150)*0.05 + (marks["physics"]/150)*0.15

    # -------------------------
    # PERSONALITY / RIASEC WEIGHTS
    # personality scores assumed 0-5 scale
    # -------------------------
    scores["Medical"] += ((personality.get("riasec_I",0) + personality.get("riasec_A",0))/10) * 0.3
    scores["Engineering"] += ((personality.get("riasec_I",0) + personality.get("riasec_C",0))/10) * 0.3
    scores["Computer Science"] += ((personality.get("riasec_C",0) + personality.get("tci_NoveltySeeking",0))/10) * 0.3
    scores["Arts"] += ((personality.get("riasec_A",0) + personality.get("riasec_E",0))/10) * 0.3
    scores["Business"] += ((personality.get("riasec_E",0) + personality.get("tci_RewardDependence",0))/10) * 0.3
    scores["Commerce"] += ((personality.get("riasec_E",0) + personality.get("riasec_C",0))/10) * 0.3

    # -------------------------
    # NORMALIZE SCORES TO PROBABILITIES
    # -------------------------
    total_score = sum(scores.values())
    probabilities = {field: round(score/total_score, 3) for field, score in scores.items()}

    # Sort by highest probability
    probabilities = dict(sorted(probabilities.items(), key=lambda x: x[1], reverse=True))

    return probabilities



# ----------------------------------------------
# MAIN FUNCTION
# ----------------------------------------------
def recommend_field(personality_csv, marksheet_csv):
    # 1. Load datasets
    p = load_personality(personality_csv)
    m = load_marksheet(marksheet_csv)

    # Single student case
    personality = p.iloc[0].to_dict()

    # Extract subject scores
    marks = extract_subject_scores(m)

    # Score fields
    field_scores = calculate_best_fit(marks, personality)

    # Best field
    best_field = max(field_scores, key=field_scores.get)

    # Subfields
    best_subfields = SUBFIELDS[best_field]

    # Output
    print("Recommended Field:", best_field)
    print("Recommended Subfields:")
    for s in best_subfields:
        print("-", s)

    return best_field, best_subfields

# give there your response file path 

    recommend_field("/content/response.csv", "marksheet_merged.csv")
