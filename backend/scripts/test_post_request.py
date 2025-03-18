#!/usr/bin/env python
"""
Test POST Request Script

This script makes a POST request to create a client with an API key.

Usage:
    python test_post_request.py [api_key]
"""

import os
import sys
import argparse
import requests
import json
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

def test_post_request(api_key: str):
    """Make a POST request to create a client with the given API key."""
    # Construct the full URL
    base_url = "http://localhost:8000"
    endpoint = "/api/v1/clients"
    
    url = f"{base_url}{endpoint}"
    
    print(f"Making POST request to: {url}")
    print(f"Using API key: {api_key}")
    
    # Generate random data to avoid duplicates
    random_num = random.randint(1000, 9999)
    
    # Request payload
    data = {
        "name": f"Test Client {random_num}",
        "email": f"test{random_num}@example.com",
        "phone": f"555-{random_num}",
        "notes": "Created via test script"
    }
    
    print(f"Request payload: {json.dumps(data, indent=2)}")
    
    # Set up headers with API key
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Make the request
    try:
        response = requests.post(url, json=data, headers=headers)
        
        # Print response details
        print(f"\nStatus code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code < 300:
            print("\n✅ Request SUCCESSFUL!")
            print("Response body:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("\n❌ Request FAILED!")
            print("Response body:")
            try:
                print(json.dumps(response.json(), indent=2))
            except:
                print(response.text)
                
        return response.status_code < 300
            
    except Exception as e:
        print(f"\n⚠️ Error making request: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test a POST request with an API key.')
    parser.add_argument('api_key', nargs='?', default='tmk_40af9844458144dc9ba5f5859c8b0f02', help='The API key to use')
    args = parser.parse_args()
    
    # Make the request
    success = test_post_request(args.api_key)
    
    # Provide some troubleshooting tips if the request failed
    if not success:
        print("\nTroubleshooting tips:")
        print("1. Check if the API server is running")
        print("2. Verify the API key exists in the database")
        print("3. Check for any logging output from the API server")
        print("4. Make sure the API key has permission to create clients")

if __name__ == '__main__':
    main() 