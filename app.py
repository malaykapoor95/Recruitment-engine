import streamlit as st
import pandas as pd
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="Trident Scheduling Platform", layout="wide", initial_sidebar_state="collapsed")

# --- 1. BRANDING & STYLING ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }
    .reportview-container .main .block-container{ padding-top: 1rem; }
    div[data-testid="metric-container"] { background-color: #ffffff; padding: 15px; border-radius: 12px; }
    .status-pill { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .status-high { background-color: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
    .status-medium { background-color: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
    .status-low { background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
    </style>
""", unsafe_allow_html=True)

LOGO_URL = "https://raw.githubusercontent.com/malaykapoor95/Recruitment-engine/main/logo.png"
GAS_URL = "https://script.google.com/macros/s/AKfycbwvHrmZKX7jx7VJMZy65d6zxT0bHsBtglqYhWsnFWq7KdruyXg2T-9mpO6SAUgF7yKJ/exec"

ACCESS_KEYS = {
    "TR-ADMIN-99": {"role": "Admin", "center": "Center 1"},
    "REC-C1": {"role": "Recruitment", "center": "Center 1"},
    "REC-C2": {"role": "Recruitment", "center": "Center 2"},
    "REC-C3": {"role": "Recruitment", "center": "Center 3"},
    "MGR-C1": {"role": "Host", "center": "Center 1"},
    "MGR-C2": {"role": "Host", "center": "Center 2"},
    "MGR-C3": {"role": "Host", "center": "Center 3"},
}

# --- 2. SESSION INITIALIZATION & FAILSAFE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'issues' not in st.session_state: st.session_state.issues = []

if st.session_state.logged_in and 'active_view' not in st.session_state:
    st.session_state.logged_in = False
    st.rerun()

# --- 3. LOGIN GATE ---
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
                    st.session_state.active_view = ACCESS_KEYS[user_code]["role"]
                    if st.session_state.user_role == "Admin":
                        st.session_state.active_view = "Admin"
                    st.rerun()
                else:
                    st.error("Access Denied. Invalid Code.")

# --- 4. THE MASTER_DB DASHBOARD ---
else:
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
            curr_index = 0
            if st.session_state.sel_center in ["Center 1", "Center 2", "Center 3"]:
                curr_index = ["Center 1", "Center 2", "Center 3"].index(st.session_state.sel_center)
            st.session_state.sel_center = st.selectbox("Center", ["Center 1", "Center 2", "Center 3"], index=curr_index, label_visibility="collapsed")
        else:
            st.selectbox("Center", [st.session_state.sel_center], disabled=True, label_visibility="collapsed")

    with c_logout:
        if st.button("⏏️", help="Log Out"):
            st.cache_data.clear()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.divider()

    role = st.session_state.user_role
    active_view = st.session_state.active_view
    sel_center = st.session_state.sel_center

    # --- THE MAGIC SPEED UP: FETCH ONLY MASTER_DB ONCE ---
    @st.cache_data(ttl=120) 
    def fetch_master_data():
        try:
            r = requests.get(f"{GAS_URL}?tab=Master_DB")
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

    with st.spinner("Syncing Master Database..."):
        df_master = fetch_master_data()
        
        if not df_master.empty and 'Center' in df_master.columns:
            df_center = df_master[df_master['Center'] == sel_center]
        else:
            df_center = pd.DataFrame()

    total_target = 1450 
    total_sessions = len(df_center)
    completed = len(df_center[df_center['Booking_Status'] == 'Completed']) if not df_center.empty and 'Booking_Status' in df_center.columns else 0
    pending = total_target - completed

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
                v_comp = len(df_center[(df_center['Venue_Id'] == v_name) & (df_center['Booking_Status'] == 'Completed')]) if not df_center.empty and 'Venue_Id' in df_center.columns and 'Booking_Status' in df_center.columns else 0
                v_pend = len(df_center[(df_center['Venue_Id'] == v_name) & (df_center['Booking_Status'] != 'Completed')]) if not df_center.empty and 'Venue_Id' in df_center.columns and 'Booking_Status' in df_center.columns else 0
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
                fresh_c = len(df_center[df_center['Status'] == 'Fresh']) if not df_center.empty and 'Status' in df_center.columns else 0
                st.progress(min(fresh_c/1015, 1.0) if fresh_c else 0.0, text=f"Fresh Participants ({fresh_c} / 1015)")
                st.progress(0.0, text=f"Repeat Participants (0 / 435)")
                st.markdown("---")
                if not df_center.empty and 'Gender' in df_center.columns:
                    m_c = len(df_center[df_center['Gender'] == 'Male'])
                    f_c = len(df_center[df_center['Gender'] == 'Female'])
                    st.progress(min(m_c/580, 1.0) if m_c else 0.0, text=f"Male ({m_c} / 580)")
                    st.progress(min(f_c/580, 1.0) if f_c else 0.0, text=f"Female ({f_c} / 580)")

            v_col1, v_col2 = st.columns(2)
            for i in range(4):
                tgt_col = v_col1 if i % 2 == 0 else v_col2
                v_name = f"House {i+1}"
                v_comp = len(df_center[(df_center['Venue_Id'] == v_name) & (df_center['Booking_Status'] == 'Completed')]) if not df_center.empty and 'Venue_Id' in df_center.columns and 'Booking_Status' in df_center.columns else 0
                v_pend = len(df_center[(df_center['Venue_Id'] == v_name) & (df_center['Booking_Status'] != 'Completed')]) if not df_center.empty and 'Venue_Id' in df_center.columns and 'Booking_Status' in df_center.columns else 0
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
                    s_type = c_a.selectbox("Category", ["1 Person session", "2-3 people session", "4-5 people session"])
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
                    
                    c_j, c_k = st.columns(2)
                    r_date = c_j.date_input("Scheduled Date")
                    r_time = c_k.time_input("Scheduled Time")
                    
                    hob = st.multiselect("Hobbies", ["Cooking", "Music", "Games", "Housekeeping", "Exercise"])
                    
                    if st.button("Add Single Recruit", type="primary"):
                        if not rid or not fn:
                            st.error("Respondent ID and First Name are required.")
                        else:
                            hobbies_str = ", ".join(hob)
                            payload = {
                                "action": "add",
                                "type": s_type,
                                "venue": venue,
                                "center_name": sel_center,
                                "date": str(r_date),
                                "time": str(r_time),
                                "pax": [{
                                    "rid": rid, "fn": fn, "status": status, "gender": gen, 
                                    "race": race, "height": h, "age": age, "hobbies": hobbies_str
                                }]
                            }
                            with st.spinner("Syncing to Master_DB..."):
                                push_data(payload)
                                st.success(f"{fn} added successfully!")
                                st.rerun()
                
                with tab_csv:
                    st.info("Upload a CSV file containing your bulk respondent list.")
                    uploaded_file = st.file_uploader("Drop CSV file here", type=["csv"], label_visibility="collapsed")
                    if uploaded_file is not None:
                        try:
                            df_upload = pd.read_csv(uploaded_file)
                            st.dataframe(df_upload.head(3))
                            
                            if st.button("Process & Sync All Rows", type="primary"):
                                pax_list = []
                                for _, row in df_upload.iterrows():
                                    pax_list.append({
                                        "rid": str(row.get('Respondent_ID', '')),
                                        "fn": str(row.get('First_Name', '')),
                                        "status": str(row.get('Status', 'Fresh')),
                                        "gender": str(row.get('Gender', '')),
                                        "race": str(row.get('Race', '')),
                                        "height": str(row.get('Height', '')),
                                        "age": str(row.get('Age_Group', '')),
                                        "hobbies": str(row.get('Hobbies', ''))
                                    })
                                
                                payload = {
                                    "action": "add",
                                    "type": s_type, 
                                    "venue": venue, 
                                    "center_name": sel_center,
                                    "date": str(r_date),
                                    "time": str(r_time),
                                    "pax": pax_list
                                }
                                with st.spinner(f"Batch syncing {len(df_upload)} rows..."):
                                    push_data(payload)
                                    st.success(f"Successfully synced {len(df_upload)} participants!")
                                    st.rerun()
                        except Exception as e: 
                            st.error(f"Error reading CSV: Ensure headers match exactly. {e}")

            with st.container(border=True):
                st.markdown("##### 📋 Booking Inventory")
                st.caption("2026-06-01 • 09:00 AM | House 1 - Remaining: **1**")
                st.caption("2026-06-01 • 10:30 AM | House 2 - Remaining: **4**")

        with col_side:
            render_quick_panel()
            
            with st.container(border=True):
                st.markdown(f"##### Quota Snapshot")
                fresh_c = len(df_center[df_center['Status'] == 'Fresh']) if not df_center.empty and 'Status' in df_center.columns else 0
                rep_c = len(df_center[df_center['Status'] == 'Repeat']) if not df_center.empty and 'Status' in df_center.columns else 0
                st.progress(min(fresh_c/1015, 1.0) if fresh_c else 0.0, text=f"Fresh ({fresh_c} / 1015)")
                st.progress(min(rep_c/435, 1.0) if rep_c else 0.0, text=f"Repeat ({rep_c} / 435)")
                
                st.markdown("---")
                m_c = len(df_center[df_center['Gender'] == 'Male']) if not df_center.empty and 'Gender' in df_center.columns else 0
                f_c = len(df_center[df_center['Gender'] == 'Female']) if not df_center.empty and 'Gender' in df_center.columns else 0
                st.progress(min(m_c/580, 1.0) if m_c else 0.0, text=f"Male ({m_c} / 580)")
                st.progress(min(f_c/580, 1.0) if f_c else 0.0, text=f"Female ({f_c} / 580)")
                
                st.markdown("---")
                age_c = len(df_center[df_center['Age_Group'] == '30-40']) if not df_center.empty and 'Age_Group' in df_center.columns else 0
                st.progress(min(age_c/435, 1.0) if age_c else 0.0, text=f"Age 30-40 ({age_c} / 435)")
                
                ea_c = len(df_center[df_center['Race'] == 'East Asian']) if not df_center.empty and 'Race' in df_center.columns else 0
                st.progress(min(ea_c/145, 1.0) if ea_c else 0.0, text=f"East Asian ({ea_c} / 145)")
                
            render_issues()

    # --- 7. HOST VIEW (CENTER MANAGER) ---
    elif active_view == "Host":
        col_main, col_side = st.columns([2.2, 1])
        
        with col_main:
            with st.container(border=True):
                st.markdown("##### Daily Roster")
                
                c_sz, c_vn = st.columns(2)
                h_tab = c_sz.selectbox("Session Size", ["1 Person session", "2-3 people session", "4-5 people session"])
                v_sel = c_vn.selectbox("Filter Venue", [f"House {j+1}" for j in range(10)])
                search_query = st.text_input("🔍 Search Name or ID:", placeholder="e.g. Jordan or P-1001")
                
                if not df_center.empty:
                    v_col = 'Venue_Id' if 'Venue_Id' in df_center.columns else ('Venue Id' if 'Venue Id' in df_center.columns else None)
                    g_col = 'Group_Id' if 'Group_Id' in df_center.columns else ('Group Id' if 'Group Id' in df_center.columns else None)
                    fn_col = 'First_Name' if 'First_Name' in df_center.columns else ('First Name' if 'First Name' in df_center.columns else None)
                    rid_col = 'Respondent_Id' if 'Respondent_Id' in df_center.columns else ('Respondent Id' if 'Respondent Id' in df_center.columns else None)
                    s_col = 'Session_Type' if 'Session_Type' in df_center.columns else ('Session Type' if 'Session Type' in df_center.columns else None)
                    
                    if v_col and g_col and s_col:
                        v_df = df_center[(df_center[v_col] == v_sel) & (df_center[s_col] == h_tab)]
                        
                        if search_query and fn_col and rid_col:
                            sq = str(search_query).lower()
                            v_df = v_df[v_df[fn_col].astype(str).str.lower().str.contains(sq, na=False) | 
                                        v_df[rid_col].astype(str).str.lower().str.contains(sq, na=False)]

                        if v_df.empty: st.info(f"No participants found for {h_tab} at {v_sel}.")
                        for g_id, group in v_df.groupby(g_col):
                            with st.container(border=True):
                                st.markdown(f"**Group: {g_id}**")
                                for _, p in group.iterrows():
                                    status = p.get('Booking_Status', 'Scheduled')
                                    color = "🟢" if status == "Completed" else "🔵" if status == "Arrived" else "🔴" if status == "No-Show" else "⚪"
                                    p_name = p.get(fn_col, 'Unknown') if fn_col else 'Unknown'
                                    p_id = p.get(rid_col, 'N/A') if rid_col else 'N/A'
                                    st.write(f"{color} **{p_name}** (ID: {p_id}) - {status}")
                                
                                ca, cc, cn = st.columns(3)
                                if ca.button("Mark Arrived", key=f"a_{g_id}", use_container_width=True): 
                                    push_data({"action": "update", "group_id": g_id, "status": "Arrived"}); st.rerun()
                                if cc.button("Mark Completed", key=f"c_{g_id}", type="primary", use_container_width=True): 
                                    push_data({"action": "update", "group_id": g_id, "status": "Completed"}); st.rerun()
                                if cn.button("Mark No-Show", key=f"n_{g_id}", use_container_width=True): 
                                    push_data({"action": "update", "group_id": g_id, "status": "No-Show"}); st.rerun()
                    else:
                        st.error("Error: Could not find required 'Venue_Id', 'Session_Type', or 'Group_Id' columns in Master_DB.")
                else: st.info("No roster data available.")

        with col_side:
            render_quick_panel()
            
            with st.container(border=True):
                st.markdown("##### 🚨 Log Operational Issue")
                iss_rid = st.text_input("Respondent ID (Required)")
                iss_venue = st.selectbox("Issue Venue", [f"House {i+1}" for i in range(10)])
                iss_session = st.selectbox("Session Type", ["1 Person session", "2-3 people session", "4-5 people session"])
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
