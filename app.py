import streamlit as st
import pandas as pd
import requests
import random
import string
from datetime import datetime

st.set_page_config(page_title="Trident Project Command", layout="wide")

# --- 1. BRANDING & RAW LOGO CONNECTION ---
# Using the raw version of your GitHub link so Streamlit can render it
LOGO_URL = "https://raw.githubusercontent.com/malaykapoor95/Recruitment-engine/main/logo.png"

# Top Header with Logo on the Right
col_title, col_logo = st.columns([4, 1])
with col_title:
    st.title("Trident Project Command")
    st.caption(f"Pilot Operations | Started: April 6, 2026")
with col_logo:
    st.image(LOGO_URL, width=120)

st.divider()

# --- 2. CONFIGURATION ---
GAS_URL = "https://script.google.com/macros/s/AKfycbzHBCGpDIXjozsRDvJgStMIQvV_W1Lf_zSptRjrzGjMRuvtD2ZnUQd7gLESgEtegp_D/exec"
CENTER_MAP = {"Center 1": "C1", "Center 2": "C2", "Center 3": "C3"}

# --- 3. DATA HELPERS ---
def fetch_tab_data(tab_name):
    try:
        r = requests.get(f"{GAS_URL}?tab={tab_name}")
        data = r.json()
        if not data or len(data) < 2: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except: return pd.DataFrame()

def push_data(payload):
    try:
        r = requests.post(GAS_URL, json=payload)
        return r.text # Returns the generated Group ID (e.g., 2C1H001)
    except: return None

def get_height_tier(inches):
    try:
        i = int(inches)
        if 58 <= i <= 63: return "Tier 1 (4'10\"-5'2\")"
        elif 64 <= i <= 68: return "Tier 2 (5'3\"-5'7\")"
        elif 69 <= i <= 72: return "Tier 3 (5'8\"-6'1\")"
        elif i >= 73: return "Tier 4 (6'2\"+)"
        return "Out of Range"
    except: return "N/A"

# --- 4. SIDEBAR NAVIGATION ---
st.sidebar.image(LOGO_URL, width=100)
st.sidebar.title("Navigation")
sel_center = st.sidebar.selectbox("Current Center", ["Center 1", "Center 2", "Center 3"])
role = st.sidebar.selectbox("Access Level", ["Overview", "Recruitment", "Host"])
c_code = CENTER_MAP[sel_center]

if 'step' not in st.session_state: st.session_state.step = 1

# --- 5. RECRUITMENT VIEW ---
if role == "Recruitment":
    st.header(f"Recruitment Portal: {sel_center}")
    if st.session_state.step == 1:
        with st.container(border=True):
            col1, col2 = st.columns(2)
            s_type = col1.selectbox("Session Category", ["1 Person session", "2-3 people session", "4-5 people session"])
            num_pax = 1 if "1 Person" in s_type else (col1.slider("Count?", 2, 3) if "2-3" in s_type else col1.slider("Count?", 4, 5))
            venue = col2.selectbox("Venue", [f"House {i+1}" for i in range(10)])
            s_date, s_time = str(col2.date_input("Date")), str(col2.time_input("Time"))
        
        pax_list = []
        for i in range(num_pax):
            st.markdown(f"---")
            st.markdown(f"**Participant {i+1} Details**")
            c1, c2, c3, c4 = st.columns(4)
            rid = c1.text_input(f"Respondent ID", key=f"rid_{i}")
            fn = c2.text_input(f"First Name", key=f"fn_{i}")
            status = c3.selectbox("Status", ["Fresh", "Repeat"], key=f"stat_{i}")
            gen = c4.selectbox(f"Gender", ["Male", "Female"], key=f"g_{i}")
            
            c5, c6, c7 = st.columns(3)
            race = c5.selectbox(f"Race", ["East Asian", "South Asian", "Black", "Hispanic", "White", "Middle East", "Native American"], key=f"r_{i}")
            h = c6.number_input(f"Height (In)", 58, 85, key=f"h_{i}")
            age = c7.selectbox(f"Age Group", ["20-30", "30-40", "40-50", "50-60"], key=f"a_{i}")
            
            hob = st.multiselect(f"Hobbies", ["Cooking", "Music", "Games", "Housekeeping", "Exercise"], key=f"hob_{i}")
            pax_list.append({"rid": rid, "fn": fn, "status": status, "gender": gen, "race": race, "height": h, "age": age, "hobbies": str(hob)})

        if st.button("Review & Confirm →"):
            st.session_state.temp = {"type": s_type, "venue": venue, "date": s_date, "time": s_time, "pax": pax_list}
            st.session_state.step = 2; st.rerun()

    elif st.session_state.step == 2:
        st.subheader("Review Session Summary")
        st.table(pd.DataFrame(st.session_state.temp['pax']))
        c_back, c_conf = st.columns(2)
        if c_back.button("← Edit Details"): st.session_state.step = 1; st.rerun()
        if c_conf.button("CONFIRM & SYNC TO SHEET", type="primary"):
            payload = {"action": "add", "center_name": sel_center, "center_code": c_code, "venue": st.session_state.temp['venue'], "type": st.session_state.temp['type'], "date": st.session_state.temp['date'], "time": st.session_state.temp['time'], "pax": st.session_state.temp['pax']}
            new_id = push_data(payload)
            if new_id:
                st.success(f"Successfully Booked! Group ID: {new_id}")
                st.session_state.step = 1; st.balloons()

# --- 6. HOST VIEW ---
elif role == "Host":
    st.header(f"Host Operations: {sel_center}")
    h_tabs = st.tabs(["1 Pax", "2-3 Pax", "4-5 Pax"])
    prefixes = ["1-", "2-", "4-"]
    for i, tab in enumerate(h_tabs):
        with tab:
            curr_tab = prefixes[i] + c_code
            df = fetch_tab_data(curr_tab)
            if not df.empty:
                v_sel = st.selectbox("Select Venue", [f"House {j+1}" for j in range(10)], key=f"v_h_{i}")
                v_df = df[df['Venue ID'] == v_sel]
                for g_id, group in v_df.groupby('Group ID'):
                    with st.expander(f"[{group.iloc[0]['Scheduled Time']}] ID: {g_id}"):
                        for _, p in group.iterrows():
                            st.write(f"• ID: {p['Respondent ID']} | {p['First Name']} | {p['Booking Status']}")
                        c_a, c_c = st.columns(2)
                        if c_a.button("Arrived", key=f"a_{g_id}"):
                            push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "Arrived"}); st.rerun()
                        if c_c.button("Completed", key=f"c_{g_id}"):
                            push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "Completed"}); st.rerun()
            else: st.info("No data in this category.")

# --- 7. OVERVIEW ---
else:
    st.header(f"Center Overview: {sel_center}")
    frames = []
    for p in ["1-", "2-", "4-"]:
        frames.append(fetch_tab_data(p + c_code))
    all_data = pd.concat(frames, ignore_index=True)
    if not all_data.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Recruited", len(all_data), f"{1450 - len(all_data)} left")
        fresh_n = len(all_data[all_data['Status'] == 'Fresh'])
        m2.metric("Fresh Participants", fresh_n, "Target: 1015")
        comp_n = len(all_data[all_data['Booking Status'] == 'Completed'])
        m3.metric("Total Completes", comp_n)
        
        c_left, c_right = st.columns(2)
        with c_left:
            st.subheader("Height Distribution")
            all_data['Tier'] = all_data['Height (Inches)'].apply(get_height_tier)
            st.bar_chart(all_data['Tier'].value_counts())
            st.subheader("Race Distribution")
            st.bar_chart(all_data['Race'].value_counts())
        with c_right:
            st.subheader("Gender Split")
            st.pie_chart(all_data['Gender'].value_counts())
            st.subheader("Hobby Quotas (>10%)")
            for h in ["Cooking", "Music", "Games", "Housekeeping", "Exercise"]:
                count = all_data['Hobbies'].str.contains(h).sum()
                st.progress(min(count/145, 1.0), text=f"{h}: {count} participants")
    else: st.info("Awaiting pilot data...")
