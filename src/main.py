"""
Main entry point for the prediction app.
"""
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from futurecast.app import run_app


if __name__ == "__main__":
    run_app()
