import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Trident Command Center", layout="wide")

# Simple Role-Based Login (In a real app, use streamlit-authenticator)
user_role = st.sidebar.selectbox("Select User Role", ["Trident Admin", "Vendor (Shapard)", "Client (Tata Elxsi)"])

def get_data(query, params=()):
    conn = sqlite3.connect('trident_ops.db')
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# --- VIEW 1: VENDOR DASHBOARD ---
if user_role == "Vendor (Shapard)":
    st.header("Recruitment Portal - Center 1 (Oklahoma)")
    # Show real-time quota progress
    df = get_data("SELECT race, status FROM participants WHERE center_id='Center 1'")
    st.write(f"Total Recruited: {len(df)} / 1450") [cite: 164]
    
    with st.form("recruit_form"):
        st.subheader("New Participant Entry")
        f_name = st.text_input("First Name")
        l_name = st.text_input("Last Name")
        status = st.selectbox("Status", ["Fresh", "Repeat"])
        race = st.selectbox("Race", ["East Asian", "South Asian", "Black", "Hispanic", "White", "Middle East", "Native American"]) [cite: 192]
        height = st.number_input("Height (inches)", min_value=50, max_value=90)
        hobby = st.multiselect("Hobbies", ["Cooking", "Music", "Games", "Housekeeping", "Exercise"]) [cite: 186]
        
        if st.form_submit_button("Book Participant"):
            # Add database insert logic here...
            st.success("Participant Logged Successfully.")

# --- VIEW 2: CLIENT DASHBOARD (Tata Elxsi Managers) ---
elif user_role == "Client (Tata Elxsi)":
    st.header("Daily Venue Operations")
    venue = st.selectbox("Select Venue", [f"Venue {chr(65+i)}" for i in range(10)]) # Venues A-J
    
    # Show only Today's Roster (Completes and Pendings)
    df_venue = get_data("SELECT id, first_name, session_type, booking_status FROM participants WHERE venue_id=?", (venue,))
    st.table(df_venue)
    
    selected_id = st.number_input("Enter Participant ID to Check-in", step=1)
    col1, col2, col3 = st.columns(3)
    if col1.button("Mark Arrived"):
        pass # Update DB to 'Arrived'
    if col2.button("Mark Completed"):
        st.balloons() # Update DB to 'Completed' - Triggers $150 incentive release
    if col3.button("Mark No-Show"):
        pass # Update DB to 'No-Show'

# --- VIEW 3: TRIDENT MASTER ADMIN ---
elif user_role == "Trident Admin":
    st.header("Global Multi-Center Command")
    global_df = get_data("SELECT * FROM participants")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Center 1 (Oklahoma)", f"{len(global_df[global_df['center_id']=='Center 1'])} / 1450")
    c2.metric("Center 2", "0 / 1450")
    c3.metric("Center 3", "0 / 1450")
    
    st.subheader("Race Quota Tracking (>10% Target)") [cite: 192]
    st.bar_chart(global_df['race'].value_value_counts())