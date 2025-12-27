#!/usr/bin/env python3
"""
Simple runner script for COS scraper
Reads URLs from config.json and runs the scraper automatically
"""

import sys
import os

# Add current directory to path so we can import cos_scraper
sys.path.insert(0, os.path.dirname(__file__))

# Import and run the main function with --config flag
if __name__ == "__main__":
    # Simulate command line arguments
    sys.argv = ["cos_scraper.py", "--config"]

    # Import and run
    from cos_scraper import main
    main()
