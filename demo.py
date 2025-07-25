#!/usr/bin/env python3
"""
Onloq Demo Script
A quick way to test Onloq functionality
"""

import os
import sys
import time
import tempfile
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storage.database import Database
from utils.config import Config
from summarizer.llm_summarizer import LLMSummarizer


def check_ollama():
    """Check if Ollama is available."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False


def demo_database():
    """Demo database functionality."""
    print("🗄️  Testing database functionality...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        db = Database(db_path)
        db.initialize()
        
        # Add some sample data
        db.log_activity(
            event_type="app_focus",
            application="vscode.exe",
            window_title="Onloq - main.py",
            duration_seconds=3600
        )
        
        db.log_activity(
            event_type="website_visit",
            application="chrome.exe",
            website_domain="github.com"
        )
        
        db.log_code_change(
            file_path="demo.py",
            change_type="created",
            file_size=1024,
            diff_content="@@ -0,0 +1,3 @@\n+def hello():\n+    print('Hello Onloq!')\n+    return True"
        )
        
        # Get stats
        stats = db.get_recent_stats()
        print(f"   ✅ Database created successfully")
        print(f"   📊 Sample stats: {stats}")
        
        db.close()
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def demo_config():
    """Demo configuration functionality."""
    print("⚙️  Testing configuration...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_path = f.name
    
    try:
        config = Config(config_path)
        print(f"   ✅ Config created at: {config_path}")
        print(f"   📁 Watch dirs: {config.get_watch_directories()}")
        print(f"   📄 File extensions: {len(config.get_file_extensions())} types")
        
    finally:
        if os.path.exists(config_path):
            os.unlink(config_path)


def demo_summarizer():
    """Demo LLM summarizer (requires Ollama)."""
    print("🤖 Testing AI summarizer...")
    
    if not check_ollama():
        print("   ⚠️  Ollama not available - skipping AI demo")
        print("   💡 Install Ollama from https://ollama.ai to test AI features")
        return
    
    try:
        summarizer = LLMSummarizer("qwen2.5")
        print("   ✅ Summarizer initialized")
        print("   🧠 Model: qwen2.5")
        print("   💡 Ready for AI summarization!")
        
    except Exception as e:
        print(f"   ⚠️  Summarizer test failed: {e}")


def main():
    """Run the demo."""
    print("🚀 Onloq Demo - Testing Core Functionality")
    print("=" * 50)
    
    try:
        demo_config()
        print()
        
        demo_database()
        print()
        
        demo_summarizer()
        print()
        
        print("✨ Demo completed successfully!")
        print("🎯 Ready to run: python main.py init")
        print("📖 Full docs: https://github.com/adhilroshan/onloq")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
