"""
Basic tests for Onloq components
"""

import pytest
import tempfile
import os
from pathlib import Path

# Add src to path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storage.database import Database
from utils.config import Config


def test_config_creation():
    """Test configuration creation and loading."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_path = f.name
    
    try:
        config = Config(config_path)
        
        # Test default values
        assert config.get_watch_directories() == ["."]
        assert ".py" in config.get_file_extensions()
        assert "__pycache__" in config.get_ignored_directories()
        
        # Test setting watch directories
        config.set_watch_directories(["/test/path"])
        assert config.get_watch_directories() == ["/test/path"]
        
    finally:
        if os.path.exists(config_path):
            os.unlink(config_path)


def test_database_initialization():
    """Test database creation and basic operations."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        db = Database(db_path)
        db.initialize()
        
        # Test logging activity
        db.log_activity(
            event_type="app_focus",
            application="test_app",
            window_title="Test Window",
            duration_seconds=60
        )
        
        # Test logging code change
        db.log_code_change(
            file_path="test.py",
            change_type="modified",
            file_size=100,
            diff_content="test diff"
        )
        
        # Test getting logs
        activity_logs = db.get_activity_logs(days=1)
        code_logs = db.get_code_logs(days=1)
        
        assert len(activity_logs) == 1
        assert len(code_logs) == 1
        assert activity_logs[0]['application'] == 'test_app'
        assert code_logs[0]['file_path'] == 'test.py'
        
        # Test stats
        stats = db.get_recent_stats()
        assert isinstance(stats, dict)
        assert 'apps_today' in stats
        
        db.close()
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_cli_import():
    """Test that CLI module can be imported."""
    from cli.main import app
    assert app is not None


def test_logger_imports():
    """Test that logger modules can be imported."""
    from logger.activity_logger import ActivityLogger
    from logger.code_logger import CodeLogger
    
    assert ActivityLogger is not None
    assert CodeLogger is not None


def test_summarizer_import():
    """Test that summarizer module can be imported."""
    from summarizer.llm_summarizer import LLMSummarizer
    
    assert LLMSummarizer is not None
    
    # Test summarizer initialization
    summarizer = LLMSummarizer("test_model")
    assert summarizer.model == "test_model"


if __name__ == "__main__":
    pytest.main([__file__])
