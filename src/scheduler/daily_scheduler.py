"""
Daily scheduler for automatic summarization and notifications
"""

import schedule
import time
import threading
import datetime
from pathlib import Path
from typing import Optional

from storage.database import Database
from summarizer.llm_summarizer import LLMSummarizer
from utils.config import Config
from .notifier import Notifier


class DailyScheduler:
    def __init__(self, config: Config):
        self.config = config
        self.settings = config.get_summarization_settings()
        self.running = False
        self.scheduler_thread = None
        self.notifier = Notifier()
        
        # Get schedule time from config
        self.summary_time = self.settings.get("summarize_time", "23:59")
        self.auto_summarize = self.settings.get("auto_summarize", False)
        self.model = self.settings.get("default_model", "qwen2.5")
        
    def setup_schedule(self):
        """Setup the daily schedule."""
        if not self.auto_summarize:
            print("📅 Auto-summarization disabled in config")
            return
            
        # Clear any existing schedules
        schedule.clear()
        
        # Schedule daily summary
        schedule.every().day.at(self.summary_time).do(self._generate_daily_summary)
        
        # Schedule periodic notifications (optional)
        if self.settings.get("periodic_reminders", False):
            schedule.every().hour.do(self._check_activity_reminder)
        
        print(f"📅 Scheduled daily summary at {self.summary_time}")
        print(f"🤖 Using model: {self.model}")
        
    def _generate_daily_summary(self):
        """Generate and save daily summary."""
        try:
            print("🤖 Generating daily summary...")
            
            # Initialize components
            db = Database()
            summarizer = LLMSummarizer(model=self.model)
            
            # Generate summary
            summary = summarizer.generate_summary(db, days=1)
            
            # Save to file
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            summary_file = f"daily_summary_{date_str}.md"
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            # Get stats for notification
            stats = db.get_recent_stats()
            
            # Send notification
            self.notifier.send_daily_summary_notification(
                summary_file=summary_file,
                stats=stats
            )
            
            print(f"✅ Daily summary saved: {summary_file}")
            
        except Exception as e:
            print(f"❌ Failed to generate daily summary: {e}")
            self.notifier.send_error_notification(f"Daily summary failed: {e}")
    
    def _check_activity_reminder(self):
        """Check if user needs activity reminders."""
        try:
            db = Database()
            
            # Get activity from last hour
            from datetime import datetime, timedelta
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            cursor = db.conn.execute("""
                SELECT COUNT(*) FROM activity_logs 
                WHERE timestamp >= ? AND event_type != 'idle'
            """, (one_hour_ago,))
            
            activity_count = cursor.fetchone()[0]
            
            # If very low activity, send reminder
            if activity_count < 3:
                self.notifier.send_activity_reminder()
                
        except Exception as e:
            print(f"⚠️ Activity check failed: {e}")
    
    def _run_scheduler(self):
        """Main scheduler loop."""
        print("🕐 Daily scheduler started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                time.sleep(60)
        
        print("🛑 Daily scheduler stopped")
    
    def start(self):
        """Start the daily scheduler."""
        if self.running:
            return
        
        self.setup_schedule()
        
        if not self.auto_summarize:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        # Send startup notification
        self.notifier.send_startup_notification(self.summary_time)
    
    def stop(self):
        """Stop the daily scheduler."""
        if not self.running:
            return
        
        self.running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        print("📅 Daily scheduler stopped")
    
    def force_summary(self):
        """Force generate summary now."""
        print("🚀 Forcing daily summary generation...")
        self._generate_daily_summary()
    
    def get_next_run_time(self) -> Optional[str]:
        """Get the next scheduled run time."""
        if not schedule.jobs:
            return None
        
        next_run = schedule.next_run()
        if next_run:
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        return None
    
    def update_schedule_time(self, new_time: str):
        """Update the scheduled summary time."""
        self.summary_time = new_time
        
        # Update config
        summarization_settings = self.config.get_summarization_settings()
        summarization_settings["summarize_time"] = new_time
        self.config.config["summarization"] = summarization_settings
        self.config._save_config()
        
        # Restart scheduler with new time
        if self.running:
            self.stop()
            time.sleep(1)
            self.start()
        
        print(f"📅 Updated summary time to: {new_time}")
