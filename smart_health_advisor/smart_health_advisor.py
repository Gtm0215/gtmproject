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

# Create tables if they don't exist
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
    # Add 100+ exercises similarly
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
    # Add 100+ foods similarly
}

# ------------------------------
# USER INPUT
# ------------------------------
st.title("Smart Health Advisor 💪")

name = st.text_input("Enter Your Name")
age = st.number_input("Enter Your Age", min_value=10, max_value=100, step=1)
gender = st.selectbox("Select Gender", ["Male", "Female"])
activity = st.selectbox("Select Activity Level", ["Sedentary", "Light", "Moderate", "Very Active"])
diet = st.selectbox("Diet Preference", ["Vegetarian", "Non-Vegetarian"])

if st.button("Save Profile"):
    c.execute("INSERT INTO users (name, age, gender, activity, diet) VALUES (?, ?, ?, ?, ?)", 
              (name, age, gender, activity, diet))
    conn.commit()
    st.success("Profile saved successfully!")

# ------------------------------
# WORKOUT GENERATOR
# ------------------------------
st.header("🏋️ Personalized Workout Plan")

def generate_workout(gender, activity):
    plan = []
    for ex_name, ex_info in exercises.items():
        # Simple logic for activity level
        if activity == "Sedentary" and ex_info["level"] == "Beginner":
            plan.append(ex_name)
        elif activity == "Light" and ex_info["level"] in ["Beginner", "Intermediate"]:
            plan.append(ex_name)
        elif activity in ["Moderate", "Very Active"]:
            plan.append(ex_name)
    return plan[:10]  # Limit to 10 exercises for simplicity

workout_plan = generate_workout(gender, activity)

for ex in workout_plan:
    ex_info = exercises[ex]
    st.subheader(ex)
    st.write(f"**Muscles targeted:** {ex_info['muscles']}")
    st.write(f"**Difficulty:** {ex_info['level']}")
    # Display 3D animation
    components.html(f"""
    <model-viewer src="{ex_info['animation']}" auto-rotate camera-controls ar
        style="width: 100%; height: 400px;"></model-viewer>
    """, height=400)

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
    st.write(meal)

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
        st.write(f"{ex} - {ex_info['muscles']}")
        components.html(f"""
        <model-viewer src="{ex_info['animation']}" auto-rotate camera-controls ar
            style="width: 100%; height: 400px;"></model-viewer>
        """, height=400)

st.subheader("Back Day 2")
for ex in back_day2:
    if ex in exercises:
        ex_info = exercises[ex]
        st.write(f"{ex} - {ex_info['muscles']}")
        components.html(f"""
        <model-viewer src="{ex_info['animation']}" auto-rotate camera-controls ar
            style="width: 100%; height: 400px;"></model-viewer>
        """, height=400)

st.success("Your personalized workout and diet plan is ready! 🎉")
