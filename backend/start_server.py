#!/usr/bin/env python3
"""
Startup script for the Web Search Agent backend server
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the backend directory
    backend_dir = Path(__file__).parent.absolute()
    project_root = backend_dir.parent
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Set PYTHONPATH to include the backend directory
    env = os.environ.copy()
    env['PYTHONPATH'] = str(backend_dir)
    
    # Print startup info
    print("🚀 Starting Web Search Agent Backend Server...")
    print(f"📁 Backend directory: {backend_dir}")
    print(f"🐍 Python path: {env.get('PYTHONPATH', 'Not set')}")
    print(f"🌐 Server will be available at: http://localhost:8000")
    print("=" * 50)
    
    # Start the server
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "src.api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], env=env, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 