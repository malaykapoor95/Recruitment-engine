import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Trident Ops", layout="wide")

# --- 1. DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect('trident_study_v2.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        center_id TEXT, venue_id TEXT, status TEXT, 
        first_name TEXT, last_name TEXT, age_group TEXT, 
        gender TEXT, race TEXT, height_inches INTEGER, 
        hobby TEXT, session_type TEXT, 
        scheduled_date TEXT, scheduled_time TEXT,
        group_id TEXT, -- Added to link people in the same session
        booking_status TEXT DEFAULT 'Scheduled'
    )''')
    conn.commit()
    conn.close()

init_db()

# --- 2. DATA UTILITIES ---
def run_query(query, params=()):
    with sqlite3.connect('trident_study_v2.db') as conn:
        conn.execute(query, params)
        conn.commit()

def get_data(query, params=()):
    with sqlite3.connect('trident_study_v2.db') as conn:
        return pd.read_sql_query(query, conn, params=params)

def get_height_tier(inches):
    if 58 <= inches <= 63: return "Tier 1: 4'10\"-5'2\""
    elif 64 <= inches <= 68: return "Tier 2: 5'3\"-5'7\""
    elif 69 <= inches <= 72: return "Tier 3: 5'8\"-6'1\""
    elif inches >= 73: return "Tier 4: 6'2\"+"
    return "Out of Range"

# --- 3. SESSION STATE FOR WIZARD ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'temp_data' not in st.session_state: st.session_state.temp_data = {}

# --- 4. SIDEBAR ---
role = st.sidebar.selectbox("Access Level", ["Overview", "Recruitment", "Host"])

# --- 5. RECRUITMENT VIEW (The Multi-Person Wizard) ---
if role == "Recruitment":
    st.header("Recruitment Portal")

    if st.session_state.step == 1:
        st.subheader("Step 1: Session Logistics")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            s_type = col1.selectbox("Session Category", ["1 Person session", "2-3 people session", "4-5 people session"])
            
            # Determine how many input rows to show
            if s_type == "1 Person session": num_pax = 1
            elif s_type == "2-3 people session": num_pax = col1.slider("Exact number of people?", 2, 3)
            else: num_pax = col1.slider("Exact number of people?", 4, 5)
            
            venue = col2.selectbox("Venue", [f"House {i+1}" for i in range(10)])
            s_date = col2.date_input("Date")
            s_time = col2.time_input("Time")

        # Collect data for each person
        pax_list = []
        for i in range(num_pax):
            st.markdown(f"**Participant {i+1} Details**")
            c1, c2, c3, c4 = st.columns(4)
            fn = c1.text_input(f"First Name", key=f"fn_{i}")
            ln = c2.text_input(f"Last Name", key=f"ln_{i}")
            race = c3.selectbox(f"Race", ["East Asian", "South Asian", "Black", "Hispanic", "White", "Middle East", "Native American"], key=f"r_{i}")
            height = c4.number_input(f"Height (In)", 58, 85, key=f"h_{i}")
            
            pax_list.append({"fn": fn, "ln": ln, "race": race, "height": height})

        if st.button("Review Summary →"):
            st.session_state.temp_data = {
                "s_type": s_type, "venue": venue, "date": str(s_date), 
                "time": str(s_time), "pax": pax_list
            }
            st.session_state.step = 2
            st.rerun()

    elif st.session_state.step == 2:
        st.subheader("Step 2: Confirm Recruitment")
        d = st.session_state.temp_data
        
        with st.container(border=True):
            st.write(f"**Session:** {d['s_type']} | **Venue:** {d['venue']}")
            st.write(f"**Scheduled for:** {d['date']} at {d['time']}")
            st.divider()
            st.table(pd.DataFrame(d['pax']))
        
        c1, c2 = st.columns(2)
        if c1.button("← Back (Edit)"):
            st.session_state.step = 1
            st.rerun()
        
        if c2.button("CONFIRM & BOOK ALL", type="primary"):
            group_id = datetime.now().strftime("%Y%m%d%H%M%S")
            for person in d['pax']:
                query = "INSERT INTO participants (center_id, venue_id, first_name, last_name, race, height_inches, session_type, scheduled_date, scheduled_time, group_id) VALUES (?,?,?,?,?,?,?,?,?,?)"
                run_query(query, ("Center 1", d['venue'], person['fn'], person['ln'], person['race'], person['height'], d['s_type'], d['date'], d['time'], group_id))
            
            st.success("All participants booked successfully!")
            st.session_state.step = 1
            st.session_state.temp_data = {}
            st.balloons()
            # No rerun here so they can see the success message

# --- 6. HOST VIEW ---
elif role == "Host":
    st.header("Host Dashboard")
    selected_venue = st.selectbox("Select Your Venue", [f"House {i+1}" for i in range(10)])
    df = get_data("SELECT * FROM participants WHERE venue_id=? ORDER BY scheduled_time ASC", (selected_venue,))
    
    if not df.empty:
        # Grouping by group_id so the host sees people in the same session together
        for g_id, group in df.groupby('group_id'):
            with st.expander(f"Session: {group.iloc[0]['scheduled_time']} ({len(group)} People)"):
                for _, row in group.iterrows():
                    st.write(f"{row['first_name']} {row['last_name']} - {row['booking_status']}")
                
                c1, c2 = st.columns(2)
                if c1.button("Check-in Group", key=f"in_{g_id}"):
                    run_query("UPDATE participants SET booking_status='Arrived' WHERE group_id=?", (g_id,))
                    st.rerun()
                if c2.button("Group Completed", key=f"out_{g_id}"):
                    run_query("UPDATE participants SET booking_status='Completed' WHERE group_id=?", (g_id,))
                    st.rerun()
    else: st.write("No sessions scheduled.")

# --- 7. OVERVIEW VIEW ---
else:
    st.header("Global Overview")
    all_data = get_data("SELECT * FROM participants")
    if not all_data.empty:
        st.metric("Total People Recruited", len(all_data))
        all_data['Height Tier'] = all_data['height_inches'].apply(get_height_tier)
        st.bar_chart(all_data['Height Tier'].value_counts())
    else: st.info("Waiting for data...")
