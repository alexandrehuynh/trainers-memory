import sys
import jwt
import base64
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")

def decode_token_without_verification(token):
    """Decode a JWT token without verifying signature (for debugging)"""
    try:
        # JWT tokens have 3 parts: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            print("Invalid token format (should have 3 parts)")
            return
            
        # Decode the header
        header_padded = parts[0] + '=' * (4 - len(parts[0]) % 4)
        header_decoded = base64.urlsafe_b64decode(header_padded)
        header = json.loads(header_decoded)
        
        print("\n--- TOKEN HEADER ---")
        print(json.dumps(header, indent=2))
        
        # Decode the payload (middle part)
        payload_padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
        payload_decoded = base64.urlsafe_b64decode(payload_padded)
        payload = json.loads(payload_decoded)
        
        print("\n--- TOKEN PAYLOAD ---")
        print(json.dumps(payload, indent=2))
        
        # Check for key claims
        print("\n--- KEY CLAIMS ---")
        print(f"sub (user ID): {payload.get('sub', 'NOT FOUND')}")
        print(f"exp (expiration): {payload.get('exp', 'NOT FOUND')}")
        print(f"role: {payload.get('user_metadata', {}).get('role', 'NOT FOUND')}")
        
        return payload
        
    except Exception as e:
        print(f"Error decoding token: {str(e)}")
        return None

def verify_token(token):
    """Try to verify the token using JWT_SECRET"""
    if not JWT_SECRET:
        print("\nWarning: JWT_SECRET not found in environment variables")
        return False
        
    print(f"\n--- VERIFYING TOKEN WITH JWT_SECRET ---")
    print(f"Using secret: {JWT_SECRET[:5]}...")
    
    try:
        # Try to decode and verify the token
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        print("✅ Token verification SUCCESSFUL!")
        return True
    except jwt.ExpiredSignatureError:
        print("❌ Token verification FAILED: Token has expired")
        return False
    except jwt.InvalidSignatureError:
        print("❌ Token verification FAILED: Invalid signature")
        print("This likely means your JWT_SECRET doesn't match the one used to create the token")
        return False
    except Exception as e:
        print(f"❌ Token verification FAILED: {str(e)}")
        return False

def main():
    print("=== JWT Token Inspector ===")
    
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        # Try to read from jwt_token.txt
        try:
            with open("jwt_token.txt", "r") as f:
                token = f.read().strip()
                print(f"Using token from jwt_token.txt")
        except:
            token = input("Enter the JWT token: ")
    
    # First decode without verification
    payload = decode_token_without_verification(token)
    
    # Then try to verify
    if payload:
        verify_token(token)
        
        print("\n--- DEBUGGING TIPS ---")
        print("1. Make sure your JWT_SECRET in .env matches your Supabase JWT secret")
        print("2. Check if the token has expired (look at the 'exp' claim)")
        print("3. Verify the token contains a 'role' claim with value 'trainer'")
        print("4. Ensure the token is being sent correctly in Authorization header")

if __name__ == "__main__":
    main() 