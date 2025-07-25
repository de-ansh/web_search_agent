#!/usr/bin/env python3
"""
API Key Setup Script for Web Search Agent
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create a .env file with API key configuration"""
    env_file = Path(".env")
    
    print("🔑 Web Search Agent - API Key Setup")
    print("=" * 50)
    
    # Check if .env already exists
    if env_file.exists():
        print("⚠️  .env file already exists!")
        overwrite = input("Do you want to overwrite it? (y/N): ").lower().strip()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    print("\n📋 API Key Options:")
    print("1. OpenAI API (Recommended - Best quality summaries)")
    print("2. HuggingFace API (Free alternative)")
    print("3. Both (Best of both worlds)")
    print("4. Skip for now (Use extractive summarization only)")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    env_content = []
    env_content.append("# Web Search Agent Configuration")
    env_content.append("# Generated by setup_api_keys.py")
    env_content.append("")
    
    if choice in ["1", "3"]:
        print("\n🤖 OpenAI API Setup:")
        print("1. Go to: https://platform.openai.com/api-keys")
        print("2. Create a new API key")
        print("3. Copy the key (starts with 'sk-')")
        
        openai_key = input("\nPaste your OpenAI API key (or press Enter to skip): ").strip()
        if openai_key:
            env_content.append(f"OPENAI_API_KEY={openai_key}")
            print("✅ OpenAI API key added!")
        else:
            env_content.append("# OPENAI_API_KEY=your_openai_api_key_here")
    
    if choice in ["2", "3"]:
        print("\n🤗 HuggingFace API Setup:")
        print("1. Go to: https://huggingface.co/settings/tokens")
        print("2. Create a new token")
        print("3. Copy the token")
        
        hf_key = input("\nPaste your HuggingFace API token (or press Enter to skip): ").strip()
        if hf_key:
            env_content.append(f"HUGGINGFACE_API_KEY={hf_key}")
            print("✅ HuggingFace API key added!")
        else:
            env_content.append("# HUGGINGFACE_API_KEY=your_huggingface_api_key_here")
    
    # Add other configuration
    env_content.extend([
        "",
        "# Application Settings",
        "SIMILARITY_THRESHOLD=0.8",
        "MAX_SEARCH_RESULTS=5",
        "SUMMARY_MAX_LENGTH=150",
        "",
        "# Environment",
        "ENVIRONMENT=development",
        "LOG_LEVEL=INFO"
    ])
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write('\n'.join(env_content))
    
    print(f"\n✅ Configuration saved to {env_file}")
    print("\n🚀 Next steps:")
    print("1. Test the system: uv run python -m src.cli.main 'your test query'")
    print("2. Check the API usage in your provider's dashboard")
    print("3. Adjust settings in .env file if needed")

def test_api_keys():
    """Test if API keys are working"""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n🧪 Testing API Keys...")
    
    # Test OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            client = openai.Client(api_key=openai_key)
            # Simple test
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'API test successful'"}],
                max_tokens=10
            )
            print("✅ OpenAI API: Working!")
        except Exception as e:
            print(f"❌ OpenAI API: Error - {e}")
    else:
        print("⚠️  OpenAI API: Not configured")
    
    # Test HuggingFace
    hf_key = os.getenv("HUGGINGFACE_API_KEY")
    if hf_key:
        print("✅ HuggingFace API: Key found (testing requires model download)")
    else:
        print("⚠️  HuggingFace API: Not configured")

def main():
    """Main setup function"""
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_api_keys()
    else:
        create_env_file()
        
        # Ask if user wants to test
        test_now = input("\n🧪 Do you want to test the API keys now? (y/N): ").lower().strip()
        if test_now == 'y':
            test_api_keys()

if __name__ == "__main__":
    main() 