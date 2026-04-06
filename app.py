import streamlit as st
import pandas as pd
import sqlite3

# --- STEP 1: AUTO-INITIALIZE DATABASE ---
def init_db():
    conn = sqlite3.connect('trident_ops.db')
    c = conn.cursor()
    # This creates the table if it doesn't exist yet
    c.execute('''CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        center_id TEXT,          -- Center 1, 2, or 3
        venue_id TEXT,           -- 10-20 per center
        status TEXT,             -- Fresh or Repeat
        first_name TEXT,
        last_name TEXT,
        age_group TEXT,          -- 20-30, 30-40, 40-50, 50-60 [cite: 8-11]
        gender TEXT,             -- Male or Female [cite: 13-14]
        race TEXT,               -- East Asian, South Asian, etc. [cite: 34-40]
        height_inches INTEGER,   -- Map to 4 tiers [cite: 16-20]
        hobby TEXT,              -- Cooking, Music, etc. [cite: 28-32]
        session_type TEXT,       -- 1-pax, 2-3 pax, 4-5 pax [cite: 24-26]
        booking_status TEXT DEFAULT 'Scheduled',
        affiliation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

# Run initialization immediately
init_db()

# --- STEP 2: DATA RETRIEVAL FUNCTION ---
def get_data(query, params=()):
    conn = sqlite3.connect('trident_ops.db')
    try:
        df = pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        # If the table is missing, return an empty DataFrame instead of crashing
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

# --- STEP 3: DASHBOARD VIEWS ---
st.title("Trident Global Multi-Center Command")
# (Rest of your app code below...)
