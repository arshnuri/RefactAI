#!/usr/bin/env python3
"""
Script to check the database schema
"""

import sqlite3
import os

def check_schema():
    """
    Check the database schema to understand the table structure
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
        
        # List all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
        """)
        
        tables = cursor.fetchall()
        print("\nTables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Look for ProcessedFile-related tables
        processed_file_tables = [t[0] for t in tables if 'processedfile' in t[0].lower()]
        
        if processed_file_tables:
            table_name = processed_file_tables[0]
            print(f"\nUsing table: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"\nColumns in {table_name}:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Check for syntax error records
            cursor.execute(f"""
                SELECT COUNT(*) FROM {table_name} 
                WHERE error_message LIKE '%syntax%'
            """)
            
            syntax_error_count = cursor.fetchone()[0]
            print(f"\nRecords with 'syntax' in error_message: {syntax_error_count}")
            
            if syntax_error_count > 0:
                # Show a few examples
                cursor.execute(f"""
                    SELECT * FROM {table_name} 
                    WHERE error_message LIKE '%syntax%'
                    LIMIT 3
                """)
                
                print("\nExample records:")
                for row in cursor.fetchall():
                    print(f"  Row: {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == '__main__':
    check_schema()