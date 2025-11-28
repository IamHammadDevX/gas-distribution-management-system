#!/usr/bin/env python3
import sys

from PySide6.QtWidgets import QApplication
from src.core.main_app import RajputGasManagement

def main():
    app = RajputGasManagement(sys.argv)
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
