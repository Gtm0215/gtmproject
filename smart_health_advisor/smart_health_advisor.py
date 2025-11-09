# smart_health_advisor.py

import streamlit as st
import sqlite3
import pandas as pd
import datetime
import streamlit.components.v1 as components
import altair as alt

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
    "Oats": {"type":"Vegetarian","meal":"Breakfast","calories":150,"protein":5,"emoji":"🥣"},
    "Egg Omelette": {"type":"Non-Vegetarian","meal":"Breakfast","calories":200,"protein":12,"emoji":"🥚"},
    "Grilled Chicken": {"type":"Non-Vegetarian","meal":"Lunch","calories":250,"protein":25,"emoji":"🍗"},
    "Paneer Curry": {"type":"Vegetarian","meal":"Lunch","calories":300,"protein":18,"emoji":"🧀"},
    "Salad": {"type":"Vegetarian","meal":"Dinner","calories":100,"protein":3,"emoji":"🥗"},
    "Protein Shake": {"type":"Vegetarian","meal":"Snack","calories":180,"protein":20,"emoji":"🥤"},
    "Yogurt": {"type":"Vegetarian","meal":"Breakfast","calories":120,"protein":8,"emoji":"🥛"},
    "Chicken Salad": {"type":"Non-Vegetarian","meal":"Lunch","calories":220,"protein":20,"emoji":"🥗"},
}

level_colors = {"Beginner":"#4CAF50", "Intermediate":"#FF9800", "Advanced":"#F44336"}

# ------------------------------
# HEADER
# ------------------------------
st.markdown("""
<div style='background: linear-gradient(to right,#00c6ff,#0072ff); padding:25px; border-radius:15px;'>
<h1 style='text-align:center; color:#f0f0f0;'>Smart Health Advisor 💪</h1>
<p style='text-align:center; color:#f0f0f0;'>Personalized Workouts, Diet Plans, BMI & Weekly Progress</p>
</div>
""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------
# TABS FOR SECTIONS
# ------------------------------
tab_profile, tab_workout, tab_diet, tab_progress = st.tabs(["Profile & BMI", "Workout Plan", "Diet Plan", "Progress Tracker"])

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------
def age_group(age):
    if age<18: return "10-17"
    elif age<30: return "18-29"
    elif age<50: return "30-49"
    else: return "50+"

def get_calories_protein(age, activity):
    group = age_group(age)
    base = {"10-17":2000, "18-29":2400, "30-49":2200, "50+":2000}
    protein = {"10-17":50, "18-29":70, "30-49":60, "50+":50}
    multiplier = {"Sedentary":0.9,"Light":1.0,"Moderate":1.2,"Very Active":1.4}
    cal = int(base[group]*multiplier[activity])
    prot = int(protein[group]*multiplier[activity])
    return cal, prot

# ------------------------------
# PROFILE & BMI
# ------------------------------
with tab_profile:
    st.subheader("👤 Your Profile")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Enter Your Name")
        age = st.number_input("Enter Your Age", min_value=10, max_value=100, step=1)
    with col2:
        gender = st.selectbox("Select Gender", ["Male","Female"])
        activity = st.selectbox("Activity Level", ["Sedentary","Light","Moderate","Very Active"])
    diet = st.selectbox("Diet Preference", ["Vegetarian","Non-Vegetarian"])
    
    if st.button("Save Profile") and name:
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
        
        # BMI Calculator
        st.subheader("⚖️ BMI Calculator")
        weight = st.number_input("Weight (kg)")
        height = st.number_input("Height (cm)")
        
        if st.button("Calculate BMI"):
            if weight>0 and height>0:
                bmi = weight / ((height/100)**2)
                st.write(f"Your BMI: {bmi:.2f}")
                if bmi<18.5:
                    st.warning("Underweight: Consider a calorie-rich diet")
                elif bmi<24.9:
                    st.success("Normal weight")
                elif bmi<29.9:
                    st.warning("Overweight: Consider reducing calories and exercising more")
                else:
                    st.error("Obese: Consult a health professional")
            else:
                st.error("Please enter valid weight and height")

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
            if st.button(f"Mark {ex} as done") and name:
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
        cal_goal, prot_goal = get_calories_protein(age, activity)
        st.write(f"Calorie Goal: {cal_goal} kcal/day | Protein Goal: {prot_goal} g/day")
        total_cal, total_prot = 0,0
        for food, info in foods.items():
            if info["type"]==diet and total_cal<cal_goal:
                st.markdown(f"""
                <div style='background: linear-gradient(to right,#f7971e,#ffd200);padding:10px;margin:5px;border-radius:10px;box-shadow:2px 2px 5px #000000'>
                    {info['emoji']} {food} ({info['meal']}) - {info['calories']} cal | Protein: {info['protein']}g
                </div>
                """, unsafe_allow_html=True)
                total_cal+=info['calories']
                total_prot+=info['protein']

# ------------------------------
# PROGRESS TRACKER
# ------------------------------
with tab_progress:
    st.header("📊 Daily & Weekly Progress")
    if name:
        # Daily Tracker
        today = datetime.date.today().isoformat()
        c.execute("SELECT exercise, calories FROM daily_track WHERE name=? AND date=? AND completed=1",(name,today))
        rows = c.fetchall()
        total_cal = sum([r[1] for r in rows])
        st.subheader("Daily Tracker")
        if rows:
            st.write(f"Exercises completed today: {len(rows)}")
            st.write(f"Calories burned today: {total_cal} kcal")
            for r in rows:
                st.write(f"✅ {r[0]} - {r[1]} kcal")
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
# ABOUT DEVELOPER
# ------------------------------
st.markdown("<hr style='border:2px solid #0072ff'>", unsafe_allow_html=True)
st.header("👨‍💻 About Developer")
st.markdown("""
<div style='background: linear-gradient(to right,#1e3c72,#2a5298);padding:15px;border-radius:10px;box-shadow:2px 2px 10px #000000; color:#f0f0f0'>
<b>Name:</b> Gautam Lal <br>
<b>GitHub:</b> <a href='https://github.com/YourUsername' style='color:#00FFFF'>github.com/YourUsername</a> <br>
<b>Email:</b> your_email@example.com <br>
<b>About:</b> Smart Health Advisor app with personalized workouts, age-specific diets, BMI calculator, 3D exercise models, sets & reps suggestions, and weekly progress charts.
</div>
""", unsafe_allow_html=True)

st.success("Your personalized health dashboard with BMI, diet, workouts, and weekly tracking is ready! 🎉")
