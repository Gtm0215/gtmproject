import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import date

# --- Global Configuration ---
DB_PATH = "health_app.db"
# Set page configuration early
st.set_page_config(
    page_title="Smart Health Advisor",
    page_icon="🩺",
    layout="wide",
)

# ---------------- Database setup ----------------
@st.cache_resource
def get_conn():
    """Connects to the SQLite database."""
    # Use check_same_thread=False for Streamlit's multi-threading environment
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    """Initializes the database tables."""
    conn = get_conn()
    c = conn.cursor()
    
    # Create users table
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
        diet_preference TEXT DEFAULT 'Omnivore', -- Added diet preference
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create logs table
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        log_date TEXT,
        food_text TEXT,
        calories_consumed REAL,
        exercise_text TEXT,
        calories_burned REAL,
        water_liters REAL,
        sleep_hours REAL,
        notes TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    conn.commit()
    conn.close()

# ---------------- Authentication & User Management ----------------
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password: str, hashed: str):
    return hash_password(password) == hashed

def create_user(username, password, name, age, gender, height_cm, weight_kg, activity_level, medical_conditions, diet_preference="Omnivore"):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    INSERT INTO users (username, password_hash, name, age, gender, height_cm, weight_kg, activity_level, medical_conditions, diet_preference)
    VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (username, hash_password(password), name, age, gender, height_cm, weight_kg, activity_level, medical_conditions, diet_preference))
    conn.commit()
    uid = c.lastrowid
    conn.close()
    return uid

def get_user_by_username(username):
    conn = get_conn()
    c = conn.cursor()
    # Fixed SQL query issue from previous conversation: ensure proper quoting
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        cols = [desc[0] for desc in c.description]
        return dict(zip(cols, row))
    return None

def get_user_by_id(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        cols = [desc[0] for desc in c.description]
        return dict(zip(cols, row))
    return None

def update_profile(user_id, updates: dict):
    conn = get_conn()
    c = conn.cursor()
    # Create the SET clause dynamically
    fields = ", ".join([f"{k}=?" for k in updates.keys()])
    values = list(updates.values()) + [user_id]
    c.execute(f"UPDATE users SET {fields} WHERE id=?", values)
    conn.commit()
    conn.close()

# ---------------- Logs ----------------
def add_log(user_id: int, log: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    INSERT INTO logs (user_id, log_date, food_text, calories_consumed, exercise_text, calories_burned, water_liters, sleep_hours, notes)
    VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        user_id,
        log.get("log_date", date.today().isoformat()),
        log.get("food_text", ""),
        float(log.get("calories_consumed", 0.0)),
        log.get("exercise_text", ""),
        float(log.get("calories_burned", 0.0)),
        float(log.get("water_liters", 0.0)),
        float(log.get("sleep_hours", 0.0)),
        log.get("notes", "")
    ))
    conn.commit()
    conn.close()

def get_logs(user_id: int):
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM logs WHERE user_id=? ORDER BY log_date DESC", conn, params=(user_id,))
    conn.close()
    return df

# ---------------- Health logic ----------------
def calculate_bmi(weight_kg, height_cm):
    try:
        h_m = height_cm / 100.0
        if h_m <= 0: return None
        bmi = weight_kg / (h_m * h_m)
        return round(bmi, 2)
    except Exception:
        return None

def bmi_category(bmi):
    if bmi is None: return "Unknown"
    if bmi < 18.5: return "Underweight"
    if bmi < 25: return "Normal"
    if bmi < 30: return "Overweight"
    return "Obese"

def calculate_bmr(weight_kg, height_cm, age, gender):
    """Calculates Basal Metabolic Rate (BMR) using Mifflin-St Jeor equation."""
    try:
        if gender.lower() in ("male", "m"):
            # Male BMR: (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else: # Female or Other
            # Female BMR: (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
        return round(bmr, 1)
    except Exception:
        return None

def activity_multiplier(level):
    mapping = {
        "Sedentary": 1.2,
        "Lightly active": 1.375,
        "Moderately active": 1.55,
        "Very active": 1.725,
        "Extra active": 1.9
    }
    return mapping.get(level, 1.2)

def daily_calorie_needs(bmr, activity_level):
    if bmr is None: return None
    mult = activity_multiplier(activity_level)
    return int(round(bmr * mult))

# --- Enhanced Recommendation Functions ---
def recommend_exercises(bmi, medical_conditions, activity_level, gender):
    recs = []
    conds = (medical_conditions or "").lower()
    
    # 1. BMI and General Recommendations
    if bmi is None:
        recs.append("Missing data. Please complete your profile (Height and Weight).")
    elif bmi < 18.5:
        recs.append("Goal: Build Mass. **Strength training** 3x/week (Focus on compound lifts). Include light cardio for heart health.")
    elif bmi < 25:
        recs.append("Goal: Maintain. **Balanced routine**: Cardio 3x/week (running, cycling) + Strength 2x/week (full body).")
    elif bmi < 30:
        recs.append("Goal: Weight Loss. **Moderate cardio** (30-45 min daily, e.g., brisk walking, elliptical) + light strength 2x/week.")
    else:
        recs.append("Goal: Significant Weight Loss. **Low-impact cardio** (walking, swimming, water aerobics) 20-40 min daily. Consult a doctor before intense training.")

    # 2. Activity Level and Custom Exercise Suggestions
    if activity_level == "Very active":
        recs.append("Advanced: Consider a **custom gym split** (e.g., Push/Pull/Legs 4-5x/week) and focus on progressive overload.")
    
    # 3. Medical Conditions
    if "diab" in conds:
        recs.append("Medical: Regular brisk walking and **resistance training** help blood sugar control.")
    if "heart" in conds or "hypert" in conds:
        recs.append("Medical: Keep activity **low-to-moderate**; consult cardiologist before starting.")
    if "back" in conds:
        recs.append("Medical: Focus on **core and mobility** (planks, bird-dogs); avoid heavy spinal loads (squats, deadlifts) initially.")
        
    # 4. Gender Specific Tip
    if gender.lower() == "female":
        recs.append("Tip: Don't avoid lifting weights; it's essential for bone density and metabolism.")
    
    return list(dict.fromkeys(recs)) # Deduplicate

def recommend_diet(bmi, medical_conditions, calorie_target, diet_preference):
    conds = (medical_conditions or "").lower()
    eat = []
    avoid = []
    
    if bmi is None:
        return {"eat": ["No data"], "avoid": ["No data"]}

    # 1. BMI and General Recommendations
    if bmi < 18.5:
        eat += ["Calorie-dense, nutrient-rich foods", "Protein (eggs, dairy, legumes, meat)", "Healthy fats (nuts, avocados)"]
        avoid += ["Empty-calorie snacks that replace nutrient-dense food"]
    elif bmi < 25:
        eat += ["Balanced meals (40% Carbs, 30% Protein, 30% Fat)", "Lean protein, vegetables, whole grains"]
        avoid += ["Excess added sugars", "High saturated fats (limit fried foods)"]
    elif bmi < 30:
        eat += ["High-fiber foods (oats, vegetables, fruit)", "Lean proteins, legumes"]
        avoid += ["Sugary drinks, fried foods, refined carbs (white bread, pasta)"]
    else:
        eat += ["Low-calorie, high-volume foods (lots of veg, salads)", "Lean protein, legumes"]
        avoid += ["Processed and sugary foods, high-fat fried items"]

    # 2. Diet Preference
    if diet_preference == "Vegetarian":
        eat.append("Vegetarian Focus: Ensure complete protein with sources like lentils, tofu, quinoa, and dairy.")
        avoid.append("Avoid all meat, poultry, and fish.")
    elif diet_preference == "Vegan":
        eat.append("Vegan Focus: B12-fortified foods, beans, legumes, nuts, and seeds for protein/nutrients.")
        avoid.append("Avoid all animal products (meat, dairy, eggs, honey).")
    
    # 3. Medical Conditions
    if "diab" in conds:
        eat.append("Medical: Low glycemic carbs, non-starchy vegetables (e.g., leafy greens).")
        avoid.append("Sweets, sugary drinks, large portions of simple carbs.")
    if "hypert" in conds or "blood pressure" in conds:
        eat.append("Medical: Potassium-rich foods (banana, spinach), whole grains (DASH diet).")
        avoid.append("High-sodium processed foods, canned soups, fast food.")
    
    # 4. Calorie Target
    if calorie_target:
        eat.append(f"Target calories ≈ **{calorie_target} kcal/day** (Consult a professional for precise goals).")

    return {"eat": list(dict.fromkeys(eat)), "avoid": list(dict.fromkeys(avoid))} # Deduplicate


# ---------------- UI / App ----------------
init_db()

# Initialize session state for user authentication
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

st.title("Smart Health Advisor 🩺")
st.caption("Sign up, login, track daily health, and get personalised diet & exercise suggestions.")

# ---- Authentication Block ----
if st.session_state.user_id is None:
    st.subheader("🔐 Login or Create Account")
    tab1, tab2 = st.tabs(["Login","Sign Up"])

    with tab1: # Login Tab
        with st.form("login_form"):
            lu = st.text_input("Username")
            lp = st.text_input("Password", type="password")
            lbtn = st.form_submit_button("Login")
            if lbtn:
                user = get_user_by_username(lu.strip())
                if user and check_password(lp, user["password_hash"]):
                    st.success("Login successful")
                    st.session_state.user_id = user["id"]
                    st.rerun() # Corrected: st.experimental_rerun() -> st.rerun()
                else:
                    st.error("Invalid username or password")

    with tab2: # Sign Up Tab
        with st.form("signup_form"):
            st.write("Please fill in your basic health profile to get the best recommendations.")
            su = st.text_input("Choose username")
            sp = st.text_input("Choose password", type="password")
            name = st.text_input("Full name")
            age = st.number_input("Age", 8, 120, 25)
            gender = st.selectbox("Gender", ["Male","Female","Other"])
            height = st.number_input("Height (cm)", 80.0, 250.0, 170.0)
            weight = st.number_input("Weight (kg)", 20.0, 300.0, 70.0)
            activity = st.selectbox("Activity level", ["Sedentary","Lightly active","Moderately active","Very active","Extra active"])
            medical = st.text_area("Medical conditions (e.g., Diabetes, Hypertension, Back Pain, comma separated)")
            diet_pref = st.selectbox("Diet Preference", ["Omnivore", "Vegetarian", "Vegan"]) # New field
            
            sbtn = st.form_submit_button("Create account")

            if sbtn:
                if not su or not sp:
                    st.error("Please provide username and password")
                elif get_user_by_username(su.strip()):
                    st.error("Username already taken")
                else:
                    try:
                        uid = create_user(
                            su.strip(), sp, name=name, age=age, gender=gender,
                            height_cm=height, weight_kg=weight,
                            activity_level=activity, medical_conditions=medical,
                            diet_preference=diet_pref # Pass new field
                        )
                        st.success(f"Account created (id {uid}). Please login.")
                        st.rerun() # Rerun to clear form and show login tab
                    except Exception as e:
                        st.error(f"Error creating account: {e}")

# ---- Main App for Logged-in Users ----
else:
    user = get_user_by_id(st.session_state.user_id)
    
    # Sidebar Navigation
    st.sidebar.write(f"👋 Hello, **{user.get('name') or user.get('username')}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.rerun()
    
    menu = st.sidebar.selectbox("Menu", ["Dashboard", "Profile", "Daily Tracker", "Recommendations", "Reports"])
    
    # --- Calculate Core Metrics for re-use ---
    bmi = calculate_bmi(user['weight_kg'], user['height_cm'])
    bmr = calculate_bmr(user['weight_kg'], user['height_cm'], user['age'], user['gender'])
    calorie_need = daily_calorie_needs(bmr, user['activity_level'])

    # ---------------- Dashboard ----------------
    if menu == "Dashboard":
        st.header("Dashboard")
        st.write("Quick summary of your current health metrics.")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("BMI", f"{bmi} ({bmi_category(bmi)})", help="Body Mass Index")
        col2.metric("BMR (kcal/day)", bmr, help="Basal Metabolic Rate")
        col3.metric("Daily Calorie Goal (kcal)", calorie_need, help="Estimate of calories needed to maintain current weight.")
        
        st.markdown("---")
        st.subheader("Recent Logs")
        df = get_logs(st.session_state.user_id)
        if df.empty:
            st.info("No logs yet. Use 'Daily Tracker' to add entries.")
        else:
            st.dataframe(df.head(5), use_container_width=True)

    # ---------------- Profile ----------------
    elif menu == "Profile":
        st.header("Your Profile")
        with st.form("profile_edit"):
            name = st.text_input("Full name", value=user.get("name") or "")
            age = st.number_input("Age", 8, 120, int(user.get("age") or 25))
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male","Female","Other"].index(user.get("gender","Male")))
            height = st.number_input("Height (cm)", 80.0, 250.0, float(user.get("height_cm") or 170.0))
            weight = st.number_input("Weight (kg)", 20.0, 300.0, float(user.get("weight_kg") or 70.0))
            activity = st.selectbox("Activity level", ["Sedentary", "Lightly active", "Moderately active", "Very active", "Extra active"], index=["Sedentary", "Lightly active", "Moderately active", "Very active", "Extra active"].index(user.get("activity_level","Sedentary")))
            medical = st.text_area("Medical conditions (comma separated)", value=user.get("medical_conditions") or "")
            diet_pref = st.selectbox("Diet Preference", ["Omnivore", "Vegetarian", "Vegan"], index=["Omnivore", "Vegetarian", "Vegan"].index(user.get("diet_preference","Omnivore")))
            
            save = st.form_submit_button("Save profile")
            
            if save:
                update_profile(st.session_state.user_id, {
                    "name": name, "age": age, "gender": gender, "height_cm": height,
                    "weight_kg": weight, "activity_level": activity,
                    "medical_conditions": medical, "diet_preference": diet_pref # Include new field
                })
                st.success("Profile updated successfully!")
                st.rerun()

    # ---------------- Daily Tracker ----------------
    elif menu == "Daily Tracker":
        st.header("Daily Health Tracker")
        st.write("Log your intake and activity for today.")
        
        with st.form("log_form"):
            log_date = st.date_input("Date", date.today())
            
            st.subheader("Food & Calories")
            food_text = st.text_area("What did you eat today? (e.g., Lunch: Chicken Salad, Dinner: Pasta)", height=100)
            calories_consumed = st.number_input("Total Calories Consumed (kcal)", min_value=0.0, value=0.0)

            st.subheader("Exercise & Activity")
            exercise_text = st.text_area("What exercises did you do? (e.g., 30 min run, 45 min weightlifting)", height=100)
            calories_burned = st.number_input("Total Calories Burned (kcal)", min_value=0.0, value=0.0)

            st.subheader("Other Metrics")
            water_liters = st.number_input("Water Intake (liters)", min_value=0.0, value=2.0, step=0.1)
            sleep_hours = st.number_input("Sleep (hours)", min_value=0.0, max_value=24.0, value=7.0, step=0.5)
            notes = st.text_area("Notes/Mood")
            
            log_btn = st.form_submit_button("Add Daily Log")
            
            if log_btn:
                log_data = {
                    "log_date": log_date.isoformat(),
                    "food_text": food_text,
                    "calories_consumed": calories_consumed,
                    "exercise_text": exercise_text,
                    "calories_burned": calories_burned,
                    "water_liters": water_liters,
                    "sleep_hours": sleep_hours,
                    "notes": notes
                }
                add_log(st.session_state.user_id, log_data)
                st.success(f"Log added for {log_date.isoformat()}")

    # ---------------- Recommendations (New Tab) ----------------
    elif menu == "Recommendations":
        st.header("Personalized Health Recommendations 🌟")
        st.caption("These suggestions are based on your profile (BMI, Activity, and Medical Conditions).")

        # --- Exercise Plan ---
        st.subheader("💪 Exercise Plan")
        ex_recs = recommend_exercises(
            bmi=bmi,
            medical_conditions=user.get('medical_conditions'),
            activity_level=user.get('activity_level'),
            gender=user.get('gender')
        )
        for rec in ex_recs:
            st.markdown(f"- {rec}")
        
        st.markdown("---")

        # --- Diet Plan ---
        st.subheader("🥗 Diet Plan")
        diet_recs = recommend_diet(
            bmi=bmi,
            medical_conditions=user.get('medical_conditions'),
            calorie_target=calorie_need,
            diet_preference=user.get('diet_preference')
        )
        
        col_eat, col_avoid = st.columns(2)
        
        with col_eat:
            st.success("✅ **Foods to Eat/Focus On**")
            for item in diet_recs['eat']:
                st.markdown(f"- {item}")
        
        with col_avoid:
            st.error("❌ **Foods to Limit/Avoid**")
            for item in diet_recs['avoid']:
                st.markdown(f"- {item}")
                
        st.markdown("---")
        st.info("Disclaimer: Always consult with a qualified medical professional or dietitian before making significant changes to your diet or exercise routine.")

    # ---------------- Reports ----------------
    elif menu == "Reports":
        st.header("Health Reports & Trends")
        df = get_logs(st.session_state.user_id)
        if df.empty:
            st.warning("No logs to generate reports. Please add entries in the 'Daily Tracker'.")
        else:
            st.subheader("Log Data Table")
            df['log_date'] = pd.to_datetime(df['log_date'])
            st.dataframe(df, use_container_width=True)
            
            st.markdown("---")
            
            # Simple line chart for calories consumed
            st.subheader("Calories Consumed Trend")
            df_plot = df.set_index('log_date')[['calories_consumed']].sort_index()
            st.line_chart(df_plot)
            
            # Simple bar chart for sleep
            st.subheader("Sleep Hours Trend")
            df_sleep = df.set_index('log_date')[['sleep_hours']].sort_index()
            st.bar_chart(df_sleep)
