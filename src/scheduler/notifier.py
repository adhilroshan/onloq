"""
Cross-platform notification system for Onloq
"""

import os
import platform
import subprocess
from typing import Dict, Any
from pathlib import Path


class Notifier:
    def __init__(self):
        self.system = platform.system().lower()
        self.enabled = True
        
    def _show_windows_notification(self, title: str, message: str, icon: str = "info"):
        """Show notification on Windows using PowerShell."""
        try:
            # Use PowerShell to show toast notification
            ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
$notification = New-Object System.Windows.Forms.NotifyIcon
$notification.Icon = [System.Drawing.SystemIcons]::{icon.title()}
$notification.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::{icon.title()}
$notification.BalloonTipText = "{message}"
$notification.BalloonTipTitle = "{title}"
$notification.Visible = $true
$notification.ShowBalloonTip(5000)
Start-Sleep -Seconds 6
$notification.Dispose()
'''
            subprocess.run([
                "powershell", "-Command", ps_script
            ], capture_output=True, text=True)
            
        except Exception as e:
            print(f"⚠️ Windows notification failed: {e}")
            self._fallback_notification(title, message)
    
    def _show_macos_notification(self, title: str, message: str):
        """Show notification on macOS using osascript."""
        try:
            subprocess.run([
                "osascript", "-e", 
                f'display notification "{message}" with title "{title}"'
            ], capture_output=True)
        except Exception as e:
            print(f"⚠️ macOS notification failed: {e}")
            self._fallback_notification(title, message)
    
    def _show_linux_notification(self, title: str, message: str):
        """Show notification on Linux using notify-send."""
        try:
            subprocess.run([
                "notify-send", title, message
            ], capture_output=True)
        except Exception as e:
            print(f"⚠️ Linux notification failed: {e}")
            self._fallback_notification(title, message)
    
    def _fallback_notification(self, title: str, message: str):
        """Fallback console notification."""
        print(f"\n🔔 {title}")
        print(f"   {message}")
        print()
    
    def send_notification(self, title: str, message: str, icon: str = "info"):
        """Send cross-platform notification."""
        if not self.enabled:
            return
        
        try:
            if self.system == "windows":
                self._show_windows_notification(title, message, icon)
            elif self.system == "darwin":  # macOS
                self._show_macos_notification(title, message)
            elif self.system == "linux":
                self._show_linux_notification(title, message)
            else:
                self._fallback_notification(title, message)
                
        except Exception as e:
            print(f"❌ Notification failed: {e}")
            self._fallback_notification(title, message)
    
    def send_daily_summary_notification(self, summary_file: str, stats: Dict[str, Any]):
        """Send notification when daily summary is ready."""
        active_time = stats.get('active_time', 'Unknown')
        apps_count = stats.get('apps_today', 0)
        files_count = stats.get('files_today', 0)
        
        title = "📊 Daily Summary Ready!"
        message = f"""Your development journal is ready!
        
📁 File: {summary_file}
⏱️ Active time: {active_time}
📱 Apps used: {apps_count}
📝 Files changed: {files_count}

Click to open the summary file."""
        
        self.send_notification(title, message, "info")
        
        # Also try to open the file
        self._try_open_file(summary_file)
    
    def send_startup_notification(self, schedule_time: str):
        """Send notification when Onloq starts with auto-summary enabled."""
        title = "🚀 Onloq Started"
        message = f"Privacy-first activity logging started!\nDaily summary scheduled for {schedule_time}"
        
        self.send_notification(title, message, "info")
    
    def send_error_notification(self, error_message: str):
        """Send error notification."""
        title = "❌ Onloq Error"
        message = f"Something went wrong:\n{error_message}"
        
        self.send_notification(title, message, "error")
    
    def send_activity_reminder(self):
        """Send reminder about low activity."""
        title = "💡 Activity Reminder"
        message = "Low activity detected. Take a break or consider logging more detailed work!"
        
        self.send_notification(title, message, "warning")
    
    def send_week_summary_notification(self):
        """Send notification for weekly summary."""
        title = "📈 Weekly Summary Available"
        message = "Your weekly development summary is ready for review!"
        
        self.send_notification(title, message, "info")
    
    def _try_open_file(self, file_path: str):
        """Try to open file with default application."""
        try:
            if self.system == "windows":
                os.startfile(file_path)
            elif self.system == "darwin":
                subprocess.run(["open", file_path])
            elif self.system == "linux":
                subprocess.run(["xdg-open", file_path])
        except Exception:
            # Silent fail - opening file is nice to have
            pass
    
    def disable(self):
        """Disable notifications."""
        self.enabled = False
        print("🔕 Notifications disabled")
    
    def enable(self):
        """Enable notifications."""
        self.enabled = True
        print("🔔 Notifications enabled")
    
    def test_notification(self):
        """Test notification system."""
        title = "🧪 Onloq Test"
        message = "This is a test notification from Onloq!"
        
        print("Testing notification system...")
        self.send_notification(title, message)
        print("✅ Test notification sent")
