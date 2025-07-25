#!/usr/bin/env python3
"""
Lightweight startup script for the enhanced web scraping API
Skips heavy ML dependencies for faster startup
"""

import os
import sys
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(src_dir))

# Set environment variable to disable heavy dependencies
os.environ["LIGHTWEIGHT_MODE"] = "1"

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Enhanced Web Scraping API in Lightweight Mode")
    print("=" * 60)
    print("✅ Skipping heavy ML dependencies for faster startup")
    print("✅ Enhanced research endpoints available")
    print("✅ Gemini AI integration enabled")
    print()
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )