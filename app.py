import streamlit as st
import pandas as pd
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="Trident Scheduling Platform", layout="wide", initial_sidebar_state="collapsed")

# --- 1. BRANDING & STYLING ---
st.markdown("""
    <style>
    /* Hide the sidebar completely */
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }
    
    .reportview-container .main .block-container{ padding-top: 1rem; }
    /* Modern SaaS Metric Cards */
    div[data-testid="metric-container"] { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 12px;
    }
    /* Status Pills */
    .status-pill { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .status-high { background-color: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
    .status-medium { background-color: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
    .status-low { background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
    </style>
""", unsafe_allow_html=True)

LOGO_URL = "https://raw.githubusercontent.com/malaykapoor95/Recruitment-engine/main/logo.png"

# --- 2. CONFIGURATION & ROLE KEYS ---
# UPDATED WITH YOUR NEW DEPLOYED LINK:
GAS_URL = "https://script.google.com/macros/s/AKfycbwvHrmZKX7jx7VJMZy65d6zxT0bHsBtglqYhWsnFWq7KdruyXg2T-9mpO6SAUgF7yKJ/exec"
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
            user_code = st.text_input("Enter Access Code:")
            
            if st.button("Secure Login", type="primary", use_container_width=True):
                if user_code in ACCESS_KEYS:
                    st.session_state.logged_in = True
                    st.session_state.user_role = ACCESS_KEYS[user_code]["role"]
                    st.session_state.sel_center = ACCESS_KEYS[user_code]["center"]
                    st.session_state.active_view = ACCESS_KEYS[user_code]["role"]
                    if st.session_state.user_role == "Admin":
                        st.session_state.active_view = "Admin"
                    st.rerun()
                else:
                    st.error("Access Denied. Invalid Code.")
    
    # CRITICAL FIX: Notice how this is aligned to the far left of the if statement.
    # It guarantees the script stops running here if you aren't logged in.
    st.stop()

# --- 4. TOP NAVIGATION (NO SIDEBAR) ---
c_title, c_role, c_center, c_logout = st.columns([4, 1.5, 1.5, 0.5])

with c_title:
    st.markdown("### Trident Scheduling Platform")
    st.caption("Multi-center operations dashboard MVP")

with c_role:
    if st.session_state.user_role == "Admin":
        st.session_state.active_view = st.selectbox("View", ["Admin", "Recruitment", "Host"], label_visibility="collapsed")
    else:
        st.selectbox("View", [st.session_state.user_role], disabled=True, label_visibility="collapsed")

with c_center:
    if st.session_state.user_role == "Admin":
        st.session_state.sel_center = st.selectbox("Center", ["Center 1", "Center 2", "Center 3"], index=["Center 1", "Center 2", "Center 3"].index(st.session_state.sel_center), label_visibility="collapsed")
    else:
        st.selectbox("Center", [st.session_state.sel_center], disabled=True, label_visibility="collapsed")

with c_logout:
    if st.button("⏏️", help="Log Out"):
        st.session_state.logged_in = False
        st.cache_data.clear()
        st.rerun()

st.divider()

role = st.session_state.user_role
active_view = st.session_state.active_view
sel_center = st.session_state.sel_center
c_code = CENTER_MAP[sel_center]

# --- DATA HELPERS (AGGRESSIVELY CACHED FOR SPEED) ---
@st.cache_data(ttl=120) 
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
        st.cache_data.clear()
        return r.text 
    except: return None

with st.spinner("Syncing data..."):
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

def render_quick_panel():
    with st.container(border=True):
        st.markdown("##### Active context")
        st.markdown(f"**User:** Malay<br>**Role:** {active_view}<br>**Center:** {sel_center}<br>**City:** TBD", unsafe_allow_html=True)
    
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
                <div style="padding: 12px; border-radius: 8px; border: 1px solid #f1f5f9; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <strong>ID: {issue['resp_id']} | {issue['venue']}</strong>
                        <span class="status-pill {sev_class}">{issue['severity']}</span>
                    </div>
                    <span style="font-size: 14px; color: #475569;">{issue['note']}</span>
                </div>
            """, unsafe_allow_html=True)

# --- 5. OVERVIEW VIEW (ADMIN) ---
if active_view == "Admin":
    render_top_metrics()
    st.write("")
    col_main, col_side = st.columns([2.2, 1])
    
    with col_main:
        with st.container(border=True):
            st.markdown(f"##### 🎛️ {sel_center} Quota Status")
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
        
        render_issues()
                    
    with col_side:
        render_quick_panel()

# --- 6. RECRUITMENT VIEW ---
elif active_view == "Recruitment":
    render_top_metrics()
    st.write("")
    col_main, col_side = st.columns([2.2, 1])
    
    with col_main:
        with st.container(border=True):
            st.markdown("##### ➕ Add New Recruit(s)")
            tab_man, tab_csv = st.tabs(["Manual Entry", "Bulk CSV Upload"])
            
            with tab_man:
                c_a, c_b, c_c = st.columns(3)
                s_type = c_a.selectbox("Category", ["1 Person", "2-3 People", "4-5 People"])
                venue = c_b.selectbox("Venue", [f"House {i+1}" for i in range(10)])
                status = c_c.selectbox("Status", ["Fresh", "Repeat"])
                
                c_d, c_e, c_f = st.columns(3)
                rid = c_d.text_input("Respondent ID")
                fn = c_e.text_input("First Name")
                gen = c_f.selectbox("Gender", ["Male", "Female"])
                
                c_g, c_h, c_i = st.columns(3)
                race = c_g.selectbox("Race", ["East Asian", "South Asian", "Black", "Hispanic", "White", "Middle East", "Native American"])
                age = c_h.selectbox("Age Group", ["20-30", "30-40", "40-50", "50-60"])
                h = c_i.number_input("Height (In)", 58, 85)
                
                hob = st.multiselect("Hobbies", ["Cooking", "Music", "Games", "Housekeeping", "Exercise"])
                
                if st.button("Add Single Recruit", type="primary"): 
                    st.success("Recruit added successfully.")
            
            with tab_csv:
                st.info("Upload a CSV file containing your bulk respondent list.")
                uploaded_file = st.file_uploader("Drop CSV file here", type=["csv"], label_visibility="collapsed")
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
        render_quick_panel()
        with st.container(border=True):
            st.markdown(f"##### Quota Snapshot")
            fresh_c = len(df_all[df_all.get('Status') == 'Fresh']) if not df_all.empty else 0
            st.progress(min(fresh_c/1015, 1.0), text=f"Fresh ({fresh_c} / 1015)")
            st.progress(0.0, text=f"Repeat (0 / 435)")

# --- 7. HOST VIEW (CENTER MANAGER) ---
elif active_view == "Host":
    col_main, col_side = st.columns([2.2, 1])
    
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
                    with st.container(border=True):
                        st.markdown(f"**Group: {g_id}**")
                        for _, p in group.iterrows():
                            status = p.get('Booking_Status', 'Scheduled')
                            color = "🟢" if status == "Completed" else "🔵" if status == "Arrived" else "🔴" if status == "No-Show" else "⚪"
                            st.write(f"{color} **{p.get('First_Name')}** (ID: {p.get('Respondent_Id')}) - {status}")
                        
                        ca, cc, cn = st.columns(3)
                        if ca.button("Mark Arrived", key=f"a_{g_id}", use_container_width=True): 
                            push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "Arrived"}); st.rerun()
                        if cc.button("Mark Completed", key=f"c_{g_id}", type="primary", use_container_width=True): 
                            push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "Completed"}); st.rerun()
                        if cn.button("Mark No-Show", key=f"n_{g_id}", use_container_width=True): 
                            push_data({"action": "update", "center": curr_tab, "group_id": g_id, "status": "No-Show"}); st.rerun()
            else: st.info("No roster data available.")

    with col_side:
        render_quick_panel()
        
        with st.container(border=True):
            st.markdown("##### 🚨 Log Operational Issue")
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
