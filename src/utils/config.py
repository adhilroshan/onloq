"""
Configuration management for Onloq
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any

class Config:
    def __init__(self, config_path: str = "./onloq_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_or_create_default()
    
    def _load_or_create_default(self) -> Dict[str, Any]:
        """Load existing config or create default configuration."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Default configuration
        default_config = {
            "watch_directories": ["."],
            "file_extensions": [
                ".py", ".js", ".ts", ".jsx", ".tsx", ".cpp", ".c", ".h", ".hpp",
                ".java", ".kt", ".swift", ".go", ".rs", ".php", ".rb", ".cs",
                ".html", ".css", ".scss", ".less", ".json", ".xml", ".yaml", ".yml",
                ".sql", ".md", ".txt", ".sh", ".bat", ".ps1", ".dockerfile"
            ],
            "ignored_directories": [
                "__pycache__", ".git", ".svn", ".hg", "node_modules", ".vscode",
                ".idea", "build", "dist", "target", "bin", "obj", ".pytest_cache",
                ".mypy_cache", "venv", "env", ".env"
            ],
            "activity_tracking": {
                "idle_threshold_minutes": 5,
                "poll_interval_seconds": 5,
                "track_websites": True,
                "track_applications": True
            },
            "database": {
                "path": "./onloq.db",
                "encryption_enabled": False
            },
            "summarization": {
                "default_model": "qwen2.5",
                "auto_summarize": True,
                "summarize_time": "23:59",
                "periodic_reminders": False
            }
        }
        
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any] = None):
        """Save configuration to file."""
        config_to_save = config or self.config
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_to_save, f, indent=2, ensure_ascii=False)
    
    def get_watch_directories(self) -> List[str]:
        """Get directories to watch for code changes."""
        return self.config.get("watch_directories", ["."])
    
    def set_watch_directories(self, directories: List[str]):
        """Set directories to watch for code changes."""
        self.config["watch_directories"] = directories
        self._save_config()
    
    def get_file_extensions(self) -> List[str]:
        """Get file extensions to track."""
        return self.config.get("file_extensions", [])
    
    def get_ignored_directories(self) -> List[str]:
        """Get directories to ignore during file watching."""
        return self.config.get("ignored_directories", [])
    
    def get_database_path(self) -> str:
        """Get database file path."""
        return self.config.get("database", {}).get("path", "./onloq.db")
    
    def get_activity_settings(self) -> Dict[str, Any]:
        """Get activity tracking settings."""
        return self.config.get("activity_tracking", {})
    
    def get_summarization_settings(self) -> Dict[str, Any]:
        """Get summarization settings."""
        return self.config.get("summarization", {})
