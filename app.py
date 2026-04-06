import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Trident Pilot Dashboard", layout="wide")

# --- 1. LIVE CONNECTION ---
# Your specific Google Apps Script URL
GAS_URL = "https://script.google.com/macros/s/AKfycbzHBCGpDIXjozsRDvJgStMIQvV_W1Lf_zSptRjrzGjMRuvtD2ZnUQd7gLESgEtegp_D/exec"

def get_sheet_data(center):
    try:
        # Pass the center name as a parameter to read the correct tab
        r = requests.get(f"{GAS_URL}?center={center}")
        data = r.json()
        # Uses Row 1 as headers
        return pd.DataFrame(data[1:], columns=data[0])
    except: 
        return pd.DataFrame()

def push_to_sheet(payload):
    try: 
        requests.post(GAS_URL, json=payload)
        return True
    except: 
        return False

def get_height_tier(inches):
    try:
        i = int(inches)
        if 58 <= i <= 63: return "Tier 1 (4'10\"-5'2\")"
        elif 64 <= i <= 68: return "Tier 2 (5'3\"-5'7\""
        elif 69 <= i <= 72: return "Tier 3 (5'8\"-6'1\")"
        elif i >= 73: return "Tier 4 (6'2\"+)"
        return "Out of Range"
    except: return "N/A"

# --- 2. SIDEBAR NAVIGATION ---
st.sidebar.title("Trident Command")
selected_center = st.sidebar.selectbox("Current Center", ["Center 1", "Center 2", "Center 3"])
role = st.sidebar.selectbox("Access Level", ["Overview", "Recruitment", "Host"])

if 'step' not in st.session_state: st.session_state.step = 1

# --- 3. RECRUITMENT VIEW ---
if role == "Recruitment":
    st.header(f"Recruitment: {selected_center}")

    if st.session_state.step == 1:
        with st.container(border=True):
            col1, col2 = st.columns(2)
            s_type = col1.selectbox("Session Category", ["1 Person session", "2-3 people session", "4-5 people session"])
            num_pax = 1 if "1 Person" in s_type else (col1.slider("Count?", 2, 3) if "2-3" in s_type else col1.slider("Count?", 4, 5))
            venue = col2.selectbox("Venue", [f"House {i+1}" for i in range(10)])
            s_date, s_time = col2.date_input("Date"), col2.time_input("Time")

        pax_data = []
        for i in range(num_pax):
            st.markdown(f"---")
            st.markdown(f"**Participant {i+1} Details**")
            c1, c2, c3 = st.columns(3)
            rid = c1.text_input(f"Respondent ID", key=f"rid_{i}")
            fn = c2.text_input(f"First Name", key=f"fn_{i}")
            gender = c3.selectbox(f"Gender", ["Male", "Female"], key=f"g_{i}")
            
            c4, c5, c6 = st.columns(3)
            race = c4.selectbox(f"Race", ["East Asian", "South Asian", "Black", "Hispanic", "White", "Middle East", "Native American"], key=f"r_{i}")
            h = c4.number_input(f"Height (In)", 58, 85, key=f"h_{i}")
            age = c5.selectbox(f"Age Group", ["20-30", "30-40", "40-50", "50-60"], key=f"a_{i}")
            
            hobbies = st.multiselect(f"Hobbies", ["Cooking", "Music", "Games", "Housekeeping", "Exercise"], key=f"hob_{i}")
            pax_data.append({"rid": rid, "fn": fn, "race": race, "height": h, "gender": gender, "age": age, "hobbies": str(hobbies)})

        if st.button("Review & Confirm →"):
            st.session_state.temp_data = {"center": selected_center, "type": s_type, "venue": venue, "date": str(s_date), "time": str(s_time), "pax": pax_data}
            st.session_state.step = 2
            st.rerun()

    elif st.session_state.step == 2:
        d = st.session_state.temp_data
        st.subheader("Review Session Summary")
        st.table(pd.DataFrame(d['pax']))
        c1, c2 = st.columns(2)
        if c1.button("← Edit"): 
            st.session_state.step = 1
            st.rerun()
        if c2.button("FINAL SYNC TO SHEET", type="primary"):
            g_id = "G" + datetime.now().strftime("%Y%m%d%H%M%S")
            payload = {"action": "add", "center": d['center'], "venue": d['venue'], "type": d['type'], "date": d['date'], "time": d['time'], "group_id": g_id, "pax": d['pax']}
            if push_to_sheet(payload):
                st.success(f"Synced to {selected_center} sheet!")
                st.session_state.step = 1
                st.balloons()

# --- 4. HOST VIEW ---
elif role == "Host":
    st.header(f"Host Dashboard: {selected_center}")
    venue = st.selectbox("Venue", [f"House {i+1}" for i in range(10)])
    df = get_sheet_data(selected_center)
    
    if not df.empty:
        # Match venue ID to the select box
        v_df = df[df['Venue ID'] == venue]
        if not v_df.empty:
            for g_id, group in v_df.groupby('Group ID'):
                with st.expander(f"[{group.iloc[0]['Scheduled Time']}] {group.iloc[0]['Session Type']}"):
                    for _, p in group.iterrows():
                        st.write(f"• ID: **{p['Respondent ID']}** | Name: {p['First Name']} | Status: {p['Booking Status']}")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("Arrived", key=f"a_{g_id}"):
                        push_to_sheet({"action": "update", "center": selected_center, "group_id": g_id, "status": "Arrived"})
                        st.rerun()
                    if c2.button("Completed", key=f"c_{g_id}"):
                        push_to_sheet({"action": "update", "center": selected_center, "group_id": g_id, "status": "Completed"})
                        st.rerun()
        else: st.info("No participants scheduled for this house.")
    else: st.write("Loading data from Google Sheets...")

# --- 5. OVERVIEW ---
else:
    st.header(f"Project Overview: {selected_center}")
    all_data = get_sheet_data(selected_center)
    if not all_data.empty:
        m1, m2 = st.columns(2)
        m1.metric("Total Recruits", len(all_data))
        # Filter for completed sessions
        completes = len(all_data[all_data['Booking Status'] == 'Completed'])
        m2.metric("Total Completes", completes)

        st.subheader("Height Tier Distribution")
        all_data['Tier'] = all_data['Height (Inches)'].apply(get_height_tier)
        st.bar_chart(all_data['Tier'].value_counts())
    else: st.info("No data recorded for this center yet.")
