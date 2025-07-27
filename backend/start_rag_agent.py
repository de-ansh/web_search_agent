#!/usr/bin/env python3
"""
Start RAG Agent with uv
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    """Start the RAG Agent server"""
    
    print("🤖 Starting RAG AI Agent with uv")
    print("=" * 50)
    print("✅ Retrieval Augmented Generation")
    print("✅ Gemini LLM Integration") 
    print("✅ Vector Database (ChromaDB)")
    print("✅ Conversation Memory")
    print("✅ Web Search Integration")
    print("✅ Legacy API Compatibility")
    print()
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Please run this script from the backend directory")
        print("   cd backend && uv run python start_rag_agent.py")
        sys.exit(1)
    
    # Load environment variables
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Loaded environment variables from .env")
        
        # Check if Gemini API key is available
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            print(f"✅ Gemini API Key: {gemini_key[:10]}...{gemini_key[-4:]}")
        else:
            print("⚠️ Gemini API Key not found in environment")
    else:
        print("⚠️ .env file not found")
    
    # Set environment variables
    os.environ["PYTHONPATH"] = str(Path.cwd())
    
    print("🌐 Server will be available at:")
    print("   http://localhost:8000")
    print("   http://localhost:8000/docs")
    print("   http://localhost:8000/agent/chat (New RAG endpoint)")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Start the server using uvicorn
    import uvicorn
    uvicorn.run(
        "src.api.rag_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()