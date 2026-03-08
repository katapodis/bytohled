# tests/conftest.py
import sys
import os

# Ensure project root is in Python path for all tests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
