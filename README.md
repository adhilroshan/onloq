# Onloq - Privacy-First Local Activity Logger

> **On-device activity and code change logger with AI summarization**

Onloq is a privacy-first local logger that tracks your development activities and code changes, then uses Ollama (running locally) to generate insightful daily summaries. Everything runs on your machine - no data leaves your device.

## 🚀 Features

### Activity Tracking
- **Application Usage**: Track time spent in different applications
- **Website Monitoring**: Monitor domains visited in browsers
- **Idle Detection**: Track when you're away from the computer
- **System Events**: Log session starts/ends and system activity

### Code Monitoring
- **File Changes**: Watch folders for code file modifications
- **Diff Generation**: Generate unified diffs for all changes
- **Smart Filtering**: Only track relevant source files (.py, .js, .ts, etc.)
- **Ignore Patterns**: Skip build folders, caches, and version control

### AI Summarization
- **Local LLM**: Uses Ollama for completely private AI summaries
- **Daily Journals**: Generate insightful development journal entries
- **Multiple Models**: Support for qwen2.5, gemma2, deepseek-r1, etc.
- **Markdown Output**: Clean, formatted daily summaries

## 📋 Prerequisites

1. **Python 3.11+**
2. **Ollama** - [Install from ollama.ai](https://ollama.ai)
3. **Ollama Model** - Run: `ollama pull qwen2.5` (or your preferred model)

## 🛠 Installation

### Option 1: Install from PyPI (Recommended)
```bash
pip install onloq
```

### Option 2: Install from Source
```bash
git clone https://github.com/adhilroshan/onloq.git
cd onloq
pip install -e .
```

### Option 3: Development Setup
```bash
git clone https://github.com/adhilroshan/onloq.git
cd onloq
pip install -r requirements-dev.txt
```

2. **Install Ollama** (if not already installed):
```bash
# Visit https://ollama.ai and follow installation instructions
# Then pull a model:
ollama pull qwen2.5
```

## 📖 Usage

### Initialize Configuration
```bash
python main.py init --watch-dirs ".,C:\\MyProjects,D:\\Code"
```

### Start Logging
```bash
# Interactive mode
python main.py run

# Daemon mode (background)
python main.py run --daemon
```

### Generate AI Summary
```bash
# Summarize today's activity
python main.py summarize

# Summarize last 3 days
python main.py summarize --days 3

# Use different model
python main.py summarize --model gemma2

# Save to specific file
python main.py summarize --output-file "my_summary.md"
```

### Check Status
```bash
python main.py status
```

## ⚙️ Configuration

Configuration is stored in `onloq_config.json`:

```json
{
  "watch_directories": ["."],
  "file_extensions": [".py", ".js", ".ts", ".cpp", ".java", ".html", ".json"],
  "ignored_directories": ["__pycache__", ".git", "node_modules", ".vscode"],
  "activity_tracking": {
    "idle_threshold_minutes": 5,
    "poll_interval_seconds": 5,
    "track_websites": true,
    "track_applications": true
  },
  "database": {
    "path": "./onloq.db",
    "encryption_enabled": false
  },
  "summarization": {
    "default_model": "qwen2.5",
    "auto_summarize": false,
    "summarize_time": "23:59"
  }
}
```

## 🏗 Architecture

```
onloq/
├── src/
│   ├── cli/           # Typer-based CLI interface
│   ├── logger/        # Activity and code change loggers
│   ├── storage/       # SQLite database management
│   ├── summarizer/    # Ollama LLM integration
│   └── utils/         # Configuration and utilities
├── main.py            # Entry point
└── requirements.txt   # Dependencies
```

## 🔐 Privacy Features

- **100% Local**: All data stays on your machine
- **No Network**: Except for Ollama (which also runs locally)
- **Encrypted Storage**: Optional SQLite encryption
- **Configurable**: Control exactly what gets tracked
- **Open Source**: Full transparency in code

## 📊 Sample Output

```markdown
# Developer Journal - 2025-01-25

## 🚀 Productivity Summary
- **Total Active Time**: 6h 23m
- **Primary Focus**: Python development on Onloq project
- **Key Applications**: VS Code (4h 12m), Chrome (1h 45m), Terminal (35m)

## 💻 Development Activity
- **Files Modified**: 8 Python files, 2 Markdown files
- **Major Changes**: 
  - `src/logger/activity_logger.py`: Enhanced Windows support
  - `src/summarizer/llm_summarizer.py`: Added error handling
  - `README.md`: Updated documentation

## 🌐 Research & References
- Visited: stackoverflow.com, python.org, github.com
- Time spent on documentation and troubleshooting

## 📈 Insights
- High focus session in the morning (3h uninterrupted)
- Productive coding patterns with good break distribution
- Balanced between development and documentation

---
*Generated from 89 activity events and 23 code changes using qwen2.5*
```

## 🔧 Troubleshooting

### Ollama Issues
```bash
# Check if Ollama is running
ollama list

# Pull model if missing
ollama pull qwen2.5

# Test model
ollama run qwen2.5 "Hello"
```

### Windows Permissions
- Run as Administrator if file watching fails
- Check antivirus exclusions for the project folder

### Database Issues
```bash
# Reset database
rm onloq.db
python main.py init
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📜 License

MIT License - see LICENSE file for details.

## 🛣 Roadmap

- [ ] Cross-platform support (macOS, Linux)
- [ ] Automatic daily summarization
- [ ] Web dashboard for viewing logs
- [ ] Export to different formats
- [ ] Integration with Git for commit analysis
- [ ] Productivity analytics and insights
- [ ] Plugin system for custom trackers

---

**Onloq** - Your private development journal, powered by local AI.
