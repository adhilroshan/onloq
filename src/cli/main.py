"""
Main CLI interface for Onloq
"""

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import asyncio
import threading
import time
import signal
import sys

from storage.database import Database
from logger.activity_logger import ActivityLogger
from logger.code_logger import CodeLogger
from summarizer.llm_summarizer import LLMSummarizer
from utils.config import Config
from scheduler.daily_scheduler import DailyScheduler
from scheduler.notifier import Notifier

app = typer.Typer(name="onloq", help="Privacy-first local activity and code change logger")
console = Console()

@app.command()
def init(
    config_path: str = typer.Option("./onloq_config.json", help="Path to config file"),
    watch_dirs: str = typer.Option(".", help="Comma-separated directories to watch for code changes")
):
    """Initialize Onloq configuration and setup tracking folders."""
    console.print(Panel.fit("🔒 Initializing Onloq", style="bold blue"))
    
    config = Config(config_path)
    
    # Setup watch directories
    dirs = [d.strip() for d in watch_dirs.split(",")]
    config.set_watch_directories(dirs)
    
    # Initialize database
    db = Database()
    db.initialize()
    
    console.print(f"✅ Configuration saved to: {config_path}")
    console.print(f"📁 Watching directories: {', '.join(dirs)}")
    console.print("🎯 Run 'python main.py run' to start logging")

@app.command()
def run(
    config_path: str = typer.Option("./onloq_config.json", help="Path to config file"),
    daemon: bool = typer.Option(False, help="Run in daemon mode (background)"),
    auto_summarize: bool = typer.Option(None, help="Enable/disable automatic daily summaries")
):
    """Start the activity and code loggers with optional automatic summarization."""
    console.print(Panel.fit("🚀 Starting Onloq Logger", style="bold green"))
    
    config = Config(config_path)
    
    # Update auto-summarize setting if provided
    if auto_summarize is not None:
        settings = config.get_summarization_settings()
        settings["auto_summarize"] = auto_summarize
        config.config["summarization"] = settings
        config._save_config()
        console.print(f"📅 Auto-summarization: {'enabled' if auto_summarize else 'disabled'}")
    
    # Initialize components
    db = Database()
    activity_logger = ActivityLogger(db)
    code_logger = CodeLogger(db, config.get_watch_directories())
    daily_scheduler = DailyScheduler(config)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        console.print("\n🛑 Shutting down gracefully...")
        activity_logger.stop()
        code_logger.stop()
        daily_scheduler.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start loggers in separate threads
        activity_thread = threading.Thread(target=activity_logger.start, daemon=True)
        code_thread = threading.Thread(target=code_logger.start, daemon=True)
        
        activity_thread.start()
        code_thread.start()
        
        # Start daily scheduler
        daily_scheduler.start()
        
        console.print("📊 Activity logging started")
        console.print("📝 Code change monitoring started")
        
        # Show scheduler status
        if config.get_summarization_settings().get("auto_summarize", False):
            next_run = daily_scheduler.get_next_run_time()
            if next_run:
                console.print(f"📅 Next summary scheduled: {next_run}")
            console.print("🔔 Desktop notifications enabled")
        else:
            console.print("📅 Auto-summarization disabled (use --auto-summarize to enable)")
        
        console.print("Press Ctrl+C to stop")
        
        if daemon:
            # Run indefinitely in daemon mode
            while True:
                time.sleep(60)
        else:
            # Interactive mode
            while True:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    break
                    
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
    finally:
        activity_logger.stop()
        code_logger.stop()

@app.command()
def summarize(
    config_path: str = typer.Option("./onloq_config.json", help="Path to config file"),
    days: int = typer.Option(1, help="Number of days to summarize"),
    model: str = typer.Option("qwen2.5", help="Ollama model to use"),
    output_file: str = typer.Option("", help="Output file for summary (optional)")
):
    """Generate AI summary of logged data."""
    console.print(Panel.fit("🤖 Generating Summary with AI", style="bold magenta"))
    
    db = Database()
    summarizer = LLMSummarizer(model=model)
    
    try:
        summary = summarizer.generate_summary(db, days=days)
        
        # Display summary
        console.print(Panel(summary, title="📋 Daily Summary", style="cyan"))
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            console.print(f"💾 Summary saved to: {output_file}")
        
        # Also save to default daily summary file
        from datetime import datetime
        default_file = f"daily_summary_{datetime.now().strftime('%Y-%m-%d')}.md"
        with open(default_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        console.print(f"📄 Summary also saved to: {default_file}")
        
    except Exception as e:
        console.print(f"❌ Error generating summary: {e}", style="bold red")

@app.command()
def status():
    """Show current status and recent activity."""
    console.print(Panel.fit("📊 Onloq Status", style="bold blue"))
    
    db = Database()
    
    try:
        # Get recent activity stats
        stats = db.get_recent_stats()
        
        console.print(f"📱 Applications tracked today: {stats.get('apps_today', 0)}")
        console.print(f"🌐 Websites visited today: {stats.get('websites_today', 0)}")
        console.print(f"📝 Code files changed today: {stats.get('files_today', 0)}")
        console.print(f"⏱️  Total active time today: {stats.get('active_time', 'Unknown')}")
        
    except Exception as e:
        console.print(f"❌ Error getting status: {e}", style="bold red")

@app.command()
def auto(
    config_path: str = typer.Option("./onloq_config.json", help="Path to config file"),
    enable: bool = typer.Option(True, help="Enable auto-summarization"),
    time: str = typer.Option("23:59", help="Time to generate summary (HH:MM format)"),
    model: str = typer.Option("qwen2.5", help="Default model for summaries")
):
    """Configure automatic daily summarization."""
    console.print(Panel.fit("⚙️ Configuring Auto-Summarization", style="bold cyan"))
    
    config = Config(config_path)
    settings = config.get_summarization_settings()
    
    # Update settings
    settings["auto_summarize"] = enable
    settings["summarize_time"] = time
    settings["default_model"] = model
    
    config.config["summarization"] = settings
    config._save_config()
    
    if enable:
        console.print(f"✅ Auto-summarization enabled")
        console.print(f"⏰ Daily summary at: {time}")
        console.print(f"🤖 Using model: {model}")
        console.print("🔔 Desktop notifications will be sent")
    else:
        console.print("❌ Auto-summarization disabled")
    
    console.print("💡 Restart Onloq for changes to take effect")

@app.command()
def schedule(
    config_path: str = typer.Option("./onloq_config.json", help="Path to config file")
):
    """Show current schedule and automation status."""
    console.print(Panel.fit("📅 Schedule Status", style="bold blue"))
    
    config = Config(config_path)
    settings = config.get_summarization_settings()
    
    auto_enabled = settings.get("auto_summarize", False)
    summary_time = settings.get("summarize_time", "23:59")
    model = settings.get("default_model", "qwen2.5")
    
    if auto_enabled:
        console.print("✅ Auto-summarization: ENABLED")
        console.print(f"⏰ Summary time: {summary_time}")
        console.print(f"🤖 Model: {model}")
        
        # Try to get next run time if scheduler is running
        try:
            scheduler = DailyScheduler(config)
            next_run = scheduler.get_next_run_time()
            if next_run:
                console.print(f"📅 Next run: {next_run}")
        except:
            pass
    else:
        console.print("❌ Auto-summarization: DISABLED")
        console.print("💡 Use 'python main.py auto --enable' to enable")

@app.command()
def notify(
    test: bool = typer.Option(False, help="Send test notification")
):
    """Test notification system or send custom notifications."""
    notifier = Notifier()
    
    if test:
        console.print("🧪 Sending test notification...")
        notifier.test_notification()
        console.print("✅ Test notification sent!")
    else:
        console.print("🔔 Notification system ready")
        console.print("💡 Use --test to send a test notification")

if __name__ == "__main__":
    app()
