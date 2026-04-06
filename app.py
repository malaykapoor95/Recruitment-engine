import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Trident Ops", layout="wide")

# --- 1. DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect('trident_ops.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        center_id TEXT, venue_id TEXT, status TEXT, 
        first_name TEXT, last_name TEXT, age_group TEXT, 
        gender TEXT, race TEXT, height_inches INTEGER, 
        hobby TEXT, session_type TEXT, 
        booking_status TEXT DEFAULT 'Scheduled'
    )''')
    conn.commit()
    conn.close()

init_db()

# --- 2. DATA UTILITIES ---
def get_data(query, params=()):
    with sqlite3.connect('trident_ops.db') as conn:
        return pd.read_sql_query(query, conn, params=params)

def run_query(query, params=()):
    with sqlite3.connect('trident_ops.db') as conn:
        conn.execute(query, params)
        conn.commit()

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("Trident Command")
role = st.sidebar.selectbox("Access Level", ["Admin (Trident)", "Vendor (Shapard)", "Client (Tata Elxsi)"])

# --- 4. VENDOR VIEW (Recruitment Portal) ---
if role == "Vendor (Shapard)":
    st.header("Center 1: Recruitment Entry")
    
    # Track Repeat Cap 
    existing = get_data("SELECT COUNT(*) as count FROM participants WHERE status='Repeat'").iloc[0]['count']
    st.info(f"Repeat Participants: {existing} / 435 used")

    with st.form("recruit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fn = st.text_input("First Name")
            ln = st.text_input("Last Name")
            status = st.selectbox("Status", ["Fresh", "Repeat"])
            age = st.selectbox("Age Group", ["20-30", "30-40", "40-50", "50-60"]) # [cite: 8-11]
        with col2:
            gender = st.selectbox("Gender", ["Male", "Female"]) # [cite: 13-14]
            race = st.selectbox("Race", ["East Asian", "South Asian", "Black", "Hispanic", "White", "Middle East", "Native American"]) # [cite: 34-40]
            height = st.number_input("Height (Inches)", 58, 80) # [cite: 16-20]
            session = st.selectbox("Session Type", ["1-pax", "2-3 pax", "4-5 pax"]) # [cite: 24-26]
        
        hobbies = st.multiselect("Hobbies", ["Cooking", "Music", "Games", "Housekeeping", "Exercise"]) # [cite: 28-32]
        venue = st.selectbox("Assign to Venue", [f"House {i+1}" for i in range(10)])

        if st.form_submit_button("Book Participant"):
            if status == "Repeat" and existing >= 435:
                st.error("Repeat quota full!")
            else:
                run_query("INSERT INTO participants (center_id, venue_id, status, first_name, last_name, age_group, gender, race, height_inches, hobby, session_type) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                          ("Center 1", venue, status, fn, ln, age, gender, race, height, str(hobbies), session))
                st.success("Booked!")
                st.rerun()

# --- 5. CLIENT VIEW (Venue Staff) ---
elif role == "Client (Tata Elxsi)":
    st.header("Venue Check-In Dashboard")
    selected_venue = st.selectbox("Select Your Venue", [f"House {i+1}" for i in range(10)])
    
    df = get_data("SELECT id, first_name, last_name, session_type, booking_status FROM participants WHERE venue_id=?", (selected_venue,))
    
    if not df.empty:
        for _, row in df.iterrows():
            with st.expander(f"{row['first_name']} {row['last_name']} - {row['booking_status']}"):
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
        st.metric("Total Completes", len(all_data[all_data['booking_status'] == 'Completed']))
        st.subheader("Race Distribution (Target >10% each)") # [cite: 33-40]
        st.bar_chart(all_data['race'].value_counts())
    else:
        st.info("Waiting for first recruitment entry...")
