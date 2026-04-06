import streamlit as st
import pandas as pd
import requests

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

LOGO_URL = "https://raw.githubusercontent.com/malaykapoor95/Recruitment-engine/main/logo.png"

# --- 2. CONFIGURATION & ROLE KEYS ---
GAS_URL = "https://script.google.com/macros/s/AKfycbzHBCGpDIXjozsRDvJgStMIQvV_W1Lf_zSptRjrzGjMRuvtD2ZnUQd7gLESgEtegp_D/exec"
CENTER_MAP = {"Center 1": "C1", "Center 2": "C2", "Center 3": "C3"}

# The new Master Key logic linking Codes to Roles and Centers
ACCESS_KEYS = {
    "TR-ADMIN-99": {"role": "Admin", "center": "All"},
    "REC-C1": {"role": "Recruitment", "center": "Center 1"},
    "REC-C2": {"role": "Recruitment", "center": "Center 2"},
    "REC-C3": {"role": "Recruitment", "center": "Center 3"},
    "MGR-C1": {"role": "Host", "center": "Center 1"},
    "MGR-C2": {"role": "Host", "center": "Center 2"},
    "MGR-C3": {"role": "Host", "center": "Center 3"},
}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'issues' not in st.session_state: st.session_state.issues = []

# --- 3. WELCOME & LOGIN SCREEN ---
if not st.session_state.logged_in:
    col_t, col_l = st.columns([4, 1])
    col_l.image(LOGO_URL, width=120)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("### Welcome to Trident Command")
            st.caption("Please authenticate to access your operational dashboard.")
            user_code = st.text_input("Enter Access Code:", type="password")
            
            if st.button("Secure Login", type="primary", use_container_width=True):
                if user_code in ACCESS_KEYS:
                    st.session_state.logged_in = True
                    st.session_state.user_role = ACCESS_KEYS[user_code]["role"]
                    st.session_state.sel_center = ACCESS_KEYS[user_code]["center"]
                    # If admin, default to Overview and Center 1
                    if st.session_state.user_role == "Admin":
                        st.session_state.admin_view = "Overview"
                        st.session_state.sel_center = "Center 1"
                    st.rerun()
                else:
                    st.error("Access Denied. Invalid Code.")
    st.stop()

# --- 4. AUTHENTICATED HEADER ---
col_title, col_logo = st.columns([4, 1])
with col_title:
    st.markdown("### Trident Scheduling Platform")
    st.caption("Multi-center operations dashboard | June 2026 MVP")
with col_logo:
    st.image(LOGO_URL, width=100)
st.divider()

# Variables for the active session
role = st.session_state.user_role
sel_center = st.session_state.sel_center

# Admin Navigation (Only Admins see the sidebar controls)
if role == "Admin":
    st.sidebar.title("Admin Controls")
    sel_center = st.sidebar.selectbox("Override Center", ["Center 1", "Center 2", "Center 3"])
    st.session_state.admin_view = st.sidebar.selectbox("Impersonate View", ["Overview", "Recruitment", "Host"])
    st.sidebar.divider()
    active_view = st.session_state.admin_view
else:
    active_view = role # Vendors and Managers are locked to their role
    # Non-admins get a simple logout button in the sidebar to keep UI clean
    st.sidebar.success(f"Logged in as: {role}")
    st.sidebar.caption(f"Assigned to: {sel_center}")

if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.rerun()

c_code = CENTER_MAP[sel_center]

# --- DATA HELPERS ---
def fetch_tab_data(tab_name):
    try:
        r = requests.get(f"{GAS_URL}?tab={tab_name}")
        data = r.json()
        if not data or len(data) < 2: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = [str(c).strip().title().replace(" ", "_") for c in df.columns]
        if 'Booking_Status' not in df.columns and 'Status' in df.columns: df['Booking_Status'] = df['Status']
        return df
    except: return pd.DataFrame()

def push_data(payload):
    try: r = requests.post(GAS_URL, json=payload); return r.text 
    except: return None

# Load Center Data
frames = [fetch_tab_data(f"{p}{c_code}") for p in ["1-", "2-", "4-"]]
df_all = pd.concat([f for f in frames if not f.empty], ignore_index=True) if frames else pd.DataFrame()

# --- 5. OVERVIEW VIEW (ADMIN ONLY) ---
if active_view == "Overview":
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Target", 1450)
    m2.metric("Sessions", len(df_all))
    m3.metric("Completed", len(df_all[df_all['Booking_Status'] == 'Completed']) if not df_all.empty and 'Booking_Status' in df_all.columns else 0)
    m4.metric("Pending", 1450 - (len(df_all[df_all['Booking_Status'] == 'Completed']) if not df_all.empty and 'Booking_Status' in df_all.columns else 0))
    
    col_main, col_side = st.columns([2, 1])
    with col_main:
        with st.container(border=True):
            st.markdown(f"##### 📊 {sel_center} Quota Status")
            fresh_c = len(df_all[df_all.get('Status') == 'Fresh']) if not df_all.empty else 0
            st.progress(min(fresh_c/1015, 1.0), text=f"Fresh Participants ({fresh_c} / 1015)")
            st.progress(0.0, text=f"Repeat Participants (0 / 435)")
            
        with st.container(border=True):
            st.markdown("##### ⚠️ System Operational Issues")
            if not st.session_state.issues: st.info("No active issues reported by Center Managers.")
            for issue in reversed(st.session_state.issues):
                if issue.get('center') == sel_center or role == "Admin": # Show center-specific issues
                    st.markdown(f"""
                        <div style="padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <strong>ID: {issue['resp_id']} | Venue: {issue['venue']} | {issue['session']}</strong>
                                <span class="status-pill status-{issue['severity'].lower()}">{issue['severity']}</span>
                            </div>
                            <span style="font-size: 14px; color: #475569;">{issue['note']}</span>
                            <div style="font-size: 11px; color: #94a3b8; margin-top: 5px;">Reported by: {issue['center']}</div>
                        </div>
                    """, unsafe_allow_html=True)
    with col_side:
        with st.container(border=True):
            st.markdown("##### Venue Performance")
            if not df_all.empty and 'Venue_Id' in df_all.columns:
                st.dataframe(df_all['Venue_Id'].value_counts(), use_container_width=True)
            else: st.info("Awaiting entries.")

# --- 6. RECRUITMENT VIEW ---
elif active_view == "Recruitment":
    if 'show_quotas' not in st.session_state: st.session_state.show_quotas = False
    
    c_head, c_btn = st.columns([3, 1])
    c_head.markdown(f"### Recruitment: {sel_center}")
    if c_btn.button("📊 View Center Quotas", use_container_width=True):
        st.session_state.show_quotas = not st.session_state.show_quotas
        st.rerun()

    if st.session_state.show_quotas:
        with st.container(border=True):
            st.markdown(f"##### Quick Quota Snapshot")
            fresh_c = len(df_all[df_all.get('Status') == 'Fresh']) if not df_all.empty else 0
            st.progress(min(fresh_c/1015, 1.0), text=f"Fresh Participants ({fresh_c} / 1015)")
            if not df_all.empty and 'Gender' in df_all.columns:
                m_c = len(df_all[df_all['Gender'] == 'Male'])
                f_c = len(df_all[df_all['Gender'] == 'Female'])
                st.progress(min(m_c/580, 1.0), text=f"Male ({m_c} / 580)")
                st.progress(min(f_c/580, 1.0), text=f"Female ({f_c} / 580)")
            if st.button("Close Quotas", size="small"): 
                st.session_state.show_quotas = False
                st.rerun()
            st.markdown("---")

    with st.container(border=True):
        st.markdown("##### ➕ Add New Recruit(s)")
        tab_man, tab_csv = st.tabs(["Manual Entry", "Bulk CSV Upload"])
        
        with tab_man:
            c1, c2 = st.columns(2)
            s_type = c1.selectbox("Category", ["1 Person session", "2-3 people session", "4-5 people session"])
            venue = c2.selectbox("Venue", [f"House {i+1}" for i in range(10)])
            c3, c4 = st.columns(2)
            rid = c3.text_input("Respondent ID")
            fn = c4.text_input("First Name")
            if st.button("Add Single Recruit", type="primary"): st.success("Recruit added successfully.")
        
        with tab_csv:
            st.info("Upload a CSV file containing your bulk respondent list.")
            uploaded_file = st.file_uploader("Drop CSV file here", type=["csv"])
            if uploaded_file is not None:
                try:
                    df_upload = pd.read_csv(uploaded_file)
                    st.dataframe(df_upload.head(3))
                    if st.button("Process & Sync All Rows", type="primary"):
                        st.success(f"Successfully synced {len(df_upload)} participants to Google Sheets!")
                except: st.error("Error formatting CSV. Please match the template headers.")

# --- 7. HOST VIEW (CENTER MANAGER) ---
elif active_view == "Host":
    col_main, col_side = st.columns([2, 1])
    
    with col_side:
        with st.container(border=True):
            st.markdown("##### 🚨 Log Operational Issue")
            st.caption("Reports are instantly sent to Admins.")
            iss_rid = st.text_input("Respondent ID (Required)")
            iss_venue = st.selectbox("Issue Venue", [f"House {i+1}" for i in range(10)])
            iss_session = st.selectbox("Session Type", ["1 Pax", "2-3 Pax", "4-5 Pax"])
            iss_sev = st.selectbox("Severity", ["Low", "Medium", "High"])
            iss_note = st.text_area("Issue Description")
            
            if st.button("Submit Report", use_container_width=True, type="primary"):
                if iss_rid:
                    st.session_state.issues.append({
                        "resp_id": iss_rid, "venue": iss_venue, "session": iss_session,
                        "severity": iss_sev, "note": iss_note, "center": sel_center
                    })
                    st.success("Issue Logged.")
                else: st.error("Respondent ID is required.")

    with col_main:
        with st.container(border=True):
            st.markdown("##### Manage Venue Roster")
            c_sz, c_vn = st.columns(2)
            h_tab = c_sz.selectbox("Select Session Size", ["1 Pax", "2-3 Pax", "4-5 Pax"])
            v_sel = c_vn.selectbox("Select Venue", [f"House {j+1}" for j in range(10)])
            
            curr_tab = {"1 Pax":"1-", "2-3 Pax":"2-", "4-5 Pax":"4-"}[h_tab] + c_code
            df = fetch_tab_data(curr_tab)
            
            if not df.empty:
                v_df = df[df.get('Venue_Id', df.get('Venue Id')) == v_sel]
                if v_df.empty: st.info("No participants scheduled here yet.")
                for g_id, group in v_df.groupby(df.get('Group_Id', df.get('Group Id'))):
                    with st.expander(f"Group: {g_id}"):
                        for _, p in group.iterrows():
                            st.write(f"• ID: {p.get('Respondent_Id')} | Name: {p.get('First_Name')} | Status: **{p.get('Booking_Status')}**")
                        ca, cc, cn = st.columns(3)
                        if ca.button("Mark Arrived", key=f"a_{g_id}"): push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "Arrived"}); st.rerun()
                        if cc.button("Mark Completed", key=f"c_{g_id}"): push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "Completed"}); st.rerun()
                        if cn.button("Mark No-Show", key=f"n_{g_id}"): push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "No-Show"}); st.rerun()
            else: st.info("No roster data fetched.")
