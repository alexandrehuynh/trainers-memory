#!/usr/bin/env python
"""
Test API Request Script

This script makes actual HTTP requests to the API with an API key
to test authentication directly.

Usage:
    python test_api_request.py [endpoint] [api_key]
"""

import os
import sys
import argparse
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_request(endpoint: str, api_key: str):
    """Make a request to the API with the given API key."""
    # Construct the full URL
    base_url = "http://localhost:8000"
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    
    url = f"{base_url}{endpoint}"
    
    print(f"Making request to: {url}")
    print(f"Using API key: {api_key}")
    
    # Set up headers with API key
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json"
    }
    
    # Make the request
    try:
        response = requests.get(url, headers=headers)
        
        # Print response details
        print(f"\nStatus code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code < 300:
            print("\n✅ Request SUCCESSFUL!")
            print("Response body:")
            print(response.json())
        else:
            print("\n❌ Request FAILED!")
            print("Response body:")
            try:
                print(response.json())
            except:
                print(response.text)
                
        return response.status_code < 300
            
    except Exception as e:
        print(f"\n⚠️ Error making request: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test an API request with an API key.')
    parser.add_argument('endpoint', nargs='?', default='/api/v1/me', help='The API endpoint to request')
    parser.add_argument('api_key', nargs='?', default='tmk_3db7baed7f1c40bb9e39b9c512fdcf8d', help='The API key to use')
    args = parser.parse_args()
    
    # Make the request
    success = test_api_request(args.endpoint, args.api_key)
    
    # Provide some troubleshooting tips if the request failed
    if not success:
        print("\nTroubleshooting tips:")
        print("1. Check if the API server is running")
        print("2. Verify the API key exists in the database")
        print("3. Check for any logging output from the API server")
        print("4. Try generating a new API key with: python scripts/generate_api_key.py")

if __name__ == '__main__':
    main() 