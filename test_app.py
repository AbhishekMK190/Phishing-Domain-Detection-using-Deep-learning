#!/usr/bin/env python3
"""
Test script for the phishing domain detection application
"""

import requests
import time

def test_app():
    """Test the Flask application"""
    base_url = "http://localhost:5000"
    
    print("Testing Phishing Domain Detection Application...")
    print("=" * 50)
    
    # Test 1: Check if the home page loads
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            print("✓ Home page loads successfully")
        else:
            print(f"✗ Home page failed to load. Status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to the application. Make sure it's running on http://localhost:5000")
        return False
    
    # Test 2: Test with a legitimate domain
    print("\nTesting with legitimate domain (google.com)...")
    try:
        response = requests.post(f"{base_url}/check_phishing", data={'url': 'google.com'})
        if response.status_code == 200:
            print("✓ Phishing check endpoint responds successfully")
            if "legitimate" in response.text.lower() or "phishing" in response.text.lower():
                print("✓ Result page displays correctly")
            else:
                print("✗ Result page may not be displaying correctly")
        else:
            print(f"✗ Phishing check failed. Status code: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing phishing check: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nTo use the application:")
    print("1. Make sure the Flask app is running (python app.py)")
    print("2. Open your browser and go to http://localhost:5000")
    print("3. Enter a domain name to check for phishing")

if __name__ == "__main__":
    test_app() 