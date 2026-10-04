#!/usr/bin/env python3
"""
Amazon Wishlist Analytics & Cart Execution Platform Launcher
Usage:
    python run.py                   # Launch Web Dashboard at http://127.0.0.1:8000
    python run.py sync --sample     # Load rich demo dataset
    python run.py list              # Display all tracked wishlist items
    python run.py optimize --budget 250   # Run budget optimizer
    python run.py cart --target-met       # Execute 1-click cart for target-met deals
"""
import sys
from src.cli import main

if __name__ == "__main__":
    main()
