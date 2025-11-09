# smart_health_advisor.py

import streamlit as st
import sqlite3
import streamlit.components.v1 as components

# ------------------------------
# DATABASE SETUP
# ------------------------------
conn = sqlite3.connect('health_advisor.db')
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
    completed BOOLEAN
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
# STYLISH HEADER
# ------------------------------
st.markdown("""
<div style='background: linear-gradient(to right, #ff7e5f, #feb47b); padding: 25px; border-radius:15px;'>
    <h1 style='text-align:center;color:white;'>Smart Health Advisor 💪</h1>
    <p style='text-align:center;color:white;'>Personalized Workout & Diet Plans | Track Your Daily Progress</p>
</div>
""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------
# PROFILE INPUT
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

# Display profile
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div style='background-color:#f0f8ff;padding:15px;border-radius:10px;box-shadow:1px 1px 10px #aaa'>
<b>Name:</b> {name} <br>
<b>Age:</b> {age} <br>
<b>Gender:</b> {gender} <br>
<b>Activity:</b> {activity} <br>
<b>Diet:</b> {diet} <br>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr style='border:2px solid #feb47b'>", unsafe_allow_html=True)

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
        <div style='background: linear-gradient(to right, #00c6ff, #0072ff); padding:15px; border-radius:15px; box-shadow:2px 2px 10px #aaa'>
            <h3 style='color:white'>{info['emoji']} {ex}</h3>
            <p style='color:white'><b>Muscles:</b> {info['muscles']}</p>
            <span style='background-color:{level_colors[info['level']]};color:white;padding:5px 10px;border-radius:5px'>{info['level']}</span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        components.html(f"""
        <model-viewer src="{info['animation']}" auto-rotate camera-controls ar style="width:100%;height:300px;"></model-viewer>
        """, height=300)
    # Daily Track Button
    if st.button(f"Mark {ex} as done"):
        c.execute("INSERT INTO daily_track (name,exercise,calories,completed) VALUES (?,?,?,?)",(name,ex,info['calories'],True))
        conn.commit()
        st.success(f"{ex} marked as done!")

# ------------------------------
# DAILY TRACK SECTION
# ------------------------------
st.markdown("<hr style='border:2px solid #feb47b'>", unsafe_allow_html=True)
st.header("📊 Daily Progress Tracker")
c.execute("SELECT exercise, calories FROM daily_track WHERE name=? AND completed=1",(name,))
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
# DIET PLAN
# ------------------------------
st.markdown("<hr style='border:2px solid #feb47b'>", unsafe_allow_html=True)
st.header("🥗 Personalized Diet Plan")

diet_plan=[]
for food,info in foods.items():
    if info["type"]==diet:
        diet_plan.append(f"{info['emoji']} {food} ({info['meal']}) - {info['calories']} cal")
diet_plan=diet_plan[:10]

for meal in diet_plan:
    st.markdown(f"""
    <div style='background: linear-gradient(to right,#ffecd2,#fcb69f);padding:10px;margin:5px;border-radius:10px;box-shadow:1px 1px 5px #ccc'>
        {meal}
    </div>
    """, unsafe_allow_html=True)

# ------------------------------
# BACK DAY PLANS
# ------------------------------
st.markdown("<hr style='border:2px solid #feb47b'>", unsafe_allow_html=True)
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
st.markdown("<hr style='border:2px solid #feb47b'>", unsafe_allow_html=True)
st.header("👨‍💻 About Developer")
st.markdown("""
<div style='background-color:#e0f7fa;padding:15px;border-radius:10px;box-shadow:1px 1px 10px #aaa'>
<b>Name:</b> Gautam Lal <br>
<b>GitHub:</b> <a href='https://github.com/YourUsername'>github.com/YourUsername</a> <br>
<b>Email:</b> your_email@example.com <br>
<b>About:</b> This Smart Health Advisor app provides personalized workouts, diets, and daily tracking with interactive 3D exercise models.
</div>
""", unsafe_allow_html=True)

st.success("Your personalized health dashboard is ready! 🎉")
