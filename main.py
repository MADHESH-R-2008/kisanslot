import sys
import os

# Add the backend directory to the sys path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

# Import the FastAPI app from backend/main.py
from backend.main import app
