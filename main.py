#!/usr/bin/env python3
"""
Planted - Application Entry Point

Main launcher script for the Planted web application.
Provides error handling and user-friendly troubleshooting messages.
"""

import sys
import os

# Add the project root to the Python path for module imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def main():
    """
    Main application entry point.

    Launches the Planted Flask web application with comprehensive
    error handling and user-friendly troubleshooting guidance.

    Handles:
        - Keyboard interrupts (Ctrl+C) gracefully
        - Import errors with installation guidance
        - Other startup errors with debugging information
    """
    try:
        # Import and run the Flask app
        from app import run_app

        run_app()
    except KeyboardInterrupt:
        print("\n👋 Thanks for using Planted!")
    except Exception as e:
        print(f"❌ Error starting Planted: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure you have Flask installed: pip install flask requests")
        print("2. Try running: python3 app.py")
        print("3. Check that all files are in the correct location")
        sys.exit(1)


if __name__ == "__main__":
    main()
