from app import app, db, City
import sqlite3
import os

def migrate_city_schema():
    """
    Migration script to remove connectivity and custom_connectivity columns from City table.
    This script does the following:
    1. Check if the database file exists
    2. Create a new table without the connectivity columns
    3. Copy data from the old table to the new one
    4. Drop the old table
    5. Rename the new table to the original name
    """
    print("Starting migration of City schema...")
    
    # Check if database file exists
    db_path = 'college_choice.db'
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        
        # Check if there's a database file in the instance folder
        instance_db_path = os.path.join('instance', 'college_choice.db')
        if os.path.exists(instance_db_path):
            db_path = instance_db_path
            print(f"Found database at {db_path}")
        else:
            print("No database file found. Will recreate it with the correct schema.")
            # Force create database with updated schema
            with app.app_context():
                db.create_all()
            return
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if city table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='city'")
        if not cursor.fetchone():
            print("City table doesn't exist. Creating the database with the updated schema.")
            # Force create database with updated schema
            with app.app_context():
                db.create_all()
            return
        
        # Check if connectivity column exists in city table
        cursor.execute("PRAGMA table_info(city)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'connectivity' not in column_names:
            print("City table already doesn't have connectivity column. No migration needed.")
            return
        
        print("Creating new city table without connectivity columns...")
        
        # Create a backup of the city data
        cursor.execute("CREATE TABLE IF NOT EXISTS city_backup AS SELECT * FROM city")
        print("Created backup of city table")
        
        # Drop the current city table
        cursor.execute("DROP TABLE city")
        print("Dropped old city table")
        
        # Create new table with correct schema
        cursor.execute('''
        CREATE TABLE city (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
        ''')
        print("Created new city table with updated schema")
        
        # Copy data from backup to new table
        cursor.execute('''
        INSERT INTO city (id, name)
        SELECT id, name FROM city_backup
        ''')
        print("Copied data from backup to new table")
        
        # Drop backup table
        cursor.execute("DROP TABLE city_backup")
        print("Dropped backup table")
        
        # Commit changes
        conn.commit()
        print("City schema migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_city_schema() 