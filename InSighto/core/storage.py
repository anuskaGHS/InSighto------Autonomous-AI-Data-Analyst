import os
import sqlite3
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename
import config
import shutil
import json

class Storage:
    """Handles file uploads and database operations (Privacy First Architecture)"""
    
    def __init__(self):
        """Initialize storage and ensure folders/database exist"""
        # Create temp base folder
        os.makedirs(config.TEMP_FOLDER, exist_ok=True)
        
        # Create database if it doesn't exist
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Create sessions table (Metadata ONLY)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'uploaded'
            )
        ''')
        
        # NOTE: 'analysis_results' table removed for Privacy First compliance.
        # All data is now ephemeral file-based.
        
        conn.commit()
        conn.close()
    
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS
    
    def _get_session_dir(self, session_id):
        """Get or create the temporary directory for this session"""
        d = os.path.join(config.TEMP_FOLDER, session_id)
        os.makedirs(d, exist_ok=True)
        return d

    def save_upload(self, file, session_id):
        """Save uploaded file to TEMP session folder and register metadata in DB"""
        if file and self.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Create session directory
            session_dir = self._get_session_dir(session_id)
            
            # Save file temporarily
            filepath = os.path.join(session_dir, filename)
            file.save(filepath)
            
            # Register METADATA in database (No actual data content)
            conn = sqlite3.connect(config.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (session_id, filename, filepath, status)
                VALUES (?, ?, ?, 'uploaded')
            ''', (session_id, filename, filepath))
            conn.commit()
            conn.close()
            
            return filepath, filename
        
        return None, None
    
    def get_session(self, session_id):
        """Get session metadata from database"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, filename, filepath, uploaded_at, status
            FROM sessions
            WHERE session_id = ?
        ''', (session_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'session_id': result[0],
                'filename': result[1],
                'filepath': result[2],
                'uploaded_at': result[3],
                'status': result[4]
            }
        return None
    
    def update_session_status(self, session_id, status):
        """Update session status"""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE sessions
            SET status = ?
            WHERE session_id = ?
        ''', (status, session_id))
        conn.commit()
        conn.close()
    
    def save_analysis_result(self, session_id, result_type, result_data):
        """Save analysis result to TEMPORARY FILE (Not DB)"""
        try:
            session_dir = self._get_session_dir(session_id)
            filepath = os.path.join(session_dir, f"{result_type}.json")
            
            # If result_data is already a string (json dumped), write it directly
            # If it's an object, dump it.
            if isinstance(result_data, str):
                with open(filepath, 'w') as f:
                    f.write(result_data)
            else:
                with open(filepath, 'w') as f:
                    json.dump(result_data, f, indent=2)
                    
        except Exception as e:
            print(f"Error saving analysis result {result_type}: {e}")
    
    def get_analysis_result(self, session_id, result_type):
        """Get analysis result from TEMPORARY FILE"""
        try:
            session_dir = self._get_session_dir(session_id)
            filepath = os.path.join(session_dir, f"{result_type}.json")
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return f.read() # Return as string to match previous API
            return None
        except Exception as e:
            print(f"Error reading analysis result {result_type}: {e}")
            return None

    def clear_session_data(self, session_id):
        """PERMANENTLY DELETE all session data"""
        try:
            session_dir = os.path.join(config.TEMP_FOLDER, session_id)
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)
                print(f"Privacy Cleanup: Wiped data for session {session_id}")
                return True
        except Exception as e:
            print(f"Error clearing session data: {e}")
            return False
    
    def load_dataframe(self, filepath):
        """Load CSV or Excel file into pandas DataFrame"""
        try:
            # Get file extension
            file_ext = filepath.rsplit('.', 1)[1].lower()
            
            # Load based on extension
            if file_ext == 'csv':
                df = pd.read_csv(filepath)
            elif file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(filepath)
            else:
                return None
            
            return df
        except Exception as e:
            print(f"Error loading file: {e}")
            return None
    
    def save_dataframe(self, df, session_id, suffix='cleaned'):
        """Save DataFrame to storage folder"""
        try:
            # Create filename
            filename = f"{session_id}_{suffix}.csv"
            
            # Privacy First: Save to session temp dir
            session_dir = self._get_session_dir(session_id)
            filepath = os.path.join(session_dir, filename)
            
            # Save as CSV
            df.to_csv(filepath, index=False)
            
            return filepath
        except Exception as e:
            print(f"Error saving dataframe: {e}")
            return None