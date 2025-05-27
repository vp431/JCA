import sqlite3
import os

def migrate_database():
    """
    Migration script to remove city_id from college table
    """
    print("Starting database migration...")
    
    # Database path
    db_path = 'instance/college_choice.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found.")
        return
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if city_id column exists in college table
        cursor.execute("PRAGMA table_info(college)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'city_id' in column_names:
            print("Found city_id column in college table. Starting migration...")
            
            # Create a new table without city_id
            cursor.execute("""
            CREATE TABLE college_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(200) NOT NULL
            )
            """)
            
            # Copy data from old table to new table
            cursor.execute("""
            INSERT INTO college_new (id, name)
            SELECT id, name FROM college
            """)
            
            # Drop old table and rename new table
            cursor.execute("DROP TABLE college")
            cursor.execute("ALTER TABLE college_new RENAME TO college")
            
            # Commit changes
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("No city_id column found in college table. No migration needed.")
    
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {str(e)}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()

# Check if database exists
if os.path.exists('instance/college_choice.db'):
    # Connect to the database
    conn = sqlite3.connect('instance/college_choice.db')
    cursor = conn.cursor()
    
    # Check if college table has cutoff_rank column
    cursor.execute("PRAGMA table_info(college)")
    college_columns = cursor.fetchall()
    college_has_cutoff = any(col[1] == 'cutoff_rank' for col in college_columns)
    
    # Check if college_branch table has cutoff_rank column
    cursor.execute("PRAGMA table_info(college_branch)")
    branch_columns = cursor.fetchall()
    branch_has_cutoff = any(col[1] == 'cutoff_rank' for col in branch_columns)
    
    # Begin transaction
    conn.execute("BEGIN TRANSACTION")
    
    try:
        # If college has cutoff_rank but college_branch doesn't, we need to migrate the data
        if college_has_cutoff and not branch_has_cutoff:
            print("Migrating cutoff ranks from college to college_branch...")
            
            # Add cutoff_rank column to college_branch
            cursor.execute("ALTER TABLE college_branch ADD COLUMN cutoff_rank INTEGER")
            
            # Get all colleges with cutoff_rank
            cursor.execute("SELECT id, cutoff_rank FROM college WHERE cutoff_rank IS NOT NULL")
            colleges = cursor.fetchall()
            
            # Update all branches of each college with the college's cutoff_rank
            for college_id, cutoff_rank in colleges:
                cursor.execute(
                    "UPDATE college_branch SET cutoff_rank = ? WHERE college_id = ?",
                    (cutoff_rank, college_id)
                )
            
            print(f"Updated {len(colleges)} colleges with cutoff ranks")
            
            # Commit changes
            conn.commit()
            print("Migration completed successfully!")
        elif not college_has_cutoff and branch_has_cutoff:
            print("Database schema is already updated.")
        elif not college_has_cutoff and not branch_has_cutoff:
            # Add cutoff_rank column to college_branch
            cursor.execute("ALTER TABLE college_branch ADD COLUMN cutoff_rank INTEGER")
            conn.commit()
            print("Added cutoff_rank column to college_branch table.")
        else:
            print("Both tables have cutoff_rank column. No migration needed.")
    
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        print(f"Error during migration: {e}")
    
    finally:
        # Close connection
        conn.close()
else:
    print("Database doesn't exist yet. No migration needed.") 