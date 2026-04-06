import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Trident Scheduling Platform", layout="wide")

# --- 1. BRANDING & STYLING ---
st.markdown("""
    <style>
    .reportview-container .main .block-container{ padding-top: 2rem; }
    .status-pill { padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: bold; }
    .status-high { background-color: #fee2e2; color: #991b1b; border: 1px solid #f87171; }
    .status-medium { background-color: #fef3c7; color: #92400e; border: 1px solid #fbbf24; }
    .status-low { background-color: #e0e7ff; color: #3730a3; border: 1px solid #818cf8; }
    </style>
""", unsafe_allow_html=True)

# Top Bar (Mimicking the React Header)
col_title, col_controls = st.columns([2, 1])
with col_title:
    st.markdown("### Trident Scheduling Platform")
    st.caption("Multi-center operations dashboard | June 2026 MVP")
with col_controls:
    # Placing the role/center select in the top right to match the JS UI
    c1, c2 = st.columns(2)
    role = c1.selectbox("Role", ["Admin", "Recruitment", "Host"], label_visibility="collapsed")
    sel_center = c2.selectbox("Center", ["Center 1", "Center 2", "Center 3"], label_visibility="collapsed")

st.divider()

# --- 2. CONFIG & HELPERS ---
GAS_URL = "https://script.google.com/macros/s/AKfycbzHBCGpDIXjozsRDvJgStMIQvV_W1Lf_zSptRjrzGjMRuvtD2ZnUQd7gLESgEtegp_D/exec"
CENTER_MAP = {"Center 1": "C1", "Center 2": "C2", "Center 3": "C3"}
c_code = CENTER_MAP[sel_center]

# Initialize local state for Operational Issues (MVP simulation)
if 'issues' not in st.session_state:
    st.session_state.issues = [
        {"id": "ISS-001", "ref": "System", "note": "Venue B HVAC maintenance scheduled for June 10th.", "severity": "Medium"}
    ]

def fetch_tab_data(tab_name):
    try:
        r = requests.get(f"{GAS_URL}?tab={tab_name}")
        data = r.json()
        if not data or len(data) < 2: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = [str(c).strip().title().replace(" ", "_") for c in df.columns]
        # Standardize known columns
        if 'Booking_Status' not in df.columns and 'Status' in df.columns: df['Booking_Status'] = df['Status']
        return df
    except: return pd.DataFrame()

def push_data(payload):
    try: r = requests.post(GAS_URL, json=payload); return r.text 
    except: return None

# Load center data
frames = [fetch_tab_data(f"{p}{c_code}") for p in ["1-", "2-", "4-"]]
df_all = pd.concat([f for f in frames if not f.empty], ignore_index=True) if frames else pd.DataFrame()

# Calculate Top Metrics
total_target = 1450
total_sessions = len(df_all) if not df_all.empty else 0
completed = len(df_all[df_all['Booking_Status'] == 'Completed']) if not df_all.empty and 'Booking_Status' in df_all.columns else 0
pending = total_target - completed

# --- 3. SHARED UI COMPONENTS ---
def render_top_metrics():
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        with st.container(border=True): st.metric("Target", total_target)
    with m2:
        with st.container(border=True): st.metric("Sessions", total_sessions)
    with m3:
        with st.container(border=True): st.metric("Completed", completed)
    with m4:
        with st.container(border=True): st.metric("Pending", pending)

def render_quick_panel(role_name):
    with st.container(border=True):
        st.markdown("##### Active context")
        st.markdown(f"**User:** Malay K.<br>**Role:** {role_name}<br>**Center:** {sel_center}<br>**City:** TBD", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("##### Venues in this center")
        for i in range(3): # Show top 3 venues
            v_name = f"House {i+1}"
            v_comp = len(df_all[(df_all.get('Venue_Id') == v_name) & (df_all.get('Booking_Status') == 'Completed')]) if not df_all.empty else 0
            v_pend = len(df_all[(df_all.get('Venue_Id') == v_name) & (df_all.get('Booking_Status') != 'Completed')]) if not df_all.empty else 0
            
            with st.container(border=True):
                st.markdown(f"📍 **{v_name}**")
                c1, c2, c3 = st.columns(3)
                c1.caption("Completed"); c1.write(f"**{v_comp}**")
                c2.caption("Pending"); c2.write(f"**{v_pend}**")
                c3.caption("Arrived"); c3.write(f"**0**")

def render_issues():
    with st.container(border=True):
        st.markdown("##### ⚠️ Operational issues")
        if not st.session_state.issues:
            st.info("No active issues reported.")
        for issue in reversed(st.session_state.issues):
            sev_class = f"status-{issue['severity'].lower()}"
            st.markdown(f"""
                <div style="padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <strong>{issue['id']} (Ref: {issue['ref']})</strong>
                        <span class="status-pill {sev_class}">{issue['severity']}</span>
                    </div>
                    <span style="font-size: 14px; color: #475569;">{issue['note']}</span>
                </div>
            """, unsafe_allow_html=True)


# --- 4. ADMIN VIEW (OVERVIEW) ---
if role == "Admin":
    render_top_metrics()
    st.write("") # Spacer
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        # Quota Status Card
        with st.container(border=True):
            st.markdown(f"##### 📊 {sel_center} quota status")
            fresh_c = len(df_all[df_all.get('Status') == 'Fresh']) if not df_all.empty else 0
            st.progress(min(fresh_c/1015, 1.0), text=f"Fresh Participants ({fresh_c} / 1015)")
            st.progress(min(0/435, 1.0), text=f"Repeat Participants (0 / 435)")
            st.markdown("---")
            if not df_all.empty and 'Gender' in df_all.columns:
                m_c = len(df_all[df_all['Gender'] == 'Male'])
                f_c = len(df_all[df_all['Gender'] == 'Female'])
                st.progress(min(m_c/580, 1.0), text=f"Male ({m_c} / 580)")
                st.progress(min(f_c/580, 1.0), text=f"Female ({f_c} / 580)")

        # Venues Grid
        v_col1, v_col2 = st.columns(2)
        for i in range(4):
            tgt_col = v_col1 if i % 2 == 0 else v_col2
            with tgt_col:
                with st.container(border=True):
                    st.markdown(f"🏢 **House {i+1}**")
                    st.caption("Completed: **--** | Pending: **--**")
        
        # Issues Component
        render_issues()

    with col_side:
        render_quick_panel("Admin")

# --- 5. RECRUITMENT VIEW ---
elif role == "Recruitment":
    render_top_metrics()
    st.write("")
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        # NEW: ADD RECRUIT MODULE
        with st.container(border=True):
            st.markdown("##### ➕ Add New Recruit(s)")
            tab_man, tab_csv = st.tabs(["Manual Entry", "Bulk CSV Upload"])
            
            with tab_man:
                c1, c2 = st.columns(2)
                s_type = c1.selectbox("Category", ["1 Person session", "2-3 people session", "4-5 people session"])
                venue = c2.selectbox("Venue", [f"House {i+1}" for i in range(10)])
                rid = st.text_input("Respondent ID")
                if st.button("Add Single Recruit", type="primary"):
                    st.success("Recruit added to queue.")
            
            with tab_csv:
                st.info("Upload a CSV with columns: Respondent_ID, First_Name, Status, Gender, Race, Age, Hobbies")
                uploaded_file = st.file_uploader("Drop CSV file here", type=["csv"])
                if uploaded_file is not None:
                    try:
                        df_upload = pd.read_csv(uploaded_file)
                        st.dataframe(df_upload.head(3))
                        if st.button("Process & Sync 50+ Rows", type="primary"):
                            st.success(f"Successfully batch uploaded {len(df_upload)} participants!")
                            st.balloons()
                    except Exception as e:
                        st.error("Error reading CSV file. Ensure it matches the template.")

        # Booking Inventory & Quotas
        with st.container(border=True):
            st.markdown("##### 📋 Booking Inventory")
            st.caption("2026-06-01 • 09:00 AM | House 1 - Remaining: **1**")
            st.caption("2026-06-01 • 10:30 AM | House 2 - Remaining: **4**")
            
        render_issues()

    with col_side:
        render_quick_panel("Recruitment")

# --- 6. HOST VIEW ---
elif role == "Host":
    col_main, col_side = st.columns([2, 1])
    
    with col_side:
        render_quick_panel("Venue Host")
        
        # NEW: ISSUE REPORTER
        with st.container(border=True):
            st.markdown("##### 🚨 Report Issue")
            issue_ref = st.text_input("Booking ID / Reference")
            severity = st.selectbox("Severity", ["Low", "Medium", "High"])
            issue_note = st.text_area("Issue Description")
            if st.button("Submit Report", use_container_width=True):
                new_id = f"ISS-{len(st.session_state.issues) + 1:03d}"
                st.session_state.issues.append({
                    "id": new_id, "ref": issue_ref, "note": issue_note, "severity": severity
                })
                st.success("Issue broadcasted to Admin & Recruitment.")
                st.rerun()

    with col_main:
        with st.container(border=True):
            st.markdown("##### Daily Roster")
            h_tab = st.selectbox("Session Size", ["1 Pax", "2-3 Pax", "4-5 Pax"])
            curr_tab = {"1 Pax":"1-", "2-3 Pax":"2-", "4-5 Pax":"4-"}[h_tab] + c_code
            df = fetch_tab_data(curr_tab)
            
            if not df.empty:
                v_sel = st.selectbox("Filter Venue", [f"House {j+1}" for j in range(10)])
                v_df = df[df.get('Venue_Id', df.get('Venue Id')) == v_sel]
                for g_id, group in v_df.groupby(df.get('Group_Id', df.get('Group Id'))):
                    with st.expander(f"Group: {g_id}"):
                        for _, p in group.iterrows():
                            st.write(f"• ID: {p.get('Respondent_Id')} | Name: {p.get('First_Name')} | Status: {p.get('Booking_Status')}")
                        ca, cc, cn = st.columns(3)
                        if ca.button("Arrived", key=f"a_{g_id}"): push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "Arrived"}); st.rerun()
                        if cc.button("Completed", key=f"c_{g_id}"): push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "Completed"}); st.rerun()
                        if cn.button("No-Show", key=f"n_{g_id}"): push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "No-Show"}); st.rerun()
            else: st.info("No schedule data available.")
