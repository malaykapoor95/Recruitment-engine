import sqlite3

def init_db():
    conn = sqlite3.connect('trident_ops.db')
    c = conn.cursor()
    
    # Core Table: Participants
    c.execute('''CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        center_id TEXT,          -- Center 1, 2, or 3
        venue_id TEXT,           -- 10-20 per center
        status TEXT,             -- Fresh or Repeat (Cap: 435) 
        first_name TEXT,
        last_name TEXT,
        age_group TEXT,          -- 20-30, 30-40, 40-50, 50-60 [cite: 166]
        gender TEXT,             -- Male or Female [cite: 171]
        race TEXT,               -- East Asian, South Asian, etc. [cite: 192]
        height_inches INTEGER,   -- Map to tiers [cite: 174]
        hobby TEXT,              -- Cooking, Music, etc. [cite: 186]
        session_type TEXT,       -- 1-pax, 2-3 pax, 4-5 pax [cite: 183-185]
        booking_status TEXT DEFAULT 'Scheduled', -- Arrived, Completed, No-Show
        affiliation TEXT,        -- Check for exclusions (Google, Meta, etc.) [cite: 130]
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()
    print("Database Initialized Successfully.")

if __name__ == "__main__":
    init_db()