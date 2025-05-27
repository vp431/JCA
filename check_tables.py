import sqlite3

def check_tables():
    # Connect to the database
    conn = sqlite3.connect('college_choice.db')
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Tables in the database:")
    for table in tables:
        print(f"- {table[0]}")
        
        # Get column info for each table
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print("  Columns:")
        for col in columns:
            # col format: (cid, name, type, notnull, dflt_value, pk)
            print(f"  - {col[1]} ({col[2]}), {'NOT NULL' if col[3] else 'NULL'}, {'PK' if col[5] else ''}")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_tables() 