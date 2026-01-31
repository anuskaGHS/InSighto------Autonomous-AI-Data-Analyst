import sqlite3
import os

db_path = os.path.join("storage", "database.db")

if not os.path.exists(db_path):
    print("Database not found!")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=== USERS ===")
    try:
        cursor.execute("SELECT id, username, password_hash, created_at FROM user")
        users = cursor.fetchall()
        if not users:
            print("No users found.")
        for user in users:
            print(f"ID: {user[0]}, Username: {user[1]}, Hash: {user[2][:20]}..., Created: {user[3]}")
    except Exception as e:
        print(f"Error reading users: {e}")

    print("\n=== ANALYSIS LOGS ===")
    try:
        cursor.execute("SELECT id, user_id, uploaded_file_name, report_id, created_at FROM analysis_log")
        logs = cursor.fetchall()
        if not logs:
            print("No analysis logs found.")
        for log in logs:
            print(f"ID: {log[0]}, UserID: {log[1]}, File: {log[2]}, ReportID: {log[3]}, Created: {log[4]}")
    except Exception as e:
        print(f"Error reading logs: {e}")

    conn.close()
