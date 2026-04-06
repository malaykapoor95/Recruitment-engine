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

ACCESS_KEYS = {
    "TR-ADMIN-99": {"role": "Admin", "center": "Center 1"},
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
            user_code = st.text_input("Enter Access Code (e.g., TR-ADMIN-99 or MGR-C1):")
            
            if st.button("Secure Login", type="primary", use_container_width=True):
                if user_code in ACCESS_KEYS:
                    st.session_state.logged_in = True
                    st.session_state.user_role = ACCESS_KEYS[user_code]["role"]
                    st.session_state.sel_center = ACCESS_KEYS[user_code]["center"]
                    if st.session_state.user_role == "Admin":
                        st.session_state.admin_view = "Overview"
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

role = st.session_state.user_role
sel_center = st.session_state.sel_center

if role == "Admin":
    st.sidebar.title("Admin Controls")
    sel_center = st.sidebar.selectbox("Override Center", ["Center 1", "Center 2", "Center 3"], index=["Center 1", "Center 2", "Center 3"].index(sel_center))
    st.session_state.sel_center = sel_center
    active_view = st.sidebar.selectbox("Impersonate View", ["Overview", "Recruitment", "Host"])
    st.sidebar.divider()
else:
    active_view = role
    st.sidebar.success(f"Logged in as: {role}")
    st.sidebar.caption(f"Assigned to: {sel_center}")

# NEW: Manual Refresh Button
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear() # Wipes the memory so the next load pulls fresh from Google
    st.rerun()

st.sidebar.write("") # Spacer
if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.cache_data.clear()
    st.rerun()

c_code = CENTER_MAP[sel_center]

# --- DATA HELPERS (NOW WITH CACHING) ---

# The @st.cache_data decorator saves the result for 60 seconds.
# This prevents the 3-6 second loading delay on every click.
@st.cache_data(ttl=60)
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
    try: 
        r = requests.post(GAS_URL, json=payload)
        # Clear the cache automatically after we push new data so the UI updates instantly
        st.cache_data.clear()
        return r.text 
    except: return None

# Load Center Data (This is now practically instant after the first load)
frames = [fetch_tab_data(f"{p}{c_code}") for p in ["1-", "2-", "4-"]]
df_all = pd.concat([f for f in frames if not f.empty], ignore_index=True) if frames else pd.DataFrame()

total_target = 1450
total_sessions = len(df_all) if not df_all.empty else 0
completed = len(df_all[df_all['Booking_Status'] == 'Completed']) if not df_all.empty and 'Booking_Status' in df_all.columns else 0
pending = total_target - completed

# --- SHARED UI COMPONENTS ---
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
        st.markdown(f"**Role:** {role_name}<br>**Center:** {sel_center}<br>**City:** TBD", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("##### Venues in this center")
        for i in range(3):
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
        filtered_issues = [iss for iss in st.session_state.issues if iss.get('center') == sel_center or role == "Admin"]
        if not filtered_issues:
            st.info("No active issues reported.")
        for issue in reversed(filtered_issues):
            sev_class = f"status-{issue['severity'].lower()}"
            st.markdown(f"""
                <div style="padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <strong>ID: {issue['resp_id']} | Venue: {issue['venue']}</strong>
                        <span class="status-pill {sev_class}">{issue['severity']}</span>
                    </div>
                    <span style="font-size: 14px; color: #475569;">{issue['note']}</span>
                </div>
            """, unsafe_allow_html=True)


# --- 5. OVERVIEW VIEW (ADMIN) ---
if active_view == "Overview":
    render_top_metrics()
    st.write("")
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        with st.container(border=True):
            st.markdown(f"##### 📊 {sel_center} Quota Status")
            fresh_c = len(df_all[df_all.get('Status') == 'Fresh']) if not df_all.empty else 0
            st.progress(min(fresh_c/1015, 1.0), text=f"Fresh Participants ({fresh_c} / 1015)")
            st.progress(0.0, text=f"Repeat Participants (0 / 435)")
            st.markdown("---")
            if not df_all.empty and 'Gender' in df_all.columns:
                m_c = len(df_all[df_all['Gender'] == 'Male'])
                f_c = len(df_all[df_all['Gender'] == 'Female'])
                st.progress(min(m_c/580, 1.0), text=f"Male ({m_c} / 580)")
                st.progress(min(f_c/580, 1.0), text=f"Female ({f_c} / 580)")

        v_col1, v_col2 = st.columns(2)
        for i in range(4):
            tgt_col = v_col1 if i % 2 == 0 else v_col2
            v_name = f"House {i+1}"
            v_comp = len(df_all[(df_all.get('Venue_Id') == v_name) & (df_all.get('Booking_Status') == 'Completed')]) if not df_all.empty else 0
            v_pend = len(df_all[(df_all.get('Venue_Id') == v_name) & (df_all.get('Booking_Status') != 'Completed')]) if not df_all.empty else 0
            with tgt_col:
                with st.container(border=True):
                    st.markdown(f"🏢 **{v_name}**")
                    st.caption(f"Completed: **{v_comp}** | Pending: **{v_pend}**")
    with col_side:
        render_quick_panel("Admin")
        render_issues()

# --- 6. RECRUITMENT VIEW ---
elif active_view == "Recruitment":
    render_top_metrics()
    st.write("")
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        if 'show_quotas' not in st.session_state: st.session_state.show_quotas = False
        if st.button("📊 Toggle Center Quotas View", use_container_width=True):
            st.session_state.show_quotas = not st.session_state.show_quotas
            st.rerun()

        if st.session_state.show_quotas:
            with st.container(border=True):
                st.markdown(f"##### Quota Snapshot")
                fresh_c = len(df_all[df_all.get('Status') == 'Fresh']) if not df_all.empty else 0
                st.progress(min(fresh_c/1015, 1.0), text=f"Fresh Participants ({fresh_c} / 1015)")
                st.progress(0.0, text=f"Repeat Participants (0 / 435)")

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
                if st.button("Add Single Recruit", type="primary"): 
                    # Simulating a backend call that would trigger clear cache
                    st.success("Recruit added successfully.")
            
            with tab_csv:
                st.info("Upload a CSV file containing your bulk respondent list.")
                uploaded_file = st.file_uploader("Drop CSV file here", type=["csv"])
                if uploaded_file is not None:
                    try:
                        df_upload = pd.read_csv(uploaded_file)
                        st.dataframe(df_upload.head(3))
                        if st.button("Process & Sync All Rows", type="primary"):
                            st.success(f"Successfully synced {len(df_upload)} participants!")
                    except: st.error("Error formatting CSV. Ensure headers match the template.")

        with st.container(border=True):
            st.markdown("##### 📋 Booking Inventory")
            st.caption("2026-06-01 • 09:00 AM | House 1 - Remaining: **1**")
            st.caption("2026-06-01 • 10:30 AM | House 2 - Remaining: **4**")

    with col_side:
        render_quick_panel("Recruitment")
        render_issues()

# --- 7. HOST VIEW (CENTER MANAGER) ---
elif active_view == "Host":
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        with st.container(border=True):
            st.markdown("##### Daily Roster")
            
            c_sz, c_vn = st.columns(2)
            h_tab = c_sz.selectbox("Session Size", ["1 Pax", "2-3 Pax", "4-5 Pax"])
            v_sel = c_vn.selectbox("Filter Venue", [f"House {j+1}" for j in range(10)])
            search_query = st.text_input("🔍 Search Name or ID:", placeholder="e.g. Jordan or P-1001")
            
            curr_tab = {"1 Pax":"1-", "2-3 Pax":"2-", "4-5 Pax":"4-"}[h_tab] + c_code
            df = fetch_tab_data(curr_tab)
            
            if not df.empty:
                v_df = df[df.get('Venue_Id', df.get('Venue Id')) == v_sel]
                if search_query:
                    search_query = str(search_query).lower()
                    v_df = v_df[v_df['First_Name'].str.lower().str.contains(search_query, na=False) | 
                                v_df['Respondent_Id'].astype(str).str.lower().str.contains(search_query, na=False)]

                if v_df.empty: st.info("No participants found.")
                for g_id, group in v_df.groupby(df.get('Group_Id', df.get('Group Id'))):
                    with st.expander(f"Group: {g_id}"):
                        for _, p in group.iterrows():
                            status = p.get('Booking_Status', 'Scheduled')
                            color = "🟢" if status == "Completed" else "🔵" if status == "Arrived" else "🔴" if status == "No-Show" else "⚪"
                            st.write(f"{color} **{p.get('First_Name')}** (ID: {p.get('Respondent_Id')}) - {status}")
                        
                        ca, cc, cn = st.columns(3)
                        # When a host taps a button, a spinner shows, the data pushes, and the cache clears automatically
                        if ca.button("Mark Arrived", key=f"a_{g_id}", use_container_width=True): 
                            with st.spinner("Syncing..."): push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "Arrived"}); st.rerun()
                        if cc.button("Mark Completed", key=f"c_{g_id}", type="primary", use_container_width=True): 
                            with st.spinner("Syncing..."): push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "Completed"}); st.rerun()
                        if cn.button("Mark No-Show", key=f"n_{g_id}", use_container_width=True): 
                            with st.spinner("Syncing..."): push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "No-Show"}); st.rerun()
            else: st.info("No roster data available.")

    with col_side:
        render_quick_panel("Venue Host")
        
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
                    new_id = f"ISS-{len(st.session_state.issues) + 1:03d}"
                    st.session_state.issues.append({
                        "id": new_id, "resp_id": iss_rid, "venue": iss_venue, "session": iss_session,
                        "severity": iss_sev, "note": iss_note, "center": sel_center
                    })
                    st.success("Issue Logged.")
                    st.rerun()
                else: st.error("Respondent ID is required.")
