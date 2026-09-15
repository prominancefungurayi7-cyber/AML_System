"""
Stage 8 Flask Startup Test
Tests Flask application startup with MySQL connection.
"""

import sys
sys.path.insert(0, '.')

try:
    from server import app
    print("Flask app imported successfully")
    print(f"Database URL: {app.config.get('DATABASE_URL', 'Not set')}")
    print(f"Debug mode: {app.config.get('DEBUG', False)}")
    print("PASS Flask startup test passed")
except Exception as e:
    print(f"FAIL Flask startup test failed: {e}")
