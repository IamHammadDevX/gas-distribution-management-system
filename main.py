#!/usr/bin/env python3
"""
Rajput Gas Control System - Main Entry Point
Organized folder structure with proper imports
"""

import sys
import os

# Add src directories to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'components'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'database_module'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'ui'))

from PySide6.QtWidgets import QApplication
from core.main_app import RajputGasManagement

def main():
    """Main entry point"""
    app = RajputGasManagement(sys.argv)
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())