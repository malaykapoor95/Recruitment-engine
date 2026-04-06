import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Trident Project Command", layout="wide")

# --- 1. BRANDING (TOP RIGHT ONLY) ---
LOGO_URL = "https://raw.githubusercontent.com/malaykapoor95/Recruitment-engine/main/logo.png"

col_title, col_logo = st.columns([4, 1])
with col_title:
    st.title("Trident Project Command")
    st.caption("Operational Dashboard | Pilot Phase | June 2026")
with col_logo:
    st.image(LOGO_URL, width=120)

st.divider()

# --- 2. CONFIGURATION & ACCESS CODES ---
GAS_URL = "https://script.google.com/macros/s/AKfycbzHBCGpDIXjozsRDvJgStMIQvV_W1Lf_zSptRjrzGjMRuvtD2ZnUQd7gLESgEtegp_D/exec"

ACCESS_CODES = {
    "TR-C1": "Center 1",
    "TR-C2": "Center 2",
    "TR-C3": "Center 3"
}

# --- 3. MAIN PAGE LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("Secure System Access")
    user_code = st.text_input("Enter your Center Access Code (e.g., TR-C1):")
    
    if user_code:
        if user_code in ACCESS_CODES:
            st.session_state.logged_in = True
            st.session_state.sel_center = ACCESS_CODES[user_code]
            st.rerun()
        else:
            st.error("Invalid Code. Please try again.")
    
    st.stop()

# --- 4. AUTHENTICATED APP ---
sel_center = st.session_state.sel_center
CENTER_MAP = {"Center 1": "C1", "Center 2": "C2", "Center 3": "C3"}
c_code = CENTER_MAP[sel_center]

# SIDEBAR NAVIGATION & SWITCHING
st.sidebar.title("Navigation")
st.sidebar.success(f"Active: {sel_center}")
role = st.sidebar.selectbox("Access Level", ["Overview", "Recruitment", "Host"])

st.sidebar.divider()

# --- NEW: SWITCH CENTER FEATURE ---
st.sidebar.caption("Switch Location")
switch_code = st.sidebar.text_input("Enter New Code:", placeholder="e.g. TR-C2")
if switch_code:
    if switch_code in ACCESS_CODES:
        # Update the session state and refresh the page instantly
        st.session_state.sel_center = ACCESS_CODES[switch_code]
        st.rerun()
    else:
        st.sidebar.error("Invalid Code")
        
# Optional: A clean logout button to return to the main screen
if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.divider()

if 'step' not in st.session_state: st.session_state.step = 1

# --- DATA HELPERS ---
def fetch_tab_data(tab_name):
    try:
        r = requests.get(f"{GAS_URL}?tab={tab_name}")
        data = r.json()
        if not data or len(data) < 2: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = [str(c).strip().title() for c in df.columns]
        df.columns = [c.replace("Height (Inches)", "Height") for c in df.columns]
        df.columns = [c.replace("Booking Status", "Booking_Status") for c in df.columns]
        df.columns = [c.replace("Group Id", "Group_Id") for c in df.columns]
        df.columns = [c.replace("Respondent Id", "Respondent_Id") for c in df.columns]
        df.columns = [c.replace("Venue Id", "Venue_Id") for c in df.columns]
        df.columns = [c.replace("Session Type", "Session_Type") for c in df.columns]
        return df
    except: return pd.DataFrame()

def push_data(payload):
    try:
        r = requests.post(GAS_URL, json=payload)
        return r.text 
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

# --- 5. RECRUITMENT ---
if role == "Recruitment":
    st.header(f"Recruitment: {sel_center}")
    if st.session_state.step == 1:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            s_type = c1.selectbox("Category", ["1 Person session", "2-3 people session", "4-5 people session"])
            num_pax = 1 if "1 Person" in s_type else (c1.slider("Count", 2, 3) if "2-3" in s_type else c1.slider("Count", 4, 5))
            venue = c2.selectbox("Venue", [f"House {i+1}" for i in range(10)])
            s_date, s_time = str(c2.date_input("Date")), str(c2.time_input("Time"))
        
        pax_list = []
        for i in range(num_pax):
            st.markdown("---")
            st.markdown(f"**Participant {i+1}**")
            ca, cb, cc, cd = st.columns(4)
            rid = ca.text_input("Respondent ID", key=f"rid_{i}")
            fn = cb.text_input("First Name", key=f"fn_{i}")
            status = cc.selectbox("Status", ["Fresh", "Repeat"], key=f"stat_{i}")
            gen = cd.selectbox("Gender", ["Male", "Female"], key=f"g_{i}")
            ce, cf, cg = st.columns(3)
            race = ce.selectbox("Race", ["East Asian", "South Asian", "Black", "Hispanic", "White", "Middle East", "Native American"], key=f"r_{i}")
            h = cf.number_input("Height (In)", 58, 85, key=f"h_{i}")
            age = cg.selectbox("Age Group", ["20-30", "30-40", "40-50", "50-60"], key=f"a_{i}")
            hob = st.multiselect("Hobbies", ["Cooking", "Music", "Games", "Housekeeping", "Exercise"], key=f"hob_{i}")
            pax_list.append({"rid": rid, "fn": fn, "status": status, "gender": gen, "race": race, "height": h, "age": age, "hobbies": str(hob)})

        if st.button("Review & Confirm"):
            st.session_state.temp = {"type": s_type, "venue": venue, "date": s_date, "time": s_time, "pax": pax_list}
            st.session_state.step = 2; st.rerun()

    elif st.session_state.step == 2:
        st.table(pd.DataFrame(st.session_state.temp['pax']))
        cb, cc = st.columns(2)
        if cb.button("← Edit"): st.session_state.step = 1; st.rerun()
        if cc.button("SYNC TO GOOGLE SHEETS", type="primary"):
            payload = {"action": "add", "center_name": sel_center, "center_code": c_code, "venue": st.session_state.temp['venue'], "type": st.session_state.temp['type'], "date": st.session_state.temp['date'], "time": st.session_state.temp['time'], "pax": st.session_state.temp['pax']}
            new_id = push_data(payload)
            if new_id: st.success(f"Success! ID: {new_id}"); st.session_state.step = 1; st.balloons()

# --- 6. HOST ---
elif role == "Host":
    st.header(f"Host Ops: {sel_center}")
    h_tabs = st.tabs(["1 Pax", "2-3 Pax", "4-5 Pax"])
    prefixes = ["1-", "2-", "4-"]
    for i, tab in enumerate(h_tabs):
        with tab:
            curr_tab = prefixes[i] + c_code
            df = fetch_tab_data(curr_tab)
            if not df.empty:
                v_sel = st.selectbox("Select Venue", [f"House {j+1}" for j in range(10)], key=f"v_{i}")
                v_df = df[df['Venue_Id'] == v_sel]
                for g_id, group in v_df.groupby('Group_Id'):
                    with st.expander(f"[{group.iloc[0].get('Scheduled_Time', '')}] ID: {g_id}"):
                        for _, p in group.iterrows():
                            st.write(f"• ID: {p.get('Respondent_Id')} | {p.get('First Name')} | Status: {p.get('Booking_Status')}")
                        ca, cc, cn = st.columns(3)
                        if ca.button("Arrived", key=f"a_{g_id}"): push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "Arrived"}); st.rerun()
                        if cc.button("Completed", key=f"c_{g_id}"): push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "Completed"}); st.rerun()
                        if cn.button("No-Show", key=f"n_{g_id}"): push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "No-Show"}); st.rerun()
            else: st.info("No data.")

# --- 7. OVERVIEW ---
else:
    st.header(f"Center Overview: {sel_center}")
    frames = []
    for p in ["1-", "2-", "4-"]: 
        df = fetch_tab_data(p + c_code)
        if not df.empty: frames.append(df)
        
    if frames:
        all_data = pd.concat(frames, ignore_index=True)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Recruited", len(all_data), f"{1450 - len(all_data)} left")
        m2.metric("Fresh (Target 1015)", len(all_data[all_data['Status'] == 'Fresh']))
        m3.metric("Completes", len(all_data[all_data['Booking_Status'] == 'Completed']))
        
        no_shows = len(all_data[all_data['Booking_Status'] == 'No-Show'])
        m4.metric("No-Shows", no_shows, delta_color="inverse")
        
        st.divider()

        cl, cc, cr = st.columns(3)
        with cl:
            st.subheader("Race Distribution")
            st.bar_chart(all_data['Race'].value_counts())
        with cc:
            st.subheader("Gender Split")
            if 'Gender' in all_data.columns: st.pie_chart(all_data['Gender'].value_counts())
        with cr:
            st.subheader("House Bookings")
            if 'Venue_Id' in all_data.columns: st.bar_chart(all_data['Venue_Id'].value_counts())

        st.divider()

        cb1, cb2 = st.columns(2)
        with cb1:
            st.subheader("Hobby Quotas (Need 145+)")
            for h in ["Cooking", "Music", "Games", "Housekeeping", "Exercise"]:
                count = all_data['Hobbies'].str.contains(h).sum()
                st.progress(min(count/145, 1.0), text=f"{h}: {count} pax")
        with cb2:
            st.subheader("Session Mix")
            if 'Session_Type' in all_data.columns:
                st.bar_chart(all_data['Session_Type'].value_counts())

    else: st.info("System is ready. Awaiting June pilot entries...")
