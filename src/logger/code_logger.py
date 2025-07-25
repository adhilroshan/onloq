"""
Code change logger for monitoring file changes and generating diffs
"""

import os
import time
import difflib
import threading
from pathlib import Path
from typing import List, Dict, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from storage.database import Database
from utils.config import Config

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self, database: Database, config: Config):
        self.db = database
        self.config = config
        self.file_extensions = set(config.get_file_extensions())
        self.ignored_dirs = set(config.get_ignored_directories())
        
        # Store file contents for diff generation
        self.file_cache = {}
        
        # Debounce rapid file changes
        self.change_queue = {}
        self.debounce_delay = 1.0  # 1 second
    
    def _should_track_file(self, file_path: str) -> bool:
        """Check if a file should be tracked based on extension and location."""
        path = Path(file_path)
        
        # Check file extension
        if path.suffix.lower() not in self.file_extensions:
            return False
        
        # Check if in ignored directory
        for part in path.parts:
            if part in self.ignored_dirs:
                return False
        
        return True
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """Safely read file content."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            try:
                # Try with different encoding
                with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                    return f.read()
            except Exception:
                return None
    
    def _generate_diff(self, old_content: str, new_content: str, file_path: str) -> str:
        """Generate unified diff between old and new content."""
        if old_content is None:
            old_content = ""
        if new_content is None:
            new_content = ""
        
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{Path(file_path).name}",
            tofile=f"b/{Path(file_path).name}",
            lineterm=""
        )
        
        return "".join(diff)
    
    def _process_file_change(self, file_path: str, change_type: str):
        """Process a file change event."""
        if not self._should_track_file(file_path):
            return
        
        try:
            file_size = None
            diff_content = None
            
            if change_type == "deleted":
                # File was deleted
                old_content = self.file_cache.get(file_path, "")
                diff_content = self._generate_diff(old_content, "", file_path)
                
                # Remove from cache
                if file_path in self.file_cache:
                    del self.file_cache[file_path]
            
            elif change_type in ["created", "modified"]:
                # File was created or modified
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    new_content = self._read_file_content(file_path)
                    
                    if new_content is not None:
                        old_content = self.file_cache.get(file_path, "")
                        
                        # Only generate diff if content actually changed
                        if old_content != new_content:
                            diff_content = self._generate_diff(old_content, new_content, file_path)
                            
                            # Update cache
                            self.file_cache[file_path] = new_content
                        else:
                            # Content didn't change, skip logging
                            return
            
            # Log the change
            if diff_content:
                relative_path = os.path.relpath(file_path)
                self.db.log_code_change(
                    file_path=relative_path,
                    change_type=change_type,
                    file_size=file_size,
                    diff_content=diff_content,
                    metadata={
                        "absolute_path": file_path,
                        "file_extension": Path(file_path).suffix
                    }
                )
                
                print(f"📝 Logged {change_type}: {relative_path}")
        
        except Exception as e:
            print(f"Error processing file change {file_path}: {e}")
    
    def _debounced_change(self, file_path: str, change_type: str):
        """Handle debounced file changes to avoid rapid-fire events."""
        def process_after_delay():
            time.sleep(self.debounce_delay)
            # Check if this is still the latest change for this file
            if (file_path in self.change_queue and 
                self.change_queue[file_path] == change_type):
                
                self._process_file_change(file_path, change_type)
                
                # Remove from queue
                if file_path in self.change_queue:
                    del self.change_queue[file_path]
        
        # Update queue with latest change type
        self.change_queue[file_path] = change_type
        
        # Start debounced processing in background
        thread = threading.Thread(target=process_after_delay, daemon=True)
        thread.start()
    
    def on_created(self, event):
        if not event.is_directory:
            self._debounced_change(event.src_path, "created")
    
    def on_modified(self, event):
        if not event.is_directory:
            self._debounced_change(event.src_path, "modified")
    
    def on_deleted(self, event):
        if not event.is_directory:
            self._debounced_change(event.src_path, "deleted")
    
    def on_moved(self, event):
        if not event.is_directory:
            # Treat move as delete + create
            self._debounced_change(event.src_path, "deleted")
            self._debounced_change(event.dest_path, "created")

class CodeLogger:
    def __init__(self, database: Database, watch_directories: List[str] = None):
        self.db = database
        self.config = Config()
        self.watch_dirs = watch_directories or self.config.get_watch_directories()
        
        self.observer = Observer()
        self.event_handler = CodeChangeHandler(database, self.config)
        self.running = False
    
    def _initialize_file_cache(self):
        """Initialize file cache with existing files."""
        print("🔍 Initializing file cache...")
        
        for watch_dir in self.watch_dirs:
            watch_path = Path(watch_dir).resolve()
            
            if not watch_path.exists():
                print(f"⚠️  Watch directory does not exist: {watch_path}")
                continue
            
            # Walk through directory and cache existing files
            for root, dirs, files in os.walk(watch_path):
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if d not in self.config.get_ignored_directories()]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    if self.event_handler._should_track_file(file_path):
                        content = self.event_handler._read_file_content(file_path)
                        if content is not None:
                            self.event_handler.file_cache[file_path] = content
        
        cached_files = len(self.event_handler.file_cache)
        print(f"📁 Cached {cached_files} files for change tracking")
    
    def start(self):
        """Start code change monitoring."""
        if self.running:
            return
        
        self.running = True
        
        # Initialize file cache
        self._initialize_file_cache()
        
        # Setup watchers for each directory
        for watch_dir in self.watch_dirs:
            watch_path = Path(watch_dir).resolve()
            
            if watch_path.exists():
                self.observer.schedule(
                    self.event_handler,
                    str(watch_path),
                    recursive=True
                )
                print(f"👀 Watching: {watch_path}")
            else:
                print(f"⚠️  Directory not found: {watch_path}")
        
        # Start observer
        self.observer.start()
        print("🚀 Code change monitoring started")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop code change monitoring."""
        if not self.running:
            return
        
        self.running = False
        
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        
        print("🛑 Code change monitoring stopped")
