#!/usr/bin/env python3
"""
Debug script to test problematic domains like ChatGPT and LeetCode
"""

import requests
import json
import sys

def test_domain(domain):
    """Test a domain with the API"""
    print(f"\n🔍 Testing domain: {domain}")
    
    try:
        # Test API health first
        health_response = requests.get('http://127.0.0.1:5000/api/health', timeout=10)
        if health_response.status_code == 200:
            print("✅ API health check passed")
        else:
            print(f"❌ API health check failed: {health_response.status_code}")
            return
        
        # Test domain check
        payload = {"domain": domain}
        print(f"📤 Sending request: {json.dumps(payload)}")
        
        response = requests.post(
            'http://127.0.0.1:5000/api/check',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Response data: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Raw response: {response.text}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response text: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the Flask server running?")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    print("🛡️ Quanta AI Domain Debug Tool")
    print("=" * 50)
    
    # Test problematic domains
    problematic_domains = [
        "chat.openai.com",
        "leetcode.com",
        "www.leetcode.com",
        "openai.com",
        "github.com",  # Control test
        "google.com"   # Control test
    ]
    
    for domain in problematic_domains:
        test_domain(domain)
        print("-" * 50)

if __name__ == "__main__":
    main()
