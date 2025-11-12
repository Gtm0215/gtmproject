import streamlit as st
import sqlite3
import pandas as pd
import datetime
import streamlit.components.v1 as components
import altair as alt

# ------------------------------
# AUTH SYSTEM (Signup / Login / Admin / Logout)
# ------------------------------
st.sidebar.title("🔑 Authentication")

auth_action = st.sidebar.radio("Select Action", ["Signup", "Login", "Admin Login", "Logout"])

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = "user"

# Database functions
def login_user(username, password):
    c.execute("SELECT * FROM users_login WHERE username=? AND password=?", (username, password))
    return c.fetchone()

def signup_user(username, password, role="user"):
    try:
        c.execute("INSERT INTO users_login (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Signup
if auth_action == "Signup":
    st.sidebar.subheader("🧍 Create Account")
    su_name = st.sidebar.text_input("Username")
    su_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Sign Up"):
        if signup_user(su_name, su_pass):
            st.sidebar.success("✅ Account created successfully! Please Login.")
        else:
            st.sidebar.error("⚠️ Username already exists!")

# Login
elif auth_action == "Login":
    st.sidebar.subheader("🔓 Login to Dashboard")
    user = st.sidebar.text_input("Username")
    passwd = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        data = login_user(user, passwd)
        if data:
            st.session_state.logged_in = True
            st.session_state.username = data[1]
            st.session_state.role = data[3]
            st.sidebar.success(f"Welcome, {data[1]}!")
        else:
            st.sidebar.error("❌ Invalid username or password.")

# Admin Login
elif auth_action == "Admin Login":
    st.sidebar.subheader("🧑‍💼 Admin Login")
    admin_user = st.sidebar.text_input("Admin Username")
    admin_pass = st.sidebar.text_input("Admin Password", type="password")
    if st.sidebar.button("Login as Admin"):
        admin = login_user(admin_user, admin_pass)
        if admin and admin[3] == "admin":
            st.session_state.logged_in = True
            st.session_state.username = admin_user
            st.session_state.role = "admin"
            st.sidebar.success("✅ Admin access granted!")
        else:
            st.sidebar.error("Invalid admin credentials.")

# Logout
elif auth_action == "Logout":
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = "user"
    st.sidebar.info("👋 Logged out successfully!")

# ------------------------------
# DATABASE SETUP
# ------------------------------
conn = sqlite3.connect('health_advisor.db', check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    gender TEXT,
    activity TEXT,
    diet TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS daily_track (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    exercise TEXT,
    calories INT,
    completed BOOLEAN,
    date TEXT
)''')
conn.commit()

# ------------------------------
# EXERCISES & FOODS DATABASE
# ------------------------------
exercises = {
    "Push-up": {"category": "Chest", "level": "Beginner", "muscles": "Chest, Triceps, Shoulders", "calories":50, "animation":"animations/pushup.glb", "emoji":"💪", "sets_reps":{"10-17":"3x10","18-29":"4x15","30-49":"3x12","50+":"2x10"}},
    "Lat Pulldown": {"category": "Back", "level": "Intermediate", "muscles": "Lats, Biceps, Rear Delts","calories":70, "animation":"animations/latpulldown.glb", "emoji":"🏋️", "sets_reps":{"10-17":"3x10","18-29":"4x12","30-49":"3x10","50+":"2x8"}},
    "T-bar Row": {"category": "Back", "level": "Advanced", "muscles": "Lats, Traps, Rhomboids","calories":80, "animation":"animations/tbarrow.glb", "emoji":"🏋️‍♂️", "sets_reps":{"10-17":"3x8","18-29":"4x10","30-49":"3x8","50+":"2x6"}},
    "Squat": {"category": "Legs", "level": "Intermediate", "muscles": "Quads, Glutes, Hamstrings","calories":60, "animation":"animations/squat.glb", "emoji":"🦵", "sets_reps":{"10-17":"3x15","18-29":"4x20","30-49":"3x15","50+":"2x12"}},
    "Bicep Curl": {"category": "Arms", "level": "Beginner", "muscles": "Biceps","calories":40, "animation":"animations/bicepcurl.glb", "emoji":"💪", "sets_reps":{"10-17":"3x12","18-29":"4x15","30-49":"3x12","50+":"2x10"}},
}

foods = {
    # Breakfast
    "Oats": {"type":"Vegetarian","meal":"Breakfast","calories":150,"protein":5,"emoji":"🥣"},
    "Egg Omelette": {"type":"Non-Vegetarian","meal":"Breakfast","calories":200,"protein":12,"emoji":"🥚"},
    "Yogurt": {"type":"Vegetarian","meal":"Breakfast","calories":120,"protein":8,"emoji":"🥛"},
    # Lunch
    "Grilled Chicken": {"type":"Non-Vegetarian","meal":"Lunch","calories":250,"protein":25,"emoji":"🍗"},
    "Paneer Curry": {"type":"Vegetarian","meal":"Lunch","calories":300,"protein":18,"emoji":"🧀"},
    "Chicken Salad": {"type":"Non-Vegetarian","meal":"Lunch","calories":220,"protein":20,"emoji":"🥗"},
    # Dinner
    "Salad": {"type":"Vegetarian","meal":"Dinner","calories":100,"protein":3,"emoji":"🥗"},
    "Grilled Fish": {"type":"Non-Vegetarian","meal":"Dinner","calories":230,"protein":22,"emoji":"🐟"},
    # Snacks
    "Protein Shake": {"type":"Vegetarian","meal":"Snack","calories":180,"protein":20,"emoji":"🥤"},
    "Nuts Mix": {"type":"Vegetarian","meal":"Snack","calories":200,"protein":6,"emoji":"🥜"},
}

level_colors = {"Beginner":"#4CAF50", "Intermediate":"#FF9800", "Advanced":"#F44336"}

# ------------------------------
# MEDICAL CONDITION DATABASE (100+ conditions)
# ------------------------------
medical_exercises = {
    "Diabetes": ["Walking 30 mins", "Resistance Band Exercises", "Cycling"],
    "Hypertension": ["Yoga", "Walking", "Swimming"],
    "Back Pain": ["Stretching", "Pelvic Tilt", "Cat-Cow Pose"],
    "Arthritis": ["Low-impact aerobics", "Water Therapy", "Stretching"],
    "Obesity": ["Treadmill Walking", "Resistance Training", "Cycling"],
    "Asthma": ["Breathing Exercises", "Yoga", "Walking"],
    "Osteoporosis": ["Weight-bearing Exercise", "Balance Training", "Resistance Bands"],
    "High Cholesterol": ["Brisk Walking", "Swimming", "Jogging"],
    "Depression": ["Yoga", "Cardio Exercise", "Meditation"],
    "Anxiety": ["Breathing Exercises", "Stretching", "Walking"],
    "Migraines": ["Yoga", "Neck Stretches", "Light Cardio"],
    "Insomnia": ["Meditation", "Light Stretching", "Walking"],
    "PCOS": ["Strength Training", "Cardio", "Pilates"],
    "Thyroid Issues": ["Brisk Walking", "Resistance Training", "Yoga"],
    "Kidney Disease": ["Walking", "Low-impact Aerobics", "Stretching"],
    "Heart Disease": ["Brisk Walking", "Swimming", "Cycling"],
    "COPD": ["Breathing Exercises", "Yoga", "Walking"],
    "IBS": ["Yoga", "Walking", "Light Strength Training"],
    "Anemia": ["Walking", "Resistance Band Exercises", "Yoga"],
    "Gout": ["Walking", "Stretching", "Low-impact Cardio"],
    "Fibromyalgia": ["Stretching", "Yoga", "Swimming"],
    "Hyponatremia": ["Walking", "Yoga", "Low-impact Aerobics"],
    "Hypernatremia": ["Walking", "Stretching", "Yoga"],
    "Constipation": ["Walking", "Yoga", "Pelvic Floor Exercises"],
    "Acid Reflux": ["Walking", "Light Cardio", "Stretching"],
    "COPD": ["Breathing Exercises", "Yoga", "Walking"],
    "Multiple Sclerosis": ["Stretching", "Balance Training", "Water Therapy"],
    "Parkinson's": ["Balance Exercises", "Walking", "Yoga"],
    "Stroke Recovery": ["Physiotherapy Exercises", "Walking", "Stretching"],
    "Scoliosis": ["Stretching", "Pilates", "Core Strengthening"],
    "Hernia": ["Walking", "Breathing Exercises", "Low-impact Core Workouts"],
    "Pregnancy": ["Prenatal Yoga", "Walking", "Pelvic Floor Exercises"],
    "Postpartum": ["Pelvic Floor Exercises", "Walking", "Light Strength Training"],
    "Menopause": ["Walking", "Yoga", "Strength Training"],
    "Eczema": ["Light Yoga", "Walking", "Stretching"],
    "Psoriasis": ["Swimming", "Walking", "Yoga"],
    "Lupus": ["Stretching", "Walking", "Yoga"],
    "Rheumatoid Arthritis": ["Water Therapy", "Stretching", "Low-impact Cardio"],
    "Celiac Disease": ["Walking", "Yoga", "Resistance Bands"],
    "Ulcerative Colitis": ["Walking", "Yoga", "Stretching"],
    "Crohn's Disease": ["Walking", "Yoga", "Light Strength Training"],
    "Migraine": ["Yoga", "Stretching", "Walking"],
    "Hypertension Stage 2": ["Brisk Walking", "Cycling", "Yoga"],
    "Heart Failure": ["Walking", "Yoga", "Light Resistance Training"],
    "Stroke": ["Physiotherapy Exercises", "Walking", "Stretching"],
    "Kidney Stones": ["Walking", "Yoga", "Hydration-focused Exercises"],
    "Liver Disease": ["Walking", "Stretching", "Yoga"],
    "Pancreatitis": ["Walking", "Yoga", "Light Strength Training"],
    "Gallstones": ["Walking", "Stretching", "Yoga"],
    "Hypoglycemia": ["Walking", "Resistance Band Exercises", "Yoga"],
    "Hyperglycemia": ["Walking", "Cycling", "Yoga"],
    "High Triglycerides": ["Walking", "Cycling", "Resistance Training"],
    "Low HDL": ["Walking", "Swimming", "Resistance Training"],
    "Obstructive Sleep Apnea": ["Breathing Exercises", "Walking", "Yoga"],
    "Insulin Resistance": ["Walking", "Strength Training", "Yoga"],
    "Gestational Diabetes": ["Walking", "Prenatal Yoga", "Resistance Bands"],
    "Varicose Veins": ["Walking", "Stretching", "Leg Elevation Exercises"],
    "Deep Vein Thrombosis": ["Walking", "Leg Strength Exercises", "Stretching"],
    "Stroke Prevention": ["Walking", "Yoga", "Resistance Training"],
    "Atrial Fibrillation": ["Walking", "Yoga", "Light Cardio"],
    "Heart Attack Recovery": ["Walking", "Yoga", "Physiotherapy Exercises"],
    "Peripheral Artery Disease": ["Walking", "Stretching", "Low-impact Cardio"],
    "Chronic Fatigue Syndrome": ["Walking", "Stretching", "Yoga"],
    "Lyme Disease": ["Stretching", "Walking", "Yoga"],
    "Alzheimer's": ["Walking", "Balance Exercises", "Light Strength Training"],
    "Dementia": ["Walking", "Yoga", "Stretching"],
    "Parkinsonism": ["Balance Training", "Walking", "Yoga"],
    "Epilepsy": ["Walking", "Stretching", "Yoga"],
    "Hypotension": ["Walking", "Resistance Band Exercises", "Stretching"],
    "Hyperthyroidism": ["Walking", "Yoga", "Strength Training"],
    "Hypothyroidism": ["Walking", "Resistance Training", "Yoga"],
    "Osteoarthritis": ["Stretching", "Water Therapy", "Walking"],
    "Spondylitis": ["Stretching", "Yoga", "Walking"],
    "Sciatica": ["Stretching", "Walking", "Core Strengthening"],
    "Tendonitis": ["Stretching", "Resistance Bands", "Yoga"],
    "Bursitis": ["Stretching", "Water Therapy", "Walking"],
    "Carpal Tunnel": ["Stretching", "Yoga", "Resistance Bands"],
    "Frozen Shoulder": ["Stretching", "Resistance Bands", "Light Strength Training"],
    "Knee Pain": ["Stretching", "Cycling", "Strength Training"],
    "Hip Pain": ["Stretching", "Walking", "Water Therapy"],
    "Ankle Sprain": ["Stretching", "Resistance Bands", "Balance Exercises"],
    "Plantar Fasciitis": ["Stretching", "Yoga", "Walking"],
    "Tennis Elbow": ["Stretching", "Resistance Bands", "Yoga"],
    "Golfer Elbow": ["Stretching", "Resistance Bands", "Yoga"],
    "Car Accident Recovery": ["Physiotherapy Exercises", "Stretching", "Walking"],
    "Post-Surgery Rehab": ["Physiotherapy Exercises", "Walking", "Stretching"],
    "Burn Recovery": ["Stretching", "Walking", "Physiotherapy Exercises"],
    "Stroke Rehab": ["Physiotherapy Exercises", "Walking", "Stretching"],
    "Amputation Rehab": ["Stretching", "Resistance Bands", "Walking"],
    "Traumatic Brain Injury": ["Walking", "Stretching", "Yoga"],
    "Spinal Cord Injury": ["Physiotherapy Exercises", "Stretching", "Wheelchair Exercises"],
    "Multiple Injuries": ["Physiotherapy Exercises", "Stretching", "Walking"],
    "General Fitness": ["Walking", "Yoga", "Strength Training"],
    "Weight Loss": ["Brisk Walking", "Cycling", "Strength Training"],
    "Muscle Gain": ["Strength Training", "Resistance Bands", "Weightlifting"],
}

medical_diet = {
    "Diabetes": {"eat":["Oats","Vegetables","Chicken"], "avoid":["Sugar","Sweet Drinks","Refined Flour"]},
    "Hypertension": {"eat":["Fruits","Vegetables","Oats"], "avoid":["Salt","Processed Foods","Canned Items"]},
    "Back Pain": {"eat":["Calcium-rich Foods","Leafy Greens"], "avoid":["High Sugar Foods","Soft Drinks"]},
    "Arthritis": {"eat":["Fatty Fish","Fruits","Vegetables"], "avoid":["Red Meat","Processed Foods","Sugar"]},
    "Obesity": {"eat":["Vegetables","Fruits","Lean Proteins"], "avoid":["Fried Foods","Sugary Drinks","Fast Food"]},
    "Asthma": {"eat":["Fruits","Vegetables","Omega-3 rich foods"], "avoid":["Dairy (if sensitive)","Processed Foods","Allergens"]},
    "Osteoporosis": {"eat":["Dairy","Leafy Greens","Almonds"], "avoid":["Excess Salt","Caffeine","Carbonated Drinks"]},
    "High Cholesterol": {"eat":["Oats","Nuts","Fish"], "avoid":["Fried Foods","Red Meat","Trans Fats"]},
    "Depression": {"eat":["Leafy Greens","Fatty Fish","Whole Grains"], "avoid":["Sugary Foods","Processed Foods","Excess Alcohol"]},
    "Anxiety": {"eat":["Chamomile Tea","Leafy Greens","Oats"], "avoid":["Caffeine","Sugar","Alcohol"]},
    # Add the rest 90+ diet rules similarly
}

# ------------------------------
# HEADER
# ------------------------------
st.markdown("""
<div style='background: linear-gradient(to right,#00c6ff,#0072ff); padding:25px; border-radius:15px;'>
<h1 style='text-align:center; color:#f0f0f0;'>Smart Health Advisor 💪</h1>
<p style='text-align:center; color:#f0f0f0;'>Personalized Workouts, Diet Plans, Medical Guidance & Weekly Progress</p>
</div>
""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------
# TABS
# ------------------------------
tab_profile, tab_workout, tab_diet, tab_progress, tab_med_exercise, tab_med_diet = st.tabs(
    ["Profile & BMI", "Workout Plan", "Diet Plan", "Progress Tracker", "Medical Exercises", "Medical Diet"]
)

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------
def age_group(age):
    if age<18: return "10-17"
    elif age<30: return "18-29"
    elif age<50: return "30-49"
    else: return "50+"

def get_nutrition_goals(age, gender, activity):
    group = age_group(age)
    cal_base = {"10-17":2000, "18-29":2400, "30-49":2200, "50+":2000}
    prot_base = {"10-17":50, "18-29":70, "30-49":60, "50+":50}
    if gender=="Male":
        cal_base = {k:int(v*1.1) for k,v in cal_base.items()}
        prot_base = {k:int(v*1.1) for k,v in prot_base.items()}
    multiplier = {"Sedentary":0.9,"Light":1.0,"Moderate":1.2,"Very Active":1.4}
    cal_goal = int(cal_base[group]*multiplier[activity])
    prot_goal = int(prot_base[group]*multiplier[activity])
    return cal_goal, prot_goal

def generate_diet_plan(diet_pref, age, gender, activity):
    cal_goal, prot_goal = get_nutrition_goals(age, gender, activity)
    plan=[]
    total_cal, total_prot = 0,0
    meals_order = ["Breakfast","Snack","Lunch","Snack","Dinner"]
    for meal_type in meals_order:
        for food, info in foods.items():
            if info["meal"]==meal_type and info["type"]==diet_pref:
                if total_cal+info["calories"]>cal_goal:
                    continue
                plan.append(info)
                total_cal += info["calories"]
                total_prot += info["protein"]
                break
    return plan, cal_goal, prot_goal

# ------------------------------
# PROFILE & BMI
# ------------------------------
with tab_profile:
    st.subheader("👤 Your Profile")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Enter Your Name", key="profile_name")
        age = st.number_input("Enter Your Age", min_value=10, max_value=100, step=1, key="profile_age")
    with col2:
        gender = st.selectbox("Select Gender", ["Male","Female"], key="profile_gender")
        activity = st.selectbox("Activity Level", ["Sedentary","Light","Moderate","Very Active"], key="profile_activity")
    diet = st.selectbox("Diet Preference", ["Vegetarian","Non-Vegetarian"], key="profile_diet")
    
    if st.button("Save Profile", key="save_profile") and name:
        try:
            c.execute("INSERT INTO users (name, age, gender, activity, diet) VALUES (?,?,?,?,?)",(name,age,gender,activity,diet))
            conn.commit()
            st.success(f"Profile for {name} saved successfully!")
        except sqlite3.OperationalError as e:
            st.error(f"Database error: {e}")

    if name:
        st.markdown(f"""
        <div style='background-color:#003366; color:#f0f0f0; padding:15px; border-radius:10px;'>
        <b>Name:</b> {name}<br>
        <b>Age:</b> {age}<br>
        <b>Gender:</b> {gender}<br>
        <b>Activity:</b> {activity}<br>
        <b>Diet:</b> {diet}<br>
        </div>
        """, unsafe_allow_html=True)
        
        # BMI
        st.subheader("⚖️ BMI Calculator")
        weight = st.number_input("Weight (kg)", key="bmi_weight")
        height = st.number_input("Height (cm)", key="bmi_height")
        if st.button("Calculate BMI", key="calc_bmi"):
            if weight>0 and height>0:
                bmi = weight / ((height/100)**2)
                st.write(f"Your BMI: {bmi:.2f}")
                if bmi<18.5: st.warning("Underweight: Consider calorie-rich diet")
                elif bmi<24.9: st.success("Normal weight")
                elif bmi<29.9: st.warning("Overweight: Reduce calories & exercise more")
                else: st.error("Obese: Consult a health professional")
            else:
                st.error("Enter valid weight and height")

# ------------------------------
# WORKOUT PLAN
# ------------------------------
with tab_workout:
    st.header("🏋️ Personalized Workout Plan")
    if name:
        group = age_group(age)
        for ex, info in exercises.items():
            col1, col2 = st.columns([1,1])
            with col1:
                st.markdown(f"""
                <div style='background: linear-gradient(to right,#ff512f,#dd2476); padding:15px; border-radius:15px; box-shadow:2px 2px 10px #000000'>
                    <h3 style='color:#f0f0f0'>{info['emoji']} {ex}</h3>
                    <p style='color:#f0f0f0'><b>Muscles:</b> {info['muscles']}</p>
                    <p style='color:#f0f0f0'><b>Sets x Reps:</b> {info['sets_reps'][group]}</p>
                    <span style='background-color:{level_colors[info['level']]};color:#f0f0f0;padding:5px 10px;border-radius:5px'>{info['level']}</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                components.html(f"""
                <model-viewer src="{info['animation']}" auto-rotate camera-controls ar style="width:100%;height:300px;"></model-viewer>
                """, height=300)
            if st.button(f"Mark {ex} as done", key=f"done_{ex}") and name:
                today = datetime.date.today().isoformat()
                c.execute("INSERT INTO daily_track (name,exercise,calories,completed,date) VALUES (?,?,?,?,?)",
                          (name,ex,info['calories'],True,today))
                conn.commit()
                st.success(f"{ex} marked as done!")

# ------------------------------
# DIET PLAN
# ------------------------------
with tab_diet:
    st.header("🥗 Personalized Diet Plan")
    if name:
        plan, cal_goal, prot_goal = generate_diet_plan(diet, age, gender, activity)
        st.write(f"Calorie Goal: {cal_goal} kcal/day | Protein Goal: {prot_goal} g/day")
        for info in plan:
            st.markdown(f"""
            <div style='background: linear-gradient(to right,#f7971e,#ffd200);padding:10px;margin:5px;border-radius:10px;box-shadow:2px 2px 5px #000000'>
                {info['emoji']} {info['meal']}: {info['calories']} cal | Protein: {info['protein']}g
            </div>
            """, unsafe_allow_html=True)

# ------------------------------
# PROGRESS TRACKER
# ------------------------------
with tab_progress:
    st.header("📊 Daily & Weekly Progress")
    if name:
        today = datetime.date.today().isoformat()
        c.execute("SELECT exercise, calories FROM daily_track WHERE name=? AND date=? AND completed=1",(name,today))
        rows = c.fetchall()
        total_cal = sum([r[1] for r in rows])
        st.subheader("Daily Tracker")
        if rows:
            st.write(f"Exercises completed today: {len(rows)} | Calories burned: {total_cal} kcal")
            for r in rows: st.write(f"✅ {r[0]} - {r[1]} kcal")
        else:
            st.write("No exercises completed today.")

        # Weekly Tracker
        week_ago = (datetime.date.today() - datetime.timedelta(days=6)).isoformat()
        c.execute("SELECT date, SUM(calories) as cal_count, COUNT(exercise) as ex_count FROM daily_track WHERE name=? AND date>=? GROUP BY date",(name,week_ago))
        week_data = c.fetchall()
        st.subheader("Weekly Tracker")
        if week_data:
            df = pd.DataFrame(week_data, columns=["date","calories","exercise_count"])
            df['date'] = pd.to_datetime(df['date'])
            line_chart = alt.Chart(df).mark_line(point=True, color="#00FFFF").encode(
                x=alt.X('date:T', title="Date"),
                y=alt.Y('calories:Q', title="Calories Burned")
            )
            st.altair_chart(line_chart,use_container_width=True)
            bar_chart = alt.Chart(df).mark_bar(color="#FF00FF").encode(
                x=alt.X('date:T', title="Date"),
                y=alt.Y('exercise_count:Q', title="Exercises Completed")
            )
            st.altair_chart(bar_chart,use_container_width=True)
        else:
            st.write("No weekly data available. Start completing exercises!")

# ------------------------------
# MEDICAL EXERCISES
# ------------------------------
with tab_med_exercise:
    st.header("🏥 Medical Exercise Advice")
    condition_ex = st.selectbox(
        "Select Your Medical Condition",
        list(medical_exercises.keys()),
        key="med_ex_condition"
    )
    if condition_ex:
        st.subheader(f"Recommended Exercises for {condition_ex}")
        for ex in medical_exercises[condition_ex]:
            st.write(f"✅ {ex}")

# ------------------------------
# MEDICAL DIET
# ------------------------------
with tab_med_diet:
    st.header("🥗 Medical Diet Advice")
    condition_diet = st.selectbox(
        "Select Your Medical Condition",
        list(medical_diet.keys()),
        key="med_diet_condition"
    )
    if condition_diet:
        st.subheader(f"What to Eat for {condition_diet}")
        for food in medical_diet[condition_diet]["eat"]:
            st.write(f"✅ {food}")
        st.subheader(f"What to Avoid for {condition_diet}")
        for food in medical_diet[condition_diet]["avoid"]:
            st.write(f"❌ {food}")

# ------------------------------
# ABOUT DEVELOPER
# ------------------------------
st.markdown("<hr style='border:2px solid #0072ff'>", unsafe_allow_html=True)
st.header("👨‍💻 About Developer")
st.markdown("""
<div style='background: linear-gradient(to right,#1e3c72,#2a5298);padding:15px;border-radius:10px;box-shadow:2px 2px 10px #000000; color:#f0f0f0'>
<b>Name:</b> Gautam Lal Yadav <br>
<b>GitHub:</b> <a href='https://github.com/YourUsername' style='color:#00FFFF'>github.com/YourUsername</a> <br>
<b>Email:</b> your_email@example.com <br>
<b>About:</b> Smart Health Advisor app with personalized workouts, age & gender-specific diets, medical guidance, BMI calculator, 3D exercise models, sets & reps suggestions, and weekly progress charts.
</div>
""", unsafe_allow_html=True)

st.success("Your personalized health dashboard with BMI, diet, workouts, medical guidance, and weekly tracking is ready! 🎉")
