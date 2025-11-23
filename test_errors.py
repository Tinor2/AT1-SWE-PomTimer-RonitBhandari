#!/usr/bin/env python3
"""
Simple script to test error pages by making requests to various endpoints.
"""

import requests
import sys

def test_error_pages():
    base_url = "http://127.0.0.1:5000"
    
    print("Testing error pages...")
    print(f"Base URL: {base_url}")
    print("-" * 50)
    
    # Test 404 error
    try:
        response = requests.get(f"{base_url}/nonexistent-page")
        print(f"404 Test - Status: {response.status_code}")
        if response.status_code == 404:
            print("✅ 404 error page working correctly")
        else:
            print("❌ 404 error page not working")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the Flask app is running.")
        return
    
    # Test 403 error (try accessing a protected route without login)
    try:
        response = requests.get(f"{base_url}/lists")
        print(f"403 Test - Status: {response.status_code}")
        if response.status_code == 403 or response.status_code == 302:
            print("✅ Access control working (redirecting to login)")
        else:
            print("❌ Access control may not be working properly")
    except Exception as e:
        print(f"❌ 403 test failed: {e}")
    
    # Test main page
    try:
        response = requests.get(f"{base_url}/")
        print(f"Main Page - Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Main page accessible")
        else:
            print("❌ Main page not accessible")
    except Exception as e:
        print(f"❌ Main page test failed: {e}")
    
    print("-" * 50)
    print("Error page testing complete!")

if __name__ == "__main__":
    test_error_pages()
