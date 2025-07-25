"""
SQLite database management for Onloq
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from utils.config import Config

class Database:
    def __init__(self, db_path: str = None):
        config = Config()
        self.db_path = db_path or config.get_database_path()
        self.conn = None
        
    def initialize(self):
        """Initialize database and create tables."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Create tables
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables."""
        
        # Activity logs table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,  -- 'app_focus', 'website_visit', 'system_event', 'idle'
                application TEXT,
                window_title TEXT,
                website_domain TEXT,
                duration_seconds INTEGER DEFAULT 0,
                metadata TEXT  -- JSON for additional data
            )
        """)
        
        # Code change logs table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS code_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT NOT NULL,
                change_type TEXT NOT NULL,  -- 'created', 'modified', 'deleted'
                file_size INTEGER,
                diff_content TEXT,  -- unified diff
                metadata TEXT  -- JSON for additional data
            )
        """)
        
        # System events table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,  -- 'login', 'logout', 'sleep', 'wake', 'network_on', 'network_off'
                metadata TEXT  -- JSON for additional data
            )
        """)
        
        # Create indexes for better performance
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_logs(timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_type ON activity_logs(event_type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_code_timestamp ON code_logs(timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_code_path ON code_logs(file_path)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_system_timestamp ON system_events(timestamp)")
        
        self.conn.commit()
    
    def log_activity(self, event_type: str, application: str = None, window_title: str = None, 
                    website_domain: str = None, duration_seconds: int = 0, metadata: Dict = None):
        """Log an activity event."""
        if not self.conn:
            self.initialize()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        self.conn.execute("""
            INSERT INTO activity_logs 
            (event_type, application, window_title, website_domain, duration_seconds, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event_type, application, window_title, website_domain, duration_seconds, metadata_json))
        
        self.conn.commit()
    
    def log_code_change(self, file_path: str, change_type: str, file_size: int = None, 
                       diff_content: str = None, metadata: Dict = None):
        """Log a code change event."""
        if not self.conn:
            self.initialize()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        self.conn.execute("""
            INSERT INTO code_logs 
            (file_path, change_type, file_size, diff_content, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (file_path, change_type, file_size, diff_content, metadata_json))
        
        self.conn.commit()
    
    def log_system_event(self, event_type: str, metadata: Dict = None):
        """Log a system event."""
        if not self.conn:
            self.initialize()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        self.conn.execute("""
            INSERT INTO system_events 
            (event_type, metadata)
            VALUES (?, ?)
        """, (event_type, metadata_json))
        
        self.conn.commit()
    
    def get_activity_logs(self, days: int = 1) -> List[Dict]:
        """Get activity logs for the specified number of days."""
        if not self.conn:
            self.initialize()
        
        since_date = datetime.now() - timedelta(days=days)
        
        cursor = self.conn.execute("""
            SELECT * FROM activity_logs 
            WHERE timestamp >= ? 
            ORDER BY timestamp DESC
        """, (since_date,))
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_code_logs(self, days: int = 1) -> List[Dict]:
        """Get code change logs for the specified number of days."""
        if not self.conn:
            self.initialize()
        
        since_date = datetime.now() - timedelta(days=days)
        
        cursor = self.conn.execute("""
            SELECT * FROM code_logs 
            WHERE timestamp >= ? 
            ORDER BY timestamp DESC
        """, (since_date,))
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_system_events(self, days: int = 1) -> List[Dict]:
        """Get system events for the specified number of days."""
        if not self.conn:
            self.initialize()
        
        since_date = datetime.now() - timedelta(days=days)
        
        cursor = self.conn.execute("""
            SELECT * FROM system_events 
            WHERE timestamp >= ? 
            ORDER BY timestamp DESC
        """, (since_date,))
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_recent_stats(self) -> Dict[str, Any]:
        """Get recent activity statistics."""
        if not self.conn:
            self.initialize()
        
        today = datetime.now().date()
        
        # Count unique apps today
        cursor = self.conn.execute("""
            SELECT COUNT(DISTINCT application) FROM activity_logs 
            WHERE DATE(timestamp) = ? AND event_type = 'app_focus'
        """, (today,))
        apps_today = cursor.fetchone()[0]
        
        # Count unique websites today
        cursor = self.conn.execute("""
            SELECT COUNT(DISTINCT website_domain) FROM activity_logs 
            WHERE DATE(timestamp) = ? AND event_type = 'website_visit' AND website_domain IS NOT NULL
        """, (today,))
        websites_today = cursor.fetchone()[0]
        
        # Count files changed today
        cursor = self.conn.execute("""
            SELECT COUNT(DISTINCT file_path) FROM code_logs 
            WHERE DATE(timestamp) = ?
        """, (today,))
        files_today = cursor.fetchone()[0]
        
        # Calculate total active time (non-idle time)
        cursor = self.conn.execute("""
            SELECT SUM(duration_seconds) FROM activity_logs 
            WHERE DATE(timestamp) = ? AND event_type != 'idle'
        """, (today,))
        active_seconds = cursor.fetchone()[0] or 0
        active_time = f"{active_seconds // 3600}h {(active_seconds % 3600) // 60}m"
        
        return {
            "apps_today": apps_today,
            "websites_today": websites_today,
            "files_today": files_today,
            "active_time": active_time
        }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
