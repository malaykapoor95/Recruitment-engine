import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Trident Ops", layout="wide")

# --- 1. DATABASE INITIALIZATION (V2) ---
def init_db():
    # Renamed to v2 to force a fresh table with the new date/time columns
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

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("Trident Command")
role = st.sidebar.selectbox("Access Level", ["Admin (Trident)", "Vendor (Shapard)", "Client (Tata Elxsi)"])

# --- 4. VENDOR VIEW (Recruitment Portal) ---
if role == "Vendor (Shapard)":
    st.header("Center 1: Recruitment Entry")
    
    # Track Repeat Cap (Target max 435 per center) [cite: 5]
    existing = get_data("SELECT COUNT(*) as count FROM participants WHERE status='Repeat'").iloc[0]['count']
    st.info(f"Repeat Participants: {existing} / 435 used")

    with st.form("recruit_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            fn = st.text_input("First Name")
            ln = st.text_input("Last Name")
            status = st.selectbox("Status", ["Fresh", "Repeat"]) # [cite: 5]
            age = st.selectbox("Age Group", ["20-30", "30-40", "40-50", "50-60"])
        with col2:
            gender = st.selectbox("Gender", ["Male", "Female"])
            race = st.selectbox("Race", ["East Asian", "South Asian", "Black", "Hispanic", "White", "Middle East", "Native American"])
            height = st.number_input("Height (Inches)", 58, 80)
            session = st.selectbox("Session Type", ["1-pax", "2-3 pax", "4-5 pax"]) # [cite: 24-26]
        with col3:
            # NEW: Scheduling Fields
            s_date = st.date_input("Schedule Date")
            s_time = st.time_input("Schedule Time")
            venue = st.selectbox("Assign to Venue", [f"House {i+1}" for i in range(10)])

        hobbies = st.multiselect("Hobbies", ["Cooking", "Music", "Games", "Housekeeping", "Exercise"])
        
        if st.form_submit_button("Book Participant"):
            if status == "Repeat" and existing >= 435:
                st.error("Repeat quota full!")
            else:
                query = """INSERT INTO participants 
                           (center_id, venue_id, status, first_name, last_name, age_group, 
                           gender, race, height_inches, hobby, session_type, scheduled_date, scheduled_time) 
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"""
                run_query(query, ("Center 1", venue, status, fn, ln, age, gender, race, height, str(hobbies), session, str(s_date), str(s_time)))
                st.success(f"Participant booked for {s_date} at {s_time}")
                st.rerun()

# --- 5. CLIENT VIEW (Venue Staff) ---
elif role == "Client (Tata Elxsi)":
    st.header("Venue Check-In Dashboard")
    selected_venue = st.selectbox("Select Your Venue", [f"House {i+1}" for i in range(10)])
    
    # Sorted by time so staff knows who is next
    df = get_data("SELECT id, first_name, last_name, scheduled_time, session_type, booking_status FROM participants WHERE venue_id=? ORDER BY scheduled_time ASC", (selected_venue,))
    
    if not df.empty:
        for _, row in df.iterrows():
            with st.expander(f"[{row['scheduled_time']}] {row['first_name']} {row['last_name']} - {row['booking_status']}"):
                st.write(f"Session Type: {row['session_type']}")
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
    else:
        st.write("No participants scheduled for this house.")

# --- 6. ADMIN VIEW (Trident Master) ---
else:
    st.header("Global Project Overview")
    all_data = get_data("SELECT * FROM participants")
    
    if not all_data.empty:
        col_a, col_b = st.columns(2)
        col_a.metric("Total Participants", len(all_data), delta=f"{1450 - len(all_data)} remaining")
        col_b.metric("Total Completes", len(all_data[all_data['booking_status'] == 'Completed']))
        
        st.subheader("Race Distribution Tracking")
        st.bar_chart(all_data['race'].value_counts())
    else:
        st.info("Waiting for first recruitment entry...")
