# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-07-25

### Added
- Initial release of Onloq
- Privacy-first local activity and code change logger
- CLI interface with `init`, `run`, `status`, and `summarize` commands
- Activity tracking for applications, websites, and idle detection
- Code change monitoring with diff generation
- AI summarization using Ollama (local LLM)
- SQLite database for local storage
- Configuration management system
- Windows support with cross-platform architecture
- Smart file filtering and ignore patterns
- Comprehensive logging and error handling
- MIT license and full documentation
- GitHub Actions CI/CD pipeline
- Pytest test suite

### Features
#### Activity Tracking
- Track time spent in different applications
- Monitor domains visited in browsers
- Detect and log idle periods
- Log system events (session start/end)

#### Code Monitoring  
- Watch directories for file modifications
- Generate unified diffs for all changes
- Filter by file extensions (.py, .js, .ts, etc.)
- Ignore build folders and version control directories
- Debounced change detection to avoid spam

#### AI Summarization
- Local LLM integration via Ollama
- Daily development journal generation
- Support for multiple models (qwen2.5, gemma2, etc.)
- Markdown formatted output
- Configurable summarization settings

#### Privacy & Security
- 100% local data storage
- No external network calls (except local Ollama)
- Optional SQLite encryption
- Configurable tracking preferences
- Open source transparency

### Technical Details
- Python 3.11+ requirement
- Modular architecture with clear separation of concerns
- Rich CLI with colored output and progress indicators
- Cross-platform file watching with fallback options
- Comprehensive error handling and logging
- Type hints and documentation throughout

### Dependencies
- typer[all] - CLI framework
- psutil - System and process utilities
- watchdog - File system event monitoring
- cryptography - Optional encryption support
- rich - Terminal formatting and colors
- python-dateutil - Date/time utilities
- pynput - Input monitoring for idle detection
- pywin32 - Windows-specific functionality

[0.1.0]: https://github.com/adhilroshan/onloq/releases/tag/v0.1.0
