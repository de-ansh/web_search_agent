#!/usr/bin/env python3
"""
Setup script for Gemini API configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv, set_key

def setup_gemini_api():
    """Setup Gemini API key configuration"""
    
    print("🚀 Gemini API Setup for Enhanced Web Scraping")
    print("=" * 50)
    
    # Load existing .env file
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
    
    # Check current status
    current_gemini = os.getenv("GEMINI_API_KEY")
    current_openai = os.getenv("OPENAI_API_KEY")
    
    print("📋 Current API Key Status:")
    print(f"   Gemini API Key: {'✅ Configured' if current_gemini else '❌ Not configured'}")
    print(f"   OpenAI API Key: {'✅ Configured' if current_openai else '❌ Not configured'}")
    print()
    
    # Gemini API setup
    print("🤖 Gemini API Configuration")
    print("-" * 30)
    print("To get your Gemini API key:")
    print("1. Go to https://makersuite.google.com/app/apikey")
    print("2. Sign in with your Google account")
    print("3. Click 'Create API Key'")
    print("4. Copy the generated API key")
    print()
    
    if current_gemini:
        print(f"Current Gemini API key: {current_gemini[:10]}...{current_gemini[-4:]}")
        update = input("Do you want to update it? (y/N): ").lower().strip()
        if update != 'y':
            print("✅ Keeping existing Gemini API key")
        else:
            new_key = input("Enter your new Gemini API key: ").strip()
            if new_key:
                set_key(env_path, "GEMINI_API_KEY", new_key)
                print("✅ Gemini API key updated!")
            else:
                print("❌ No key provided, keeping existing key")
    else:
        new_key = input("Enter your Gemini API key (or press Enter to skip): ").strip()
        if new_key:
            set_key(env_path, "GEMINI_API_KEY", new_key)
            print("✅ Gemini API key configured!")
        else:
            print("⏭️  Skipping Gemini API key setup")
    
    print()
    
    # OpenAI API setup (optional fallback)
    print("🔄 OpenAI API Configuration (Optional Fallback)")
    print("-" * 45)
    
    if not current_openai:
        setup_openai = input("Do you want to configure OpenAI as a fallback? (y/N): ").lower().strip()
        if setup_openai == 'y':
            print("To get your OpenAI API key:")
            print("1. Go to https://platform.openai.com/api-keys")
            print("2. Sign in to your OpenAI account")
            print("3. Click 'Create new secret key'")
            print("4. Copy the generated API key")
            print()
            
            openai_key = input("Enter your OpenAI API key: ").strip()
            if openai_key:
                set_key(env_path, "OPENAI_API_KEY", openai_key)
                print("✅ OpenAI API key configured as fallback!")
            else:
                print("⏭️  Skipping OpenAI API key setup")
        else:
            print("⏭️  Skipping OpenAI API key setup")
    else:
        print(f"✅ OpenAI API key already configured: {current_openai[:10]}...{current_openai[-4:]}")
    
    print()
    
    # Final status
    load_dotenv(env_path)  # Reload to get updated values
    final_gemini = os.getenv("GEMINI_API_KEY")
    final_openai = os.getenv("OPENAI_API_KEY")
    
    print("📊 Final Configuration Status:")
    print(f"   Gemini API Key: {'✅ Configured' if final_gemini else '❌ Not configured'}")
    print(f"   OpenAI API Key: {'✅ Configured' if final_openai else '❌ Not configured'}")
    print()
    
    if final_gemini or final_openai:
        print("🎉 API configuration completed!")
        print("You can now use the enhanced web scraping with AI summarization.")
        print()
        print("Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run the test: python test_enhanced_research.py")
        print("3. Integrate with your application")
    else:
        print("⚠️  No API keys configured.")
        print("The system will fall back to extractive summarization.")
        print("For best results, configure at least one AI API key.")
    
    print()
    print("📝 Configuration saved to:", env_path)

def test_api_keys():
    """Test the configured API keys"""
    print("\n🧪 Testing API Keys")
    print("=" * 20)
    
    # Load environment
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    # Test Gemini
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-pro')
            
            # Simple test
            response = model.generate_content("Say 'Hello, Gemini API is working!'")
            if response.text:
                print("✅ Gemini API: Working correctly")
                print(f"   Response: {response.text.strip()}")
            else:
                print("❌ Gemini API: No response received")
        except Exception as e:
            print(f"❌ Gemini API: Error - {e}")
    else:
        print("⏭️  Gemini API: Not configured")
    
    # Test OpenAI
    if openai_key:
        try:
            import openai
            client = openai.Client(api_key=openai_key)
            
            # Simple test
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'Hello, OpenAI API is working!'"}],
                max_tokens=20
            )
            
            if response.choices[0].message.content:
                print("✅ OpenAI API: Working correctly")
                print(f"   Response: {response.choices[0].message.content.strip()}")
            else:
                print("❌ OpenAI API: No response received")
        except Exception as e:
            print(f"❌ OpenAI API: Error - {e}")
    else:
        print("⏭️  OpenAI API: Not configured")

def main():
    """Main function for script execution"""
    setup_gemini_api()
    
    # Ask if user wants to test
    test = input("\nDo you want to test the API keys now? (y/N): ").lower().strip()
    if test == 'y':
        test_api_keys()
    
    print("\n🎯 Setup complete! Happy researching!")

if __name__ == "__main__":
    main()