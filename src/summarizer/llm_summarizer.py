"""
LLM summarizer using Ollama for generating daily activity summaries
"""

import subprocess
import json
import tempfile
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from storage.database import Database

class LLMSummarizer:
    def __init__(self, model: str = "qwen2.5"):
        self.model = model
        
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available and the model is installed."""
        try:
            # Check if ollama command exists
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return False
            
            # Check if our model is available
            available_models = result.stdout.lower()
            return self.model.lower() in available_models
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _format_activity_data(self, activity_logs: List[Dict]) -> str:
        """Format activity logs for LLM prompt."""
        if not activity_logs:
            return "No activity data recorded."
        
        # Group by application and aggregate durations
        app_durations = {}
        website_visits = set()
        system_events = []
        idle_time = 0
        
        for log in activity_logs:
            event_type = log.get('event_type', '')
            
            if event_type == 'app_focus':
                app = log.get('application', 'Unknown')
                duration = log.get('duration_seconds', 0)
                
                if app in app_durations:
                    app_durations[app] += duration
                else:
                    app_durations[app] = duration
            
            elif event_type == 'website_visit':
                domain = log.get('website_domain')
                if domain:
                    website_visits.add(domain)
            
            elif event_type == 'idle':
                idle_time += log.get('duration_seconds', 0)
            
            elif event_type in ['session_start', 'session_end']:
                system_events.append(f"{event_type} at {log.get('timestamp', 'unknown')}")
        
        # Format the data
        result = "## Application Usage:\n"
        
        # Sort apps by duration (most used first)
        sorted_apps = sorted(app_durations.items(), key=lambda x: x[1], reverse=True)
        
        for app, duration_seconds in sorted_apps:
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            
            if hours > 0:
                time_str = f"{hours}h {minutes}m"
            else:
                time_str = f"{minutes}m"
            
            result += f"- {app}: {time_str}\n"
        
        if website_visits:
            result += "\n## Websites Visited:\n"
            for domain in sorted(website_visits):
                result += f"- {domain}\n"
        
        if idle_time > 0:
            idle_hours = idle_time // 3600
            idle_minutes = (idle_time % 3600) // 60
            result += f"\n## Idle Time: {idle_hours}h {idle_minutes}m\n"
        
        if system_events:
            result += "\n## System Events:\n"
            for event in system_events:
                result += f"- {event}\n"
        
        return result
    
    def _format_code_data(self, code_logs: List[Dict]) -> str:
        """Format code change logs for LLM prompt."""
        if not code_logs:
            return "No code changes recorded."
        
        # Group by file and change type
        file_changes = {}
        total_changes = len(code_logs)
        
        for log in code_logs:
            file_path = log.get('file_path', 'Unknown')
            change_type = log.get('change_type', 'modified')
            diff_content = log.get('diff_content', '')
            
            if file_path not in file_changes:
                file_changes[file_path] = {
                    'changes': [],
                    'total_lines_changed': 0
                }
            
            # Count lines changed (rough estimate from diff)
            lines_changed = 0
            if diff_content:
                for line in diff_content.split('\n'):
                    if line.startswith('+') or line.startswith('-'):
                        if not line.startswith('+++') and not line.startswith('---'):
                            lines_changed += 1
            
            file_changes[file_path]['changes'].append({
                'type': change_type,
                'timestamp': log.get('timestamp', ''),
                'lines_changed': lines_changed,
                'diff_preview': diff_content[:200] + "..." if len(diff_content) > 200 else diff_content
            })
            
            file_changes[file_path]['total_lines_changed'] += lines_changed
        
        # Format the data
        result = f"## Code Changes ({total_changes} total changes):\n"
        
        # Sort files by number of lines changed
        sorted_files = sorted(
            file_changes.items(), 
            key=lambda x: x[1]['total_lines_changed'], 
            reverse=True
        )
        
        for file_path, changes_data in sorted_files:
            total_lines = changes_data['total_lines_changed']
            num_changes = len(changes_data['changes'])
            
            result += f"\n### {file_path} ({num_changes} changes, ~{total_lines} lines)\n"
            
            # Show recent changes (limit to avoid overwhelming the LLM)
            recent_changes = changes_data['changes'][-3:]  # Last 3 changes
            
            for change in recent_changes:
                result += f"- {change['type']} at {change['timestamp']}\n"
                if change['diff_preview'].strip():
                    # Show a small preview of the diff
                    preview_lines = change['diff_preview'].split('\n')[:3]
                    for line in preview_lines:
                        if line.strip():
                            result += f"  {line}\n"
        
        return result
    
    def _create_prompt(self, activity_data: str, code_data: str, days: int = 1) -> str:
        """Create the prompt for the LLM."""
        date_range = "today" if days == 1 else f"the past {days} days"
        
        prompt = f"""You are a helpful assistant. Here is a developer's system usage and code change log for {date_range}.

Summarize it concisely as a developer journal. Focus on major applications used, important coding activities, and anything notable.

{activity_data}

{code_data}

Please provide a clean Markdown summary with bullet points for major insights. Be concise but informative.
Focus on:
- Key applications and time spent
- Major coding projects or files worked on
- Development patterns or productivity insights
- Any notable activities or events

Keep the summary under 500 words and format it as a daily development journal entry."""
        
        return prompt
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama with the prompt and return the response."""
        try:
            # Create a temporary file for the prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(prompt)
                prompt_file = f.name
            
            # Call ollama
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutes timeout
                encoding='utf-8'
            )
            
            # Clean up temp file
            Path(prompt_file).unlink(missing_ok=True)
            
            if result.returncode != 0:
                raise Exception(f"Ollama error: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise Exception("Ollama request timed out")
        except Exception as e:
            raise Exception(f"Error calling Ollama: {e}")
    
    def generate_summary(self, database: Database, days: int = 1) -> str:
        """Generate a summary of the specified number of days."""
        
        # Check if Ollama is available
        if not self._check_ollama_availability():
            raise Exception(f"Ollama is not available or model '{self.model}' is not installed. "
                          f"Please install Ollama and run: ollama pull {self.model}")
        
        # Get data from database
        activity_logs = database.get_activity_logs(days=days)
        code_logs = database.get_code_logs(days=days)
        
        # Format data for LLM
        activity_data = self._format_activity_data(activity_logs)
        code_data = self._format_code_data(code_logs)
        
        # Create prompt
        prompt = self._create_prompt(activity_data, code_data, days)
        
        # Generate summary
        summary = self._call_ollama(prompt)
        
        # Add metadata header
        date_str = datetime.now().strftime("%Y-%m-%d")
        header = f"# Developer Journal - {date_str}\n\n"
        
        if days > 1:
            header = f"# Developer Journal - {days} Day Summary - {date_str}\n\n"
        
        # Add data summary at the end
        footer = f"\n\n---\n*Generated from {len(activity_logs)} activity events and {len(code_logs)} code changes using {self.model}*\n"
        
        return header + summary + footer
