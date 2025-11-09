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
    "Push-up": {"category": "Chest", "level": "Beginner", "muscles": "Chest, Triceps, Shoulders", "calories":50, "animation":"animations/pushup.glb", "emoji":"💪"},
    "Lat Pulldown": {"category": "Back", "level": "Intermediate", "muscles": "Lats, Biceps, Rear Delts","calories":70, "animation":"animations/latpulldown.glb", "emoji":"🏋️"},
    "T-bar Row": {"category": "Back", "level": "Advanced", "muscles": "Lats, Traps, Rhomboids","calories":80, "animation":"animations/tbarrow.glb", "emoji":"🏋️‍♂️"},
    "Squat": {"category": "Legs", "level": "Intermediate", "muscles": "Quads, Glutes, Hamstrings","calories":60, "animation":"animations/squat.glb", "emoji":"🦵"},
    "Bicep Curl": {"category": "Arms", "level": "Beginner", "muscles": "Biceps","calories":40, "animation":"animations/bicepcurl.glb", "emoji":"💪"},
}

foods = {
    "Oats": {"type":"Vegetarian","meal":"Breakfast","calories":150,"emoji":"🥣"},
    "Egg Omelette": {"type":"Non-Vegetarian","meal":"Breakfast","calories":200,"emoji":"🥚"},
    "Grilled Chicken": {"type":"Non-Vegetarian","meal":"Lunch","calories":250,"emoji":"🍗"},
    "Paneer Curry": {"type":"Vegetarian","meal":"Lunch","calories":300,"emoji":"🧀"},
    "Salad": {"type":"Vegetarian","meal":"Dinner","calories":100,"emoji":"🥗"},
}

level_colors = {"Beginner":"#4CAF50", "Intermediate":"#FF9800", "Advanced":"#F44336"}

# ------------------------------
# HEADER
# ------------------------------
st.markdown("""
<div style='background: linear-gradient(to right,#00c6ff,#0072ff); padding:25px; border-radius:15px;'>
<h1 style='text-align:center; color:#f0f0f0;'>Smart Health Advisor 💪</h1>
<p style='text-align:center; color:#f0f0f0;'>Personalized Workouts, Diet Plans & Weekly Progress Tracking</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------
# PROFILE SECTION
# ------------------------------
st.subheader("👤 Your Profile")
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Enter Your Name")
    age = st.number_input("Enter Your Age", min_value=10, max_value=100, step=1)
with col2:
    gender = st.selectbox("Select Gender", ["Male","Female"])
    activity = st.selectbox("Activity Level", ["Sedentary","Light","Moderate","Very Active"])
diet = st.selectbox("Diet Preference", ["Vegetarian","Non-Vegetarian"])

if st.button("Save Profile"):
    c.execute("INSERT INTO users (name, age, gender, activity, diet) VALUES (?,?,?,?,?)",(name,age,gender,activity,diet))
    conn.commit()
    st.success(f"Profile for {name} saved successfully!")

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

st.markdown("<hr style='border:2px solid #0072ff'>", unsafe_allow_html=True)

# ------------------------------
# WORKOUT GENERATOR
# ------------------------------
st.header("🏋️ Personalized Workout Plan")
def generate_workout(activity):
    plan=[]
    for ex,info in exercises.items():
        if activity=="Sedentary" and info["level"]=="Beginner":
            plan.append(ex)
        elif activity=="Light" and info["level"] in ["Beginner","Intermediate"]:
            plan.append(ex)
        elif activity in ["Moderate","Very Active"]:
            plan.append(ex)
    return plan[:10]

workout_plan = generate_workout(activity)

for ex in workout_plan:
    info = exercises[ex]
    col1,col2 = st.columns([1,1])
    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(to right,#ff512f,#dd2476); padding:15px; border-radius:15px; box-shadow:2px 2px 10px #000000'>
            <h3 style='color:#f0f0f0'>{info['emoji']} {ex}</h3>
            <p style='color:#f0f0f0'><b>Muscles:</b> {info['muscles']}</p>
            <span style='background-color:{level_colors[info['level']]};color:#f0f0f0;padding:5px 10px;border-radius:5px'>{info['level']}</span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        components.html(f"""
        <model-viewer src="{info['animation']}" auto-rotate camera-controls ar style="width:100%;height:300px;"></model-viewer>
        """, height=300)
    if st.button(f"Mark {ex} as done"):
        today = datetime.date.today().isoformat()
        c.execute("INSERT INTO daily_track (name,exercise,calories,completed,date) VALUES (?,?,?,?,?)",
                  (name,ex,info['calories'],True,today))
        conn.commit()
        st.success(f"{ex} marked as done!")

# ------------------------------
# DAILY TRACKER
# ------------------------------
st.markdown("<hr style='border:2px solid #0072ff'>", unsafe_allow_html=True)
st.header("📊 Daily Progress Tracker")
today = datetime.date.today().isoformat()
c.execute("SELECT exercise, calories FROM daily_track WHERE name=? AND date=? AND completed=1",(name,today))
rows = c.fetchall()
total_cal = sum([r[1] for r in rows])
if rows:
    st.write(f"Exercises completed today: {len(rows)}")
    st.write(f"Calories burned today: {total_cal} kcal")
    for r in rows:
        st.write(f"✅ {r[0]} - {r[1]} kcal")
else:
    st.write("No exercises completed yet.")

# ------------------------------
# WEEKLY TRACKING
# ------------------------------
st.markdown("<hr style='border:2px solid #0072ff'>", unsafe_allow_html=True)
st.header("📈 Weekly Progress Tracker")
week_ago = (datetime.date.today() - datetime.timedelta(days=6)).isoformat()
c.execute("SELECT date, SUM(calories) as cal_count, COUNT(exercise) as ex_count FROM daily_track WHERE name=? AND date>=? GROUP BY date",(name,week_ago))
week_data = c.fetchall()

if week_data:
    df = pd.DataFrame(week_data, columns=["date","calories","exercise_count"])
    df['date'] = pd.to_datetime(df['date'])
    # Calories burned line chart
    line_chart = alt.Chart(df).mark_line(point=True, color="#00FFFF").encode(
        x=alt.X('date:T', title="Date"),
        y=alt.Y('calories:Q', title="Calories Burned")
    )
    st.altair_chart(line_chart,use_container_width=True)
    # Exercises per day bar chart
    bar_chart = alt.Chart(df).mark_bar(color="#FF00FF").encode(
        x=alt.X('date:T', title="Date"),
        y=alt.Y('exercise_count:Q', title="Exercises Completed")
    )
    st.altair_chart(bar_chart,use_container_width=True)
else:
    st.write("No weekly data available. Start completing exercises!")

# ------------------------------
# DIET PLAN
# ------------------------------
st.markdown("<hr style='border:2px solid #0072ff'>", unsafe_allow_html=True)
st.header("🥗 Personalized Diet Plan")
diet_plan=[]
for food,info in foods.items():
    if info["type"]==diet:
        diet_plan.append(f"{info['emoji']} {food} ({info['meal']}) - {info['calories']} cal")
diet_plan=diet_plan[:10]
for meal in diet_plan:
    st.markdown(f"""
    <div style='background: linear-gradient(to right,#f7971e,#ffd200);padding:10px;margin:5px;border-radius:10px;box-shadow:2px 2px 5px #000000'>
        {meal}
    </div>
    """, unsafe_allow_html=True)

# ------------------------------
# BACK DAY PLANS
# ------------------------------
st.markdown("<hr style='border:2px solid #0072ff'>", unsafe_allow_html=True)
st.header("💪 Back Day Plans")
back_day1 = ["Pull-up","Lat Pulldown","Seated Row"]
back_day2 = ["T-bar Row","Deadlift","Face Pull"]

st.subheader("Back Day 1")
for ex in back_day1:
    if ex in exercises:
        info = exercises[ex]
        col1,col2 = st.columns([1,1])
        with col1:
            st.write(f"{info['emoji']} {ex} - {info['muscles']}")
        with col2:
            components.html(f"""
            <model-viewer src="{info['animation']}" auto-rotate camera-controls ar style="width:100%;height:300px;"></model-viewer>
            """, height=300)

st.subheader("Back Day 2")
for ex in back_day2:
    if ex in exercises:
        info = exercises[ex]
        col1,col2 = st.columns([1,1])
        with col1:
            st.write(f"{info['emoji']} {ex} - {info['muscles']}")
        with col2:
            components.html(f"""
            <model-viewer src="{info['animation']}" auto-rotate camera-controls ar style="width:100%;height:300px;"></model-viewer>
            """, height=300)

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
<b>About:</b> Smart Health Advisor app with personalized workouts, diets, 3D exercise models, daily and weekly tracking graphs.
</div>
""", unsafe_allow_html=True)

st.success("Your personalized health dashboard with weekly tracking is ready! 🎉")
