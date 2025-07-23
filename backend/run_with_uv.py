#!/usr/bin/env python3
"""
Run the enhanced web scraping application with uv
"""

import subprocess
import sys
import os
from pathlib import Path
import time

def run_command(cmd, description="", check=True, capture_output=False):
    """Run a command with proper error handling"""
    print(f"🔄 {description}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        if capture_output:
            result = subprocess.run(cmd, check=check, capture_output=True, text=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=check)
            print(f"✅ {description} completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if capture_output and e.stdout:
            print(f"   Output: {e.stdout}")
        if capture_output and e.stderr:
            print(f"   Error: {e.stderr}")
        if check:
            sys.exit(1)
        return None

def check_uv_installed():
    """Check if uv is installed"""
    try:
        result = run_command(["uv", "--version"], "Checking uv installation", capture_output=True)
        print(f"✅ uv is installed: {result}")
        return True
    except:
        print("❌ uv is not installed")
        print("   Please install uv first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("   or visit: https://docs.astral.sh/uv/getting-started/installation/")
        return False

def setup_environment():
    """Set up the development environment with uv"""
    print("🚀 Setting up Enhanced Web Scraping Environment")
    print("=" * 50)
    
    # Check if uv is installed
    if not check_uv_installed():
        return False
    
    # Sync dependencies
    run_command(["uv", "sync"], "Installing dependencies with uv")
    
    # Install playwright browsers
    print("🎭 Installing Playwright browsers...")
    run_command(["uv", "run", "playwright", "install", "chromium"], "Installing Chromium for Playwright")
    
    return True

def setup_api_keys():
    """Set up API keys interactively"""
    print("\n🔑 Setting up API Keys")
    print("=" * 30)
    
    # Check if .env exists
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file found")
        
        # Check for existing keys
        with open(env_path, 'r') as f:
            env_content = f.read()
            
        has_gemini = "GEMINI_API_KEY" in env_content
        has_openai = "OPENAI_API_KEY" in env_content
        
        print(f"   Gemini API Key: {'✅ Found' if has_gemini else '❌ Not found'}")
        print(f"   OpenAI API Key: {'✅ Found' if has_openai else '❌ Not found'}")
        
        if not has_gemini and not has_openai:
            print("\n⚠️  No API keys found. Running setup...")
            run_command(["uv", "run", "python", "setup_gemini_api.py"], "Setting up API keys")
        else:
            setup_keys = input("\nDo you want to update API keys? (y/N): ").lower().strip()
            if setup_keys == 'y':
                run_command(["uv", "run", "python", "setup_gemini_api.py"], "Updating API keys")
    else:
        print("❌ .env file not found. Creating one...")
        run_command(["uv", "run", "python", "setup_gemini_api.py"], "Setting up API keys")

def test_installation():
    """Test the installation"""
    print("\n🧪 Testing Installation")
    print("=" * 25)
    
    # Test basic imports
    test_script = '''
import sys
try:
    from src.services.enhanced_research_service import EnhancedResearchService
    from src.ai.gemini_summarizer import GeminiSummarizer
    from src.core.enhanced_scraper import EnhancedScraper
    print("✅ All imports successful")
    
    # Test service initialization
    service = EnhancedResearchService()
    status = service.get_status()
    print(f"✅ Service initialized: {status['service']}")
    
except Exception as e:
    print(f"❌ Import test failed: {e}")
    sys.exit(1)
'''
    
    with open("test_imports.py", "w") as f:
        f.write(test_script)
    
    try:
        run_command(["uv", "run", "python", "test_imports.py"], "Testing imports")
        os.remove("test_imports.py")
    except:
        if os.path.exists("test_imports.py"):
            os.remove("test_imports.py")
        return False
    
    return True

def run_server():
    """Run the FastAPI server with uv"""
    print("\n🚀 Starting Enhanced Web Scraping Server")
    print("=" * 40)
    
    print("Server will be available at:")
    print("   🌐 http://localhost:8000")
    print("   📚 API Docs: http://localhost:8000/docs")
    print("   🔍 Enhanced Research: http://localhost:8000/research/enhanced")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 40)
    
    try:
        # Run the server
        subprocess.run([
            "uv", "run", "uvicorn", 
            "src.api.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped by user")

def run_tests():
    """Run the enhanced research tests"""
    print("\n🧪 Running Enhanced Research Tests")
    print("=" * 35)
    
    run_command(["uv", "run", "python", "test_enhanced_research.py"], "Running enhanced research tests")

def show_usage():
    """Show usage instructions"""
    print("\n📖 Usage Instructions")
    print("=" * 20)
    print("Available commands:")
    print("   python run_with_uv.py setup    - Set up environment and dependencies")
    print("   python run_with_uv.py server   - Start the FastAPI server")
    print("   python run_with_uv.py test     - Run tests")
    print("   python run_with_uv.py keys     - Set up API keys")
    print("   python run_with_uv.py all      - Do everything (setup + keys + test + server)")
    print("\nDirect uv commands:")
    print("   uv run uvicorn src.api.main:app --reload")
    print("   uv run python test_enhanced_research.py")
    print("   uv run python setup_gemini_api.py")
    print("   uv run python example_usage.py")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    
    # Change to backend directory if not already there
    if not Path("pyproject.toml").exists():
        backend_path = Path(__file__).parent
        os.chdir(backend_path)
        print(f"📁 Changed to directory: {backend_path}")
    
    if command == "setup":
        if setup_environment():
            print("\n🎉 Environment setup completed!")
            print("Next steps:")
            print("1. Set up API keys: python run_with_uv.py keys")
            print("2. Run tests: python run_with_uv.py test")
            print("3. Start server: python run_with_uv.py server")
    
    elif command == "keys":
        setup_api_keys()
    
    elif command == "test":
        if test_installation():
            run_tests()
        else:
            print("❌ Installation test failed. Please run setup first.")
    
    elif command == "server":
        run_server()
    
    elif command == "all":
        print("🚀 Complete Setup and Run")
        print("=" * 25)
        
        if setup_environment():
            setup_api_keys()
            if test_installation():
                print("\n✅ All tests passed! Starting server...")
                time.sleep(2)
                run_server()
            else:
                print("❌ Tests failed. Please check the setup.")
        else:
            print("❌ Environment setup failed.")
    
    else:
        print(f"❌ Unknown command: {command}")
        show_usage()

if __name__ == "__main__":
    main()