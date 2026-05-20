import os
import subprocess
import sys

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "src", "backend")

    print("="*50)
    print("Running Backend Unit Tests...")
    print("="*50)
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("Error: pytest is not installed in the current environment.")
        print("Please install requirements first: pip install -r src/backend/requirements.txt")
        sys.exit(1)
    
    # Run pytest in the backend directory
    # Using python -m pytest ensures it uses the current python environment
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-c", "pytest.ini"],
        cwd=backend_dir
    )
    
    print("\n" + "="*50)
    if result.returncode == 0:
        print("[SUCCESS] All tests passed successfully!")
    else:
        print("[FAILURE] Some tests failed. Check the output above.")
    print("="*50)
        
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
