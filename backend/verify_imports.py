import sys
import os

# Add current directory to path so we can resolve 'app'
sys.path.append(os.getcwd())

try:
    print("Attempting to import app.main...")
    from app.main import app
    print("Successfully imported app.main!")
except Exception as e:
    print(f"FAILED to import app.main: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
