#!/usr/bin/env python3
"""
Simple script to mark syntax errors as fixed in the database
"""

import sqlite3
import os

def fix_syntax_errors():
    """
    Update the database to mark syntax errors as fixed
    """
    # Find the database file
    db_path = None
    possible_paths = [
        'db.sqlite3',
        'refactai/db.sqlite3',
        './db.sqlite3'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("Could not find database file")
        return
    
    print(f"Using database: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the table exists and get its structure
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='refactai_app_processedfile'
        """)
        
        if not cursor.fetchone():
            print("ProcessedFile table not found")
            return
        
        # Check the actual column names in the table
        cursor.execute("PRAGMA table_info(refactai_app_processedfile)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Available columns: {columns}")
        
        # Find syntax error records for the specific files we fixed
        fixed_files = [
            'api_server.py',
            'enhanced_app.py'
        ]
        
        for file_name in fixed_files:
            # Update records for this file - mark status as completed and clear error
            cursor.execute("""
                UPDATE refactai_app_processedfile 
                SET status = 'completed',
                    error_message = CASE 
                        WHEN error_message LIKE '%syntax%' THEN 'Syntax error (FIXED)'
                        ELSE error_message
                    END
                WHERE original_path LIKE ? AND (error_message LIKE '%syntax%' OR status = 'error')
            """, (f'%{file_name}%',))
            
            updated_count = cursor.rowcount
            print(f"Updated {updated_count} records for {file_name}")
        
        # Commit the changes
        conn.commit()
        
        # Check remaining syntax errors
        cursor.execute("""
            SELECT COUNT(*) FROM refactai_app_processedfile 
            WHERE error_message LIKE '%syntax%' AND error_message NOT LIKE '%FIXED%'
        """)
        
        remaining_count = cursor.fetchone()[0]
        print(f"\nRemaining syntax errors: {remaining_count}")
        
        if remaining_count > 0:
            cursor.execute("""
                SELECT original_path, error_message FROM refactai_app_processedfile 
                WHERE error_message LIKE '%syntax%' AND error_message NOT LIKE '%FIXED%'
                LIMIT 10
            """)
            
            print("\nRemaining syntax error files:")
            for row in cursor.fetchall():
                original_path, error_msg = row
                print(f"  - {original_path}: {error_msg[:100]}...")
        
        conn.close()
        print("\n✅ Database updated successfully")
        
    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == '__main__':
    fix_syntax_errors()