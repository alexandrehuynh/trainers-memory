#!/usr/bin/env python
"""
Script to verify Supabase JWT settings.

This script tests the JWT validation for Supabase tokens
and helps diagnose JWT-related issues.
"""

import os
import sys
import jwt
import logging
import base64
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def decode_jwt_without_verification(token):
    """Decode a JWT token without verifying the signature."""
    try:
        # Split the token into parts
        parts = token.split('.')
        if len(parts) != 3:
            return {'error': 'Token does not have three parts'}
        
        # Decode the payload (middle part)
        # Add padding if needed
        payload_part = parts[1]
        padding = '=' * (4 - len(payload_part) % 4)
        if padding == 4:
            padding = ''
        
        padded = payload_part + padding
        decoded = base64.b64decode(padded.replace('-', '+').replace('_', '/'))
        payload = json.loads(decoded)
        
        return payload
    except Exception as e:
        return {'error': str(e)}

def verify_jwt(token, secret, algorithms=None):
    """Try to verify a JWT using the provided secret."""
    if algorithms is None:
        algorithms = ['HS256', 'HS384', 'HS512']
    
    results = []
    for algorithm in algorithms:
        try:
            payload = jwt.decode(token, secret, algorithms=[algorithm])
            return {
                'success': True,
                'algorithm': algorithm,
                'payload': payload
            }
        except jwt.ExpiredSignatureError:
            results.append({
                'algorithm': algorithm,
                'status': 'Token has expired',
                'success': False,
                'is_valid_format': True
            })
        except jwt.InvalidSignatureError:
            results.append({
                'algorithm': algorithm,
                'status': 'Invalid signature',
                'success': False,
                'is_valid_format': True
            })
        except jwt.InvalidTokenError as e:
            results.append({
                'algorithm': algorithm,
                'status': f'Invalid token: {str(e)}',
                'success': False,
                'is_valid_format': False
            })
        except Exception as e:
            results.append({
                'algorithm': algorithm,
                'status': f'Error: {str(e)}',
                'success': False,
                'is_valid_format': False
            })
    
    return {
        'success': False,
        'results': results
    }

def check_supabase_settings():
    """Check and verify Supabase JWT settings."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Checking Supabase JWT settings...")
    
    # Get JWT secret
    jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
    if not jwt_secret:
        logger.error("SUPABASE_JWT_SECRET is not set in the environment")
        return False
    
    # Display info about the secret (safely)
    logger.info(f"SUPABASE_JWT_SECRET is set (length: {len(jwt_secret)})")
    
    # Ask for a token
    token = input("Enter a Supabase JWT token to test (optional): ")
    if not token:
        logger.info("No token provided. You can try again with a valid token.")
        return True
    
    # Decode the token without verification
    logger.info("Decoding token without verification...")
    payload = decode_jwt_without_verification(token)
    logger.info(f"Token payload: {json.dumps(payload, indent=2)}")
    
    # Check for issuer - should be 'supabase'
    if payload.get('iss') != 'supabase':
        logger.warning(f"Token issuer is not 'supabase', found: {payload.get('iss')}")
    
    # Try to verify with the secret
    logger.info("Attempting to verify token with SUPABASE_JWT_SECRET...")
    result = verify_jwt(token, jwt_secret)
    
    if result.get('success'):
        logger.info(f"Token verified successfully using algorithm: {result.get('algorithm')}")
        logger.info(f"Verified payload: {json.dumps(result.get('payload'), indent=2)}")
        return True
    else:
        logger.error("Token verification failed")
        for algorithm_result in result.get('results', []):
            logger.error(f"Algorithm {algorithm_result.get('algorithm')}: {algorithm_result.get('status')}")
        
        # Suggest potential fixes
        logger.info("\nPossible solutions:")
        logger.info("1. Make sure SUPABASE_JWT_SECRET is set correctly in your .env file")
        logger.info("2. Check if the token is expired")
        logger.info("3. Verify that the token is actually from your Supabase project")
        logger.info("4. Make sure you are using the raw JWT secret (not the Base64 encoded version)")
        
        return False

if __name__ == "__main__":
    success = check_supabase_settings()
    sys.exit(0 if success else 1) 