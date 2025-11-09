# smart_health_advisor.py

import streamlit as st
import pandas as pd
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
conn.commit()

# ------------------------------
# EXERCISES DATABASE
# ------------------------------
exercises = {
    "Push-up": {"category": "Chest", "level": "Beginner", "muscles": "Chest, Triceps, Shoulders", "animation": "animations/pushup.glb"},
    "Lat Pulldown": {"category": "Back", "level": "Intermediate", "muscles": "Lats, Biceps, Rear Delts", "animation": "animations/latpulldown.glb"},
    "T-bar Row": {"category": "Back", "level": "Advanced", "muscles": "Lats, Traps, Rhomboids", "animation": "animations/tbarrow.glb"},
    "Squat": {"category": "Legs", "level": "Intermediate", "muscles": "Quads, Glutes, Hamstrings", "animation": "animations/squat.glb"},
    "Bicep Curl": {"category": "Arms", "level": "Beginner", "muscles": "Biceps", "animation": "animations/bicepcurl.glb"},
}

# ------------------------------
# FOOD DATABASE
# ------------------------------
foods = {
    "Oats": {"type": "Vegetarian", "meal": "Breakfast", "calories": 150},
    "Egg Omelette": {"type": "Non-Vegetarian", "meal": "Breakfast", "calories": 200},
    "Grilled Chicken": {"type": "Non-Vegetarian", "meal": "Lunch", "calories": 250},
    "Paneer Curry": {"type": "Vegetarian", "meal": "Lunch", "calories": 300},
    "Salad": {"type": "Vegetarian", "meal": "Dinner", "calories": 100},
}

# ------------------------------
# STYLISH HEADER
# ------------------------------
st.markdown("""
<div style='background-color:#4CAF50;padding:20px;border-radius:10px'>
    <h1 style='color:white;text-align:center;'>Smart Health Advisor 💪</h1>
    <p style='color:white;text-align:center;'>Personalized Workout & Diet Plans with 3D Exercise Demonstrations</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------
# USER INPUT
# ------------------------------
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Enter Your Name")
    age = st.number_input("Enter Your Age", min_value=10, max_value=100, step=1)
with col2:
    gender = st.selectbox("Select Gender", ["Male", "Female"])
    activity = st.selectbox("Select Activity Level", ["Sedentary", "Light", "Moderate", "Very Active"])

diet = st.selectbox("Diet Preference", ["Vegetarian", "Non-Vegetarian"])

if st.button("Save Profile"):
    c.execute("INSERT INTO users (name, age, gender, activity, diet) VALUES (?, ?, ?, ?, ?)", 
              (name, age, gender, activity, diet))
    conn.commit()
    st.success("Profile saved successfully!")

st.markdown("<hr style='border:2px solid #4CAF50'>", unsafe_allow_html=True)

# ------------------------------
# WORKOUT GENERATOR
# ------------------------------
st.header("🏋️ Personalized Workout Plan")

def generate_workout(gender, activity):
    plan = []
    for ex_name, ex_info in exercises.items():
        if activity == "Sedentary" and ex_info["level"] == "Beginner":
            plan.append(ex_name)
        elif activity == "Light" and ex_info["level"] in ["Beginner", "Intermediate"]:
            plan.append(ex_name)
        elif activity in ["Moderate", "Very Active"]:
            plan.append(ex_name)
    return plan[:10]

workout_plan = generate_workout(gender, activity)
level_colors = {"Beginner":"#4CAF50", "Intermediate":"#FF9800", "Advanced":"#F44336"}

for ex in workout_plan:
    ex_info = exercises[ex]
    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown(f"""
        <div style='background-color:#f0f0f5;padding:15px;margin:10px;border-radius:10px;box-shadow:2px 2px 10px #aaa'>
            <h3>{ex}</h3>
            <p><b>Muscles targeted:</b> {ex_info['muscles']}</p>
            <span style='background-color:{level_colors[ex_info['level']]};color:white;padding:5px 10px;border-radius:5px'>
                {ex_info['level']}
            </span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        components.html(f"""
        <model-viewer src="{ex_info['animation']}" auto-rotate camera-controls ar
            style="width: 100%; height: 300px;"></model-viewer>
        """, height=300)

st.markdown("<hr style='border:2px solid #4CAF50'>", unsafe_allow_html=True)

# ------------------------------
# DIET PLAN GENERATOR
# ------------------------------
st.header("🥗 Personalized Diet Plan")

def generate_diet(diet_pref):
    plan = []
    for food_name, food_info in foods.items():
        if food_info["type"] == diet_pref:
            plan.append(f"{food_name} ({food_info['meal']}) - {food_info['calories']} cal")
    return plan[:10]

diet_plan = generate_diet(diet)

for meal in diet_plan:
    st.markdown(f"""
    <div style='background-color:#fff3e0;padding:10px;margin:5px;border-radius:10px;box-shadow:1px 1px 5px #ccc'>
        {meal}
    </div>
    """ , unsafe_allow_html=True)

st.markdown("<hr style='border:2px solid #4CAF50'>", unsafe_allow_html=True)

# ------------------------------
# BACK DAY PLANS
# ------------------------------
st.header("Back Day Plans")
back_day1 = ["Pull-up", "Lat Pulldown", "Seated Row"]
back_day2 = ["T-bar Row", "Deadlift", "Face Pull"]

st.subheader("Back Day 1")
for ex in back_day1:
    if ex in exercises:
        ex_info = exercises[ex]
        col1, col2 = st.columns([1,1])
        with col1:
            st.write(f"{ex} - {ex_info['muscles']}")
        with col2:
            components.html(f"""
            <model-viewer src="{ex_info['animation']}" auto-rotate camera-controls ar
                style="width: 100%; height: 300px;"></model-viewer>
            """, height=300)

st.subheader("Back Day 2")
for ex in back_day2:
    if ex in exercises:
        ex_info = exercises[ex]
        col1, col2 = st.columns([1,1])
        with col1:
            st.write(f"{ex} - {ex_info['muscles']}")
        with col2:
            components.html(f"""
            <model-viewer src="{ex_info['animation']}" auto-rotate camera-controls ar
                style="width: 100%; height: 300px;"></model-viewer>
            """, height=300)

st.success("Your personalized workout and diet plan is ready! 🎉")
