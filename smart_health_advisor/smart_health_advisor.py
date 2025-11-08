# smart_health_advisor.py
# Single-file Streamlit app with authentication, tracking, recommendations.
# Save as smart_health_advisor.py then run: streamlit run smart_health_advisor.py

import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, date
import os
import math
import bcrypt

# ---------------- Config ----------------
DB_PATH = "smart_health.db"
st.set_page_config(page_title="Smart Health Advisor", layout="centered")

# ---------------- Database helpers ----------------
def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        height_cm REAL,
        weight_kg REAL,
        activity_level TEXT,
        medical_conditions TEXT,
        created_at TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        log_date TEXT,
        food_text TEXT,
        calories_consumed REAL,
        steps_walked INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    ph = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return ph.decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def create_user(username, password, name="", age=25, gender="Other", height_cm=170.0, weight_kg=70.0, activity_level="Sedentary", medical_conditions=""):
    conn = get_conn()
    c = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    c.execute("""
        INSERT INTO users (username, password_hash, name, age, gender, height_cm, weight_kg, activity_level, medical_conditions, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (username, password_hash, name, age, gender, height_cm, weight_kg, activity_level, medical_conditions))
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute(\"SELECT * FROM users WHERE username=?\", (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    keys = [\"id\",\"username\",\"password_hash\",\"name\",\"age\",\"gender\",\"height_cm\",\"weight_kg\",\"activity_level\",\"medical_conditions\",\"created_at\"]

    return dict(zip(keys, row))

def get_user_by_id(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(\"SELECT * FROM users WHERE id=?\", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    keys = [\"id\",\"username\",\"password_hash\",\"name\",\"age\",\"gender\",\"height_cm\",\"weight_kg\",\"activity_level\",\"medical_conditions\",\"created_at\"]

    return dict(zip(keys, row))

def update_profile(user_id, profile: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute(\"\"\"
        UPDATE users SET name=?, age=?, gender=?, height_cm=?, weight_kg=?, activity_level=?, medical_conditions=?
        WHERE id=?
    \"\"\", (profile.get(\"name\",\"\"), profile.get(\"age\",25), profile.get(\"gender\",\"Other\"),
          profile.get(\"height_cm\",170.0), profile.get(\"weight_kg\",70.0), profile.get(\"activity_level\",\"Sedentary\"),
          profile.get(\"medical_conditions\",\"\"), user_id))
    conn.commit()
    conn.close()

def add_log(user_id:int, log:dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute(\"\"\"
        INSERT INTO logs (user_id, log_date, food_text, calories_consumed, exercise_text, calories_burned, water_liters, sleep_hours, notes)
        VALUES (?,?,?,?,?,?,?,?,?)
    \"\"\", (
        user_id,
        log.get(\"log_date\", date.today().isoformat()),
        log.get(\"food_text\",\"\"),
        float(log.get(\"calories_consumed\",0.0)),
        log.get(\"exercise_text\",\"\"),
        float(log.get(\"calories_burned\",0.0)),
        float(log.get(\"water_liters\",0.0)),
        float(log.get(\"sleep_hours\",0.0)),
        log.get(\"notes\",\"\")
    ))
    conn.commit()
    conn.close()

def get_logs(user_id:int):
    conn = get_conn()
    df = pd.read_sql_query(\"SELECT * FROM logs WHERE user_id=? ORDER BY log_date\", conn, params=(user_id,))
    conn.close()
    return df

def get_all_users_df():
    conn = get_conn()
    df = pd.read_sql_query(\"SELECT id, username, name, age, gender, height_cm, weight_kg, activity_level FROM users\", conn)
    conn.close()
    return df

# ---------------- Health logic ----------------
def calculate_bmi(weight_kg, height_cm):
    try:
        h_m = height_cm / 100.0
        if h_m <= 0: return None
        bmi = weight_kg / (h_m*h_m)
        return round(bmi,2)
    except Exception:
        return None

def bmi_category(bmi):
    if bmi is None: return \"Unknown\"
    if bmi < 18.5: return \"Underweight\"
    if bmi < 25: return \"Normal\"
    if bmi < 30: return \"Overweight\"
    return \"Obese\"

def calculate_bmr(weight_kg, height_cm, age, gender):
    try:
        if gender.lower() in (\"male\",\"m\"):
            bmr = 10*weight_kg + 6.25*height_cm - 5*age + 5
        else:
            bmr = 10*weight_kg + 6.25*height_cm - 5*age - 161
        return round(bmr,1)
    except Exception:
        return None

def activity_multiplier(level):
    mapping = {
        \"Sedentary\":1.2,
        \"Lightly active\":1.375,
        \"Moderately active\":1.55,
        \"Very active\":1.725,
        \"Extra active\":1.9
    }
    return mapping.get(level,1.2)

def daily_calorie_needs(bmr, activity_level):
    if bmr is None: return None
    mult = activity_multiplier(activity_level)
    return int(round(bmr * mult))

def recommend_exercises(bmi, medical_conditions):
    recs = []
    conds = (medical_conditions or \"\").lower()
    if bmi is None:
        return [\"Missing data\"]
    if bmi < 18.5:
        recs.append(\"Strength training 3x/week — progressive overload; include protein-rich meals.\")
    elif bmi < 25:
        recs.append(\"Balanced routine: cardio 3x/week + strength 2x/week + mobility daily.\")
    elif bmi < 30:
        recs.append(\"Moderate cardio (30-45 min daily) + light strength 2x/week.\")
    else:
        recs.append(\"Low-impact cardio (walking, swimming) 20-40 min daily; consult a doctor before intense training.\")
    if \"diab\" in conds:
        recs.append(\"Include regular brisk walking and resistance training to assist blood sugar control.\")
    if \"heart\" in conds or \"hypert\" in conds:
        recs.append(\"Keep activity low-to-moderate; consult cardiologist before starting.\")
    if \"back\" in conds:
        recs.append(\"Focus on core, mobility, and avoid heavy spinal load initially.\")
    return recs

def recommend_diet(bmi, medical_conditions, calorie_target):
    conds = (medical_conditions or \"\").lower()
    eat = []
    avoid = []
    if bmi is None:
        return {\"eat\":[\"No data\"], \"avoid\":[\"No data\"]}
    if bmi < 18.5:
        eat += [\"Protein-rich foods (eggs, dairy, legumes)\", \"Healthy calories: nuts, avocados, whole grains\"
        ]
        avoid += [\"Empty-calorie snacks that replace nutrient-dense food\"]
    elif bmi < 25:
        eat += [\"Balanced meals: lean protein, vegetables, whole grains, healthy fats\"]
        avoid += [\"Excess added sugars\", \"High saturated fats\"]
    elif bmi < 30:
        eat += [\"High-fiber foods, lean proteins, vegetables, legumes\"]
        avoid += [\"Sugary drinks, fried foods, refined carbs\"]
    else:
        eat += [\"Low-calorie high-volume foods (veg), lean protein, legumes\"]
        avoid += [\"Processed and sugary foods, high-fat fried items\"]
    if \"diab\" in conds:
        eat += [\"Low glycemic carbs, non-starchy vegetables\"]
        avoid += [\"Sweets, sugary drinks\"]
    if \"hypert\" in conds or \"blood pressure\" in conds:
        eat += [\"Potassium-rich foods, whole grains, lean protein\"]
        avoid += [\"High-sodium processed foods\"]
    if calorie_target:
        eat.append(f\"Target calories ≈ {calorie_target} kcal/day (adjust goals slowly)\")
    # deduplicate
    eat = list(dict.fromkeys(eat))
    avoid = list(dict.fromkeys(avoid))
    return {\"eat\":eat,\"avoid\":avoid}

# ---------------- UI / App ----------------
init_db()
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

st.title(\"Smart Health Advisor 🩺\")
st.caption(\"Sign up, login, track daily health, and get personalised diet & exercise suggestions.\")

# ---- Authentication ----
if st.session_state.user_id is None:
    st.subheader(\"🔐 Login or Create Account\")
    tab1, tab2 = st.tabs([\"Login\",\"Sign Up\"])

    with tab1:
        with st.form(\"login_form\"):
            lu = st.text_input(\"Username\")
            lp = st.text_input(\"Password\", type=\"password\")
            lbtn = st.form_submit_button(\"Login\")
            if lbtn:
                user = get_user_by_username(lu.strip())
                if user and check_password(lp, user[\"password_hash\"]):
                    st.success(\"Login successful\")
                    st.session_state.user_id = user[\"id\"]
                    st.experimental_rerun()
                else:
                    st.error(\"Invalid username or password\")

    with tab2:
        with st.form(\"signup_form\"):
            su = st.text_input(\"Choose username\")
            sp = st.text_input(\"Choose password\", type=\"password\")
            name = st.text_input(\"Full name\")
            age = st.number_input(\"Age\", 8, 120, 25)
            gender = st.selectbox(\"Gender\", [\"Male\",\"Female\",\"Other\"])
            height = st.number_input(\"Height (cm)\", 80.0, 250.0, 170.0)
            weight = st.number_input(\"Weight (kg)\", 20.0, 300.0, 70.0)
            activity = st.selectbox(\"Activity level\", [\"Sedentary\",\"Lightly active\",\"Moderately active\",\"Very active\",\"Extra active\"])
            medical = st.text_area(\"Medical conditions (comma separated)\")
            sbtn = st.form_submit_button(\"Create account\")
            if sbtn:
                if not su or not sp:
                    st.error(\"Please provide username and password\")
                else:
                    existing = get_user_by_username(su.strip())
                    if existing:
                        st.error(\"Username already taken\")
                    else:
                        try:
                            uid = create_user(su.strip(), sp, name=name, age=age, gender=gender, height_cm=height, weight_kg=weight, activity_level=activity, medical_conditions=medical)
                            st.success(f\"Account created (id {uid}). Please login.\")
                        except Exception as e:
                            st.error(f\"Error creating account: {e}\")

# ---- Main app for logged-in users ----
else:
    user = get_user_by_id(st.session_state.user_id)
    st.sidebar.write(f\"👋 Hello, **{user.get('name') or user.get('username')}**\")
    if st.sidebar.button(\"Logout\"):
        st.session_state.user_id = None
        st.experimental_rerun()

    menu = st.sidebar.selectbox(\"Menu\", [\"Dashboard\",\"Profile\",\"Daily Tracker\",\"Recommendations\",\"Reports\",\"Admin\"])
    # Dashboard
    if menu == \"Dashboard\":
        st.header(\"Dashboard\")
        st.write(\"Quick summary of your profile and today.\")
        user = get_user_by_id(st.session_state.user_id)
        bmi = calculate_bmi(user['weight_kg'], user['height_cm'])
        bmr = calculate_bmr(user['weight_kg'], user['height_cm'], user['age'], user['gender'])
        calorie_need = daily_calorie_needs(bmr, user['activity_level'])
        col1, col2, col3 = st.columns(3)
        col1.metric(\"BMI\", bmi, bmi_category(bmi))
        col2.metric(\"BMR (kcal/day)\", bmr)
        col3.metric(\"Daily need (kcal)\", calorie_need)
        st.markdown(\"---\")
        st.write(\"Recent logs (last 5)\")
        df = get_logs(st.session_state.user_id)
        if df.empty:
            st.info(\"No logs yet. Use 'Daily Tracker' to add entries.\")
        else:
            st.dataframe(df.tail(5))

    # Profile edit
    elif menu == \"Profile\":
        st.header(\"Your Profile\")
        user = get_user_by_id(st.session_state.user_id)
        with st.form(\"profile_edit\"):
            name = st.text_input(\"Full name\", value=user.get(\"name\") or \"\")
            age = st.number_input(\"Age\", 8, 120, int(user.get(\"age\") or 25))
            gender = st.selectbox(\"Gender\", [\"Male\",\"Female\",\"Other\"], index=0 if user.get(\"gender\",\"Other\")==\"Male\" else (1 if user.get(\"gender\")==\"Female\" else 2))
            height = st.number_input(\"Height (cm)\", 80.0, 250.0, float(user.get(\"height_cm\") or 170.0))
            weight = st.number_input(\"Weight (kg)\", 20.0, 300.0, float(user.get(\"weight_kg\") or 70.0))
            activity = st.selectbox(\"Activity level\", [\"Sedentary\",\"Lightly active\",\"Moderately active\",\"Very active\",\"Extra active\"], index=0)
            medical = st.text_area(\"Medical conditions\", value=user.get(\"medical_conditions\") or \"\")
            save = st.form_submit_button(\"Save profile\")
            if save:
                update_profile(st.session_state.user_id, {
                    \"name\":name, \"age\":age, \"gender\":gender, \"height_cm\":height, \"weight_kg\":weight, \"activity_level\":activity, \"medical_conditions\":medical
                })
                st.success(\"Profile updated\")
                st.experimental_rerun()

        st.markdown(\"---\")
        st.write(\"Account info\")
        st.write(f\"Username: `{user.get('username')}`\")
        st.write(f\"Created at: {user.get('created_at')}\"
)

# end of app code
