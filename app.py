import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Trident Project Command", layout="wide")

# --- 1. BRANDING ---
LOGO_URL = "https://raw.githubusercontent.com/malaykapoor95/Recruitment-engine/main/logo.png"

col_title, col_logo = st.columns([4, 1])
with col_title:
    st.title("Trident Project Command")
    st.caption("Operational Dashboard | Pilot Phase | April 6, 2026")
with col_logo:
    st.image(LOGO_URL, width=120)

st.divider()

# --- 2. CONFIGURATION & ACCESS CODES ---
GAS_URL = "https://script.google.com/macros/s/AKfycbzHBCGpDIXjozsRDvJgStMIQvV_W1Lf_zSptRjrzGjMRuvtD2ZnUQd7gLESgEtegp_D/exec"

# Define your secret codes here
ACCESS_CODES = {
    "TR-C1": "Center 1",
    "TR-C2": "Center 2",
    "TR-C3": "Center 3"
}

# --- 3. SIDEBAR ACCESS GATE ---
st.sidebar.title("Secure Access")
user_code = st.sidebar.text_input("Enter Center Access Code", type="password")

# Check if the code is valid
if user_code in ACCESS_CODES:
    sel_center = ACCESS_CODES[user_code]
    st.sidebar.success(f"Access Granted: {sel_center}")
    
    # Map for data fetching
    CENTER_MAP = {"Center 1": "C1", "Center 2": "C2", "Center 3": "C3"}
    c_code = CENTER_MAP[sel_center]
    
    # Role Selection (Vendors only see Recruitment/Host)
    role = st.sidebar.selectbox("Access Level", ["Recruitment", "Host", "Overview"])
    
    # --- DATA HELPERS ---
    def fetch_tab_data(tab_name):
        try:
            r = requests.get(f"{GAS_URL}?tab={tab_name}")
            data = r.json()
            if not data or len(data) < 2: return pd.DataFrame()
            df = pd.DataFrame(data[1:], columns=data[0])
            df.columns = [str(c).strip().title() for c in df.columns]
            return df
        except: return pd.DataFrame()

    def push_data(payload):
        try:
            r = requests.post(GAS_URL, json=payload)
            return r.text 
        except: return None

    # --- 4. RECRUITMENT VIEW ---
    if role == "Recruitment":
        st.header(f"Recruitment Portal: {sel_center}")
        # ... [Keep your existing Wizard Logic here] ...
        # (Snippet for brevity)
        if 'step' not in st.session_state: st.session_state.step = 1
        if st.session_state.step == 1:
            with st.container(border=True):
                col1, col2 = st.columns(2)
                s_type = col1.selectbox("Session Type", ["1 Person session", "2-3 people session", "4-5 people session"])
                num_pax = 1 if "1 Person" in s_type else (col1.slider("Count?", 2, 3) if "2-3" in s_type else col1.slider("Count?", 4, 5))
                venue = col2.selectbox("Venue", [f"House {i+1}" for i in range(10)])
                s_date, s_time = str(col2.date_input("Date")), str(col2.time_input("Time"))
            
            pax_list = []
            for i in range(num_pax):
                st.markdown(f"---")
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
            st.table(pd.DataFrame(st.session_state.temp['pax']))
            if st.button("CONFIRM & SYNC", type="primary"):
                payload = {"action": "add", "center_name": sel_center, "center_code": c_code, "venue": st.session_state.temp['venue'], "type": st.session_state.temp['type'], "date": st.session_state.temp['date'], "time": st.session_state.temp['time'], "pax": st.session_state.temp['pax']}
                new_id = push_data(payload)
                if new_id: st.success(f"ID: {new_id}"); st.session_state.step = 1; st.balloons()

    # --- 5. HOST VIEW ---
    elif role == "Host":
        st.header(f"Host Operations: {sel_center}")
        h_tabs = st.tabs(["1 Pax", "2-3 Pax", "4-5 Pax"])
        prefixes = ["1-", "2-", "4-"]
        for i, tab in enumerate(h_tabs):
            with tab:
                df = fetch_tab_data(prefixes[i] + c_code)
                if not df.empty:
                    v_sel = st.selectbox("Venue Filter", [f"House {j+1}" for j in range(10)], key=f"v_h_{i}")
                    v_df = df[df['Venue Id'] == v_sel]
                    for g_id, group in v_df.groupby('Group Id'):
                        with st.expander(f"ID: {g_id}"):
                            for _, p in group.iterrows():
                                st.write(f"• ID: {p['Respondent Id']} | {p['First Name']} | {p['Booking Status']}")
                            c_a, c_c, c_n = st.columns(3)
                            if c_a.button("Arrived", key=f"a_{g_id}"): push_data({"action": "update", "center": prefixes[i] + c_code, "group_id": g_id, "status": "Arrived"}); st.rerun()
                            if c_c.button("Completed", key=f"c_{g_id}"): push_data({"action": "update", "center": prefixes[i] + c_code, "group_id": g_id, "status": "Completed"}); st.rerun()
                            if c_n.button("No-Show", key=f"n_{g_id}"): push_data({"action": "update", "center": prefixes[i] + c_code, "group_id": g_id, "status": "No-Show"}); st.rerun()
                else: st.info("No data.")

    # --- 6. OVERVIEW ---
    else:
        st.header(f"Project Overview: {sel_center}")
        frames = []
        for p in ["1-", "2-", "4-"]: frames.append(fetch_tab_data(p + c_code))
        all_data = pd.concat(frames, ignore_index=True)
        if not all_data.empty:
            st.metric("Total Recruits", len(all_data), f"{1450 - len(all_data)} left")
            st.bar_chart(all_data['Race'].value_counts())
        else: st.info("Awaiting data...")

else:
    st.info("Welcome to Trident Project Command. Please enter your Center Access Code in the sidebar to begin.")
    st.image(LOGO_URL, width=200)
