import sqlite3

def validate_booking(center_id, status, affiliation):
    conn = sqlite3.connect('trident_ops.db')
    c = conn.cursor()
    
    # 1. Exclusion Check [cite: 130]
    exclusions = ['Google', 'Meta', 'Microsoft', 'Amazon', 'Apple', 'Sony']
    if any(ex in affiliation for ex in exclusions):
        return False, "Error: Participant has restricted company affiliation."

    # 2. Repeat Participant Cap 
    if status == 'Repeat':
        c.execute("SELECT COUNT(*) FROM participants WHERE center_id=? AND status='Repeat'", (center_id,))
        count = c.fetchone()[0]
        if count >= 435:
            return False, "Error: Repeat participant quota (435) is full for this center."
            
    conn.close()
    return True, "Success"