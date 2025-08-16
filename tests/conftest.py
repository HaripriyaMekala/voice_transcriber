# tests/conftest.py
import os, sys
# add the project root (parent of /tests) to Python's import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
