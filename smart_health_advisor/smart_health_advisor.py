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
    "Yogurt": {"type":"Vegetarian","meal":"Breakfast","calories":120,"protein":8,"emoji":"🥛"},
    "Grilled Chicken": {"type":"Non-Vegetarian","meal":"Lunch","calories":250,"protein":25,"emoji":"🍗"},
    "Paneer Curry": {"type":"Vegetarian","meal":"Lunch","calories":300,"protein":18,"emoji":"🧀"},
    "Chicken Salad": {"type":"Non-Vegetarian","meal":"Lunch","calories":220,"protein":20,"emoji":"🥗"},
    "Salad": {"type":"Vegetarian","meal":"Dinner","calories":100,"protein":3,"emoji":"🥗"},
    "Grilled Fish": {"type":"Non-Vegetarian","meal":"Dinner","calories":230,"protein":22,"emoji":"🐟"},
    "Protein Shake": {"type":"Vegetarian","meal":"Snack","calories":180,"protein":20,"emoji":"🥤"},
    "Nuts Mix": {"type":"Vegetarian","meal":"Snack","calories":200,"protein":6,"emoji":"🥜"},
}

level_colors = {"Beginner":"#4CAF50", "Intermediate":"#FF9800", "Advanced":"#F44336"}

# ------------------------------
# MEDICAL CONDITION DATABASE (100+)
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
    # Add rest of 100+ conditions similarly...
}

medical_diet = {
    "Diabetes": {"eat":["Oats","Vegetables","Chicken"], "avoid":["Sugar","Sweet Drinks","Refined Flour"]},
    "Hypertension": {"eat":["Fruits","Vegetables","Oats"], "avoid":["Salt","Processed Foods","Canned Items"]},
    "Back Pain": {"eat":["Calcium-rich Foods","Leafy Greens"], "avoid":["High Sugar Foods","Soft Drinks"]},
    "Arthritis": {"eat":["Fatty Fish","Fruits","Vegetables"], "avoid":["Red Meat","Processed Foods","Sugar"]},
    "Obesity": {"eat":["Vegetables","Fruits","Lean Proteins"], "avoid":["Fried Foods","Sugary Drinks","Fast Food"]},
    # Add rest of 100+ diets similarly...
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
# (rest of your code remains unchanged)
# ------------------------------
