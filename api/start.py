#!/usr/bin/env python3
"""
Startup script for HelloVM AI Funland Backend
"""

import os
import sys
from pathlib import Path

def main():
    """Main entry point"""
    # Add the api directory to Python path
    api_dir = Path(__file__).parent
    sys.path.insert(0, str(api_dir))
    
    # Import and run the main application
    try:
        from src.main import main as app_main
        app_main()
    except ImportError as e:
        print(f"Error importing main application: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()