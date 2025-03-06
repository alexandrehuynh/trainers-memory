import requests
import os
from dotenv import load_dotenv
import json
import webbrowser
import time

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # This is your anon/public key

if not SUPABASE_URL or not SUPABASE_KEY:
    # If SUPABASE_KEY isn't found, try the SERVICE_KEY or other variations
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing Supabase credentials. Check your .env file.")
    
print(f"Using Supabase URL: {SUPABASE_URL}")
print(f"Using Supabase Key: {SUPABASE_KEY[:10]}...")

# 1. Sign up a user (skip if user already exists)
def sign_up_user(email, password):
    print(f"\n--- Creating new user: {email} ---")
    response = requests.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        headers={
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        },
        json={
            "email": email,
            "password": password,
            "data": {
                "role": "trainer"  # Set user role during signup
            }
        }
    )
    print(f"Signup Status: {response.status_code}")
    result = response.json()
    
    # Don't print the full token if present
    if "access_token" in result:
        result["access_token"] = result["access_token"][:15] + "..."
    
    print(json.dumps(result, indent=2))
    return response.json()

# 2. Sign in to get access token
def sign_in_user(email, password):
    print(f"\n--- Signing in user: {email} ---")
    response = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        },
        json={
            "email": email,
            "password": password
        }
    )
    print(f"Signin Status: {response.status_code}")
    data = response.json()
    
    # Handle successful login
    if "access_token" in data:
        # Save token to a file for easy access
        with open("jwt_token.txt", "w") as f:
            f.write(data["access_token"])
        print(f"Token saved to jwt_token.txt")
        
        # Show a preview of the token
        print(f"Access Token Preview: {data['access_token'][:20]}...")
        
        # Show expiry time if available
        if "expires_in" in data:
            print(f"Token expires in: {data['expires_in']} seconds")
            
        # Return full data
        return data
    else:
        # Show error
        print(f"Error: {json.dumps(data, indent=2)}")
        return data

# 2B. Send a magic link
def send_magic_link(email):
    print(f"\n--- Sending magic link to: {email} ---")
    response = requests.post(
        f"{SUPABASE_URL}/auth/v1/magiclink",
        headers={
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        },
        json={
            "email": email
        }
    )
    print(f"Magic Link Request Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ Magic link sent to {email}")
        print("\n--- IMPORTANT: HOW TO GET YOUR JWT TOKEN ---")
        print("1. Check your email and click the magic link")
        print("2. After you're redirected to your app and logged in:")
        print("   a. Open browser DevTools (F12 or Cmd+Option+I)")
        print("   b. Go to the Application tab > Local Storage")
        print("   c. Look for 'supabase.auth.token'")
        print("   d. Copy the access_token value inside")
        print("\nAlternatively, use the Supabase Dashboard:")
        print("1. Go to https://app.supabase.com/project/_/auth/users")
        print("2. Find your user and click 'Generate link'")
        print("3. Open the generated URL in your browser")
        
        # Open the Supabase dashboard auth page
        open_dashboard = input("\nWould you like to open the Supabase Auth dashboard? (y/n): ")
        if open_dashboard.lower() == 'y':
            webbrowser.open(f"https://app.supabase.com/project/{SUPABASE_URL.split('/')[-1].split('.')[0]}/auth/users")
    else:
        try:
            print(f"Error: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Error: {response.text}")
    
    return response

# 3. Update user role to trainer (in case it wasn't set during signup)
def update_user_role(email):
    print(f"\n--- Setting {email} as trainer ---")
    
    # Note: This function may not work with anon key, it might require service key
    response = requests.post(
        f"{SUPABASE_URL}/auth/v1/admin/users/{email}/roles",
        headers={
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SUPABASE_KEY}"
        },
        json={
            "role": "trainer"
        }
    )
    print(f"Update Role Status: {response.status_code}")
    if response.status_code != 200:
        print("Note: You may need to update the role manually in Supabase SQL Editor with:")
        print(f"""
        UPDATE auth.users 
        SET raw_user_meta_data = jsonb_set(raw_user_meta_data, '{{role}}', '"trainer"')
        WHERE email = '{email}';
        """)
    else:
        print(response.json())

# 4. Test the token against your FastAPI endpoint
def test_api_with_token(token, endpoint="/clients"):
    print(f"\n--- Testing API with token ---")
    response = requests.get(
        f"http://localhost:8000{endpoint}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    print(f"API Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    
    return response

# 5. Directly enter a token
def enter_token_manually():
    print("\n--- Enter JWT Token Manually ---")
    token = input("Paste your JWT token: ")
    
    if token:
        # Save token to a file for easy access
        with open("jwt_token.txt", "w") as f:
            f.write(token)
        print(f"Token saved to jwt_token.txt")
        
        # Ask if user wants to test it
        test_now = input("Would you like to test this token with your API? (y/n): ")
        if test_now.lower() == 'y':
            endpoint = input("Enter endpoint (default: /clients): ") or "/clients"
            test_api_with_token(token, endpoint)
    else:
        print("No token entered.")

# 6. Get token from LocalStorage via instruction
def get_token_instructions():
    print("\n--- How to Get Your JWT Token from the Browser ---")
    print("If you've signed in using magic link or through your app:")
    print("1. Open your browser DevTools (F12 or Cmd+Option+I on Mac)")
    print("2. Go to the Application tab")
    print("3. Select Local Storage from the sidebar")
    print("4. Look for your Supabase domain")
    print("5. Find the key 'supabase.auth.token'")
    print("6. Copy the 'access_token' value from inside")
    print("\nOnce you have it, use option 5 in the main menu to enter it.")
    
    input("\nPress Enter to return to the main menu...")

if __name__ == "__main__":
    print("=== Supabase Auth Test Utility ===")
    print("This utility helps get valid JWT tokens for your FastAPI app")
    
    # Menu system
    while True:
        print("\nSelect an option:")
        print("1. Sign up a new user with password")
        print("2. Sign in with password to get JWT token")
        print("3. Send magic link (no password needed)")
        print("4. Update user role to trainer")
        print("5. Enter JWT token manually")
        print("6. How to get token from browser")
        print("7. Test API with token")
        print("8. Exit")
        
        choice = input("\nEnter choice (1-8): ")
        
        if choice == "1":
            email = input("Enter email: ")
            password = input("Enter password: ")
            sign_up_user(email, password)
        
        elif choice == "2":
            email = input("Enter email: ")
            password = input("Enter password: ")
            token_data = sign_in_user(email, password)
            
            if "access_token" in token_data:
                print("\n=== JWT TOKEN (COPY THIS) ===")
                print(token_data["access_token"])
        
        elif choice == "3":
            email = input("Enter email: ")
            send_magic_link(email)
        
        elif choice == "4":
            email = input("Enter email: ")
            update_user_role(email)
            
        elif choice == "5":
            enter_token_manually()
            
        elif choice == "6":
            get_token_instructions()
        
        elif choice == "7":
            # Try to read token from file first
            try:
                with open("jwt_token.txt", "r") as f:
                    token = f.read().strip()
                    print(f"Using token from jwt_token.txt: {token[:15]}...")
            except:
                token = input("Enter JWT token: ")
                
            endpoint = input("Enter endpoint (default: /clients): ") or "/clients"
            test_api_with_token(token, endpoint)
            
        elif choice == "8":
            print("Exiting...")
            break
            
        else:
            print("Invalid choice. Please try again.") 