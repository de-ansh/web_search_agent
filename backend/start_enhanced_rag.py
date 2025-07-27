#!/usr/bin/env python3
"""
Enhanced RAG Agent Server Startup Script
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Now import and run the RAG server
if __name__ == "__main__":
    from src.api.rag_main import app
    import uvicorn
    
    print("🤖 Starting Enhanced RAG AI Agent")
    print("=" * 50)
    print("✅ Retrieval Augmented Generation")
    print("✅ Gemini LLM Integration") 
    print("✅ Vector Database (ChromaDB)")
    print("✅ Enhanced Conversation Memory")
    print("✅ Intelligent Web Search")
    print("✅ Advanced Prompt Engineering")
    print()
    print("🌐 Server will be available at:")
    print("   http://localhost:8000")
    print("   http://localhost:8000/docs")
    print("   http://localhost:8000/agent/chat (Enhanced RAG)")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")