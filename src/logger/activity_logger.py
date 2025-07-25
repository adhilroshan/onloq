"""
Activity logger for tracking applications, websites, and system events
"""

import time
import threading
import psutil
import re
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse

try:
    import win32gui
    import win32process
    import win32con
    WINDOWS_SUPPORT = True
except ImportError:
    WINDOWS_SUPPORT = False

try:
    from pynput import mouse, keyboard
    PYNPUT_SUPPORT = True
except ImportError:
    PYNPUT_SUPPORT = False

from storage.database import Database
from utils.config import Config

class ActivityLogger:
    def __init__(self, database: Database):
        self.db = database
        self.config = Config()
        self.settings = self.config.get_activity_settings()
        
        self.running = False
        self.last_activity_time = time.time()
        self.current_app = None
        self.current_window = None
        self.current_domain = None
        self.app_start_time = None
        
        # Track idle state
        self.idle_threshold = self.settings.get("idle_threshold_minutes", 5) * 60
        self.poll_interval = self.settings.get("poll_interval_seconds", 5)
        
        # Input tracking for idle detection
        if PYNPUT_SUPPORT:
            self.mouse_listener = None
            self.keyboard_listener = None
            self._setup_input_listeners()
    
    def _setup_input_listeners(self):
        """Setup mouse and keyboard listeners for idle detection."""
        if not PYNPUT_SUPPORT:
            return
        
        def on_activity(*args):
            self.last_activity_time = time.time()
        
        self.mouse_listener = mouse.Listener(
            on_move=on_activity,
            on_click=on_activity,
            on_scroll=on_activity
        )
        
        self.keyboard_listener = keyboard.Listener(
            on_press=on_activity,
            on_release=on_activity
        )
    
    def _get_active_window_info(self) -> Dict[str, Optional[str]]:
        """Get information about the currently active window."""
        if not WINDOWS_SUPPORT:
            return {"app": None, "title": None, "domain": None}
        
        try:
            # Get the active window
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return {"app": None, "title": None, "domain": None}
            
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process info
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            app_name = process.name()
            
            # Try to extract domain from browser windows
            domain = self._extract_domain_from_title(window_title, app_name)
            
            return {
                "app": app_name,
                "title": window_title,
                "domain": domain
            }
            
        except Exception as e:
            print(f"Error getting window info: {e}")
            return {"app": None, "title": None, "domain": None}
    
    def _extract_domain_from_title(self, title: str, app_name: str) -> Optional[str]:
        """Extract domain from browser window title."""
        if not title:
            return None
        
        # Common browsers
        browsers = ["chrome.exe", "firefox.exe", "msedge.exe", "safari.exe", "opera.exe", "brave.exe"]
        
        if app_name.lower() not in browsers:
            return None
        
        # Common patterns for extracting domains from browser titles
        patterns = [
            r"https?://([^/\s]+)",  # Full URL
            r"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",  # Domain pattern
            r"- ([^-\s]+\.[a-zA-Z]{2,})",  # After dash
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                domain = match.group(1)
                # Clean up the domain
                domain = domain.strip().lower()
                # Remove common prefixes
                domain = re.sub(r"^www\.", "", domain)
                return domain
        
        return None
    
    def _log_app_change(self, new_app: str, new_title: str, new_domain: str):
        """Log application/window change."""
        current_time = time.time()
        
        # Log duration of previous app if it existed
        if self.current_app and self.app_start_time:
            duration = int(current_time - self.app_start_time)
            if duration > 0:
                self.db.log_activity(
                    event_type="app_focus",
                    application=self.current_app,
                    window_title=self.current_window,
                    website_domain=self.current_domain,
                    duration_seconds=duration
                )
        
        # Update current state
        self.current_app = new_app
        self.current_window = new_title
        self.current_domain = new_domain
        self.app_start_time = current_time
        
        # Log website visit if domain changed and is present
        if new_domain and new_domain != self.current_domain:
            self.db.log_activity(
                event_type="website_visit",
                application=new_app,
                website_domain=new_domain,
                metadata={"title": new_title}
            )
    
    def _check_idle_state(self):
        """Check if user is idle and log accordingly."""
        current_time = time.time()
        time_since_activity = current_time - self.last_activity_time
        
        if time_since_activity > self.idle_threshold:
            # User is idle
            self.db.log_activity(
                event_type="idle",
                duration_seconds=int(time_since_activity),
                metadata={"idle_threshold_minutes": self.idle_threshold / 60}
            )
            
            # Reset activity time to avoid repeated idle logs
            self.last_activity_time = current_time
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Get current window info
                window_info = self._get_active_window_info()
                app = window_info["app"]
                title = window_info["title"]
                domain = window_info["domain"]
                
                # Check if app/window changed
                if (app != self.current_app or 
                    title != self.current_window or 
                    domain != self.current_domain):
                    
                    self._log_app_change(app, title, domain)
                
                # Check idle state
                self._check_idle_state()
                
                # Sleep until next poll
                time.sleep(self.poll_interval)
                
            except Exception as e:
                print(f"Error in activity monitoring: {e}")
                time.sleep(self.poll_interval)
    
    def start(self):
        """Start activity logging."""
        if self.running:
            return
        
        self.running = True
        self.last_activity_time = time.time()
        
        # Start input listeners
        if PYNPUT_SUPPORT and self.mouse_listener and self.keyboard_listener:
            self.mouse_listener.start()
            self.keyboard_listener.start()
        
        # Log system startup
        self.db.log_system_event("session_start")
        
        # Start monitoring loop
        self._monitor_loop()
    
    def stop(self):
        """Stop activity logging."""
        if not self.running:
            return
        
        self.running = False
        
        # Log final app duration
        if self.current_app and self.app_start_time:
            duration = int(time.time() - self.app_start_time)
            if duration > 0:
                self.db.log_activity(
                    event_type="app_focus",
                    application=self.current_app,
                    window_title=self.current_window,
                    website_domain=self.current_domain,
                    duration_seconds=duration
                )
        
        # Stop input listeners
        if PYNPUT_SUPPORT:
            if self.mouse_listener:
                self.mouse_listener.stop()
            if self.keyboard_listener:
                self.keyboard_listener.stop()
        
        # Log system shutdown
        self.db.log_system_event("session_end")
