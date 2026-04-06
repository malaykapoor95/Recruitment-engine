import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Trident Ops", layout="wide")

# --- 1. DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect('trident_study_v2.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        center_id TEXT, venue_id TEXT, status TEXT, 
        first_name TEXT, last_name TEXT, age_group TEXT, 
        gender TEXT, race TEXT, height_inches INTEGER, 
        hobby TEXT, session_type TEXT, 
        scheduled_date TEXT, scheduled_time TEXT,
        booking_status TEXT DEFAULT 'Scheduled'
    )''')
    conn.commit()
    conn.close()

init_db()

# --- 2. DATA UTILITIES ---
def get_data(query, params=()):
    with sqlite3.connect('trident_study_v2.db') as conn:
        return pd.read_sql_query(query, conn, params=params)

def run_query(query, params=()):
    with sqlite3.connect('trident_study_v2.db') as conn:
        conn.execute(query, params)
        conn.commit()

def get_height_tier(inches):
    if 58 <= inches <= 63: return "Tier 1: 4'10\"-5'2\""
    elif 64 <= inches <= 68: return "Tier 2: 5'3\"-5'7\""
    elif 69 <= inches <= 72: return "Tier 3: 5'8\"-6'1\""
    elif inches >= 73: return "Tier 4: 6'2\"+"
    return "Out of Range"

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("Trident Command")
# Updated Labels: Overview, Recruitment, Host
role = st.sidebar.selectbox("Access Level", ["Overview", "Recruitment", "Host"])

# --- 4. RECRUITMENT VIEW ---
if role == "Recruitment":
    st.header("Recruitment Portal: Center 1 Entry")
    existing_rep = get_data("SELECT COUNT(*) as count FROM participants WHERE status='Repeat'").iloc[0]['count']
    st.info(f"Repeat Quota Used: {existing_rep} / 435")

    with st.form("recruit_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            fn, ln = st.text_input("First Name"), st.text_input("Last Name")
            status = st.selectbox("Status", ["Fresh", "Repeat"])
            age = st.selectbox("Age Group", ["20-30", "30-40", "40-50", "50-60"])
        with col2:
            gender = st.selectbox("Gender", ["Male", "Female"])
            race = st.selectbox("Race", ["East Asian", "South Asian", "Black", "Hispanic", "White", "Middle East", "Native American"])
            height = st.number_input("Height (Inches)", 58, 85)
            session = st.selectbox("Session Type", ["1-pax", "2-3 pax", "4-5 pax"])
        with col3:
            s_date, s_time = st.date_input("Schedule Date"), st.time_input("Schedule Time")
            venue = st.selectbox("Assign to Venue", [f"House {i+1}" for i in range(10)])

        hobbies = st.multiselect("Hobbies", ["Cooking", "Music", "Games", "Housekeeping", "Exercise"])
        
        if st.form_submit_button("Submit Recruitment"):
            if status == "Repeat" and existing_rep >= 435:
                st.error("Cannot book: Repeat quota is full.")
            else:
                query = "INSERT INTO participants (center_id, venue_id, status, first_name, last_name, age_group, gender, race, height_inches, hobby, session_type, scheduled_date, scheduled_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
                run_query(query, ("Center 1", venue, status, fn, ln, age, gender, race, height, str(hobbies), session, str(s_date), str(s_time)))
                st.success(f"Recruit scheduled for {s_date} at {s_time}")
                st.rerun()

# --- 5. HOST VIEW ---
elif role == "Host":
    st.header("Host Dashboard: Venue Operations")
    selected_venue = st.selectbox("Select Your Venue", [f"House {i+1}" for i in range(10)])
    df = get_data("SELECT * FROM participants WHERE venue_id=? ORDER BY scheduled_time ASC", (selected_venue,))
    
    if not df.empty:
        for _, row in df.iterrows():
            with st.expander(f"[{row['scheduled_time']}] {row['first_name']} {row['last_name']} - {row['booking_status']}"):
                c1, c2, c3 = st.columns(3)
                if c1.button("Arrived", key=f"arr_{row['id']}"):
                    run_query("UPDATE participants SET booking_status='Arrived' WHERE id=?", (row['id'],))
                    st.rerun()
                if c2.button("Completed", key=f"comp_{row['id']}"):
                    run_query("UPDATE participants SET booking_status='Completed' WHERE id=?", (row['id'],))
                    st.rerun()
                if c3.button("No-Show", key=f"no_{row['id']}"):
                    run_query("UPDATE participants SET booking_status='No-Show' WHERE id=?", (row['id'],))
                    st.rerun()
    else: st.write("No participants scheduled.")

# --- 6. OVERVIEW VIEW ---
else:
    st.header("Global Project Overview")
    all_data = get_data("SELECT * FROM participants")
    
    if not all_data.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Recruited", len(all_data), f"{1450 - len(all_data)} left")
        m2.metric("Fresh Count", len(all_data[all_data['status']=='Fresh']), "Goal: 1015")
        m3.metric("Total Completes", len(all_data[all_data['booking_status'] == 'Completed']))

        c_left, c_right = st.columns(2)
        with c_left:
            st.subheader("Height Tier Distribution")
            all_data['Height Tier'] = all_data['height_inches'].apply(get_height_tier)
            st.bar_chart(all_data['Height Tier'].value_counts())
            
            st.subheader("Race Tracking (>10% Target)")
            st.bar_chart(all_data['race'].value_counts())

        with c_right:
            st.subheader("Age Group Breakdown")
            st.write(all_data['age_group'].value_counts())
            
            st.subheader("Session Type Mix")
            st.pie_chart(all_data['session_type'].value_counts())

        st.subheader("Hobby/Skill Quotas (>10% Target)")
        for hobby in ["Cooking", "Music", "Games", "Housekeeping", "Exercise"]:
            count = all_data['hobby'].str.contains(hobby).sum()
            st.progress(min(count/145, 1.0), text=f"{hobby}: {count} participants")
    else:
        st.info("System live. Waiting for recruitment data.")
