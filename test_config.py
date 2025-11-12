#!/usr/bin/env python
"""Test script to debug app_config"""
import sys
import os

print("Current directory:", os.getcwd())
print("Python path:", sys.path[:3])

# Try importing
try:
    print("\n=== Attempting import ===")
    import app_config
    print("Import successful")
    print("Module attributes:", [x for x in dir(app_config) if not x.startswith('__')])
    print("Has FLASK_HOST:", hasattr(app_config, 'FLASK_HOST'))
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()

# Try executing directly
try:
    print("\n=== Attempting direct execution ===")
    with open('app_config.py', 'r') as f:
        code = f.read()
    exec(code)
    print("Execution successful")
    print("FLASK_HOST in locals:", 'FLASK_HOST' in locals())
    if 'FLASK_HOST' in locals():
        print("FLASK_HOST value:", FLASK_HOST)
except Exception as e:
    print(f"Execution failed: {e}")
    import traceback
    traceback.print_exc()

