#!/usr/bin/env python3
"""
Onloq - Privacy-first local activity and code change logger
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cli.main import app

if __name__ == "__main__":
    app()
