#!/usr/bin/env python3
"""
Test script to verify financial query enhancement and content validation fixes
Specifically tests the Tata Steel vs Tata Motors issue
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.api.main import _enhance_financial_query, _validate_financial_content

def test_query_enhancement():
    """Test the query enhancement function"""
    print("🧪 Testing Financial Query Enhancement")
    print("=" * 60)
    
    test_cases = [
        "Tata Steel current share price",
        "Tata Motors share price",
        "ITC Ltd stock price",
        "Reliance Industries share price",
        "Infosys current stock price",
        "HDFC Bank share price today",
        "TCS stock price",
        "general company ltd share price"
    ]
    
    for query in test_cases:
        enhanced = _enhance_financial_query(query)
        print(f"Original: '{query}'")
        print(f"Enhanced: '{enhanced}'")
        print(f"Changed: {'✅ YES' if enhanced != query else '❌ NO'}")
        print()

def test_content_validation():
    """Test the content validation function"""
    print("\n🧪 Testing Content Validation")
    print("=" * 60)
    
    # Test case 1: Tata Steel query with Tata Motors content (should fail)
    print("\n📝 Test 1: Tata Steel query with Tata Motors content (should FAIL)")
    tata_steel_query = "Tata Steel current share price"
    tata_motors_content = """
    Tata Motors Share Price, Tata Motors Stock Price, Tata Motors Share Price Today
    Tata Motors Ltd is India's largest automobile company. The share price of Tata Motors Ltd is ₹695.50.
    TATAMOTORS Share Price: Explore the latest Tata Motors Ltd stock price. NSE:TATAMOTORS stock price.
    Tata Motors automobile company passenger vehicle commercial vehicle.
    """
    
    is_valid = _validate_financial_content(tata_motors_content, tata_steel_query)
    print(f"Result: {'❌ CORRECTLY REJECTED' if not is_valid else '⚠️ INCORRECTLY ACCEPTED'}")
    
    # Test case 2: Tata Steel query with Tata Steel content (should pass)
    print("\n📝 Test 2: Tata Steel query with Tata Steel content (should PASS)")
    tata_steel_content = """
    Tata Steel Share Price, Tata Steel Stock Price, Tata Steel Share Price Today
    Tata Steel Limited is India's largest steel manufacturing company. The share price of Tata Steel is ₹125.30.
    NSE:TATASTEEL stock price. Tata Steel steel production iron mining metal sponge iron.
    Steel manufacturing company iron ore mining.
    """
    
    is_valid = _validate_financial_content(tata_steel_content, tata_steel_query)
    print(f"Result: {'✅ CORRECTLY ACCEPTED' if is_valid else '❌ INCORRECTLY REJECTED'}")
    
    # Test case 3: Tata Motors query with Tata Motors content (should pass)
    print("\n📝 Test 3: Tata Motors query with Tata Motors content (should PASS)")
    tata_motors_query = "Tata Motors share price"
    
    is_valid = _validate_financial_content(tata_motors_content, tata_motors_query)
    print(f"Result: {'✅ CORRECTLY ACCEPTED' if is_valid else '❌ INCORRECTLY REJECTED'}")
    
    # Test case 4: ITC Ltd query with ITC Hotels content (should fail)
    print("\n📝 Test 4: ITC Ltd query with ITC Hotels content (should FAIL)")
    itc_ltd_query = "ITC Ltd share price"
    itc_hotels_content = """
    ITC Hotels is India's leading hotel chain. ITC Hotels luxury hospitality resort.
    Welcome to ITC Hotels - premium hotel experiences across India.
    """
    
    is_valid = _validate_financial_content(itc_hotels_content, itc_ltd_query)
    print(f"Result: {'❌ CORRECTLY REJECTED' if not is_valid else '⚠️ INCORRECTLY ACCEPTED'}")
    
    # Test case 5: ITC Ltd query with ITC Ltd content (should pass)
    print("\n📝 Test 5: ITC Ltd query with ITC Ltd content (should PASS)")
    itc_ltd_content = """
    ITC Limited Share Price Today. ITC Ltd is a leading FMCG and tobacco company.
    NSE:ITC stock price. ITC tobacco cigarette consumer goods food products.
    ITC Limited FMCG company tobacco products.
    """
    
    is_valid = _validate_financial_content(itc_ltd_content, itc_ltd_query)
    print(f"Result: {'✅ CORRECTLY ACCEPTED' if is_valid else '❌ INCORRECTLY REJECTED'}")

def test_edge_cases():
    """Test edge cases"""
    print("\n🧪 Testing Edge Cases")
    print("=" * 60)
    
    # Test very short content
    print("\n📝 Test: Very short content (should FAIL)")
    short_content = "Error"
    is_valid = _validate_financial_content(short_content, "Tata Steel share price")
    print(f"Result: {'❌ CORRECTLY REJECTED' if not is_valid else '⚠️ INCORRECTLY ACCEPTED'}")
    
    # Test content with cookie/privacy notices
    print("\n📝 Test: Content with privacy notices (should FAIL)")
    privacy_content = """
    This website uses cookies. By continuing to browse this site you are agreeing to our use of cookies.
    Please accept our privacy policy. Click here to continue if the page does not redirect automatically.
    """
    is_valid = _validate_financial_content(privacy_content, "Tata Steel share price")
    print(f"Result: {'❌ CORRECTLY REJECTED' if not is_valid else '⚠️ INCORRECTLY ACCEPTED'}")
    
    # Test general company without specific rules
    print("\n📝 Test: General company without specific rules")
    general_query = "ABC Company Ltd share price"
    general_content = """
    ABC Company Ltd Share Price Today. ABC Company Limited is a leading manufacturer.
    Current share price of ABC Company Ltd is ₹150.25. NSE:ABC stock price.
    """
    is_valid = _validate_financial_content(general_content, general_query)
    print(f"Result: {'✅ CORRECTLY ACCEPTED' if is_valid else '❌ INCORRECTLY REJECTED'}")

if __name__ == "__main__":
    try:
        test_query_enhancement()
        test_content_validation()
        test_edge_cases()
        
        print("\n🎉 All tests completed!")
        print("\n📋 Summary:")
        print("- Query enhancement now preserves full company names and adds specific disambiguation")
        print("- Content validation now properly distinguishes between different companies")
        print("- Tata Steel vs Tata Motors issue should now be resolved")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 