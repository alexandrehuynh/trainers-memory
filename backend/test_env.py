import os
from dotenv import load_dotenv

# Explicitly load the .env file
load_dotenv(verbose=True)

print("Environment variables loaded:")
print(f"OPENAI_API_KEY: {'*' * 8 + os.getenv('OPENAI_API_KEY')[-5:] if os.getenv('OPENAI_API_KEY') else 'Not found'}")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL') or 'Not found'}")
print(f"JWT_SECRET: {'*' * 8 + os.getenv('JWT_SECRET')[-5:] if os.getenv('JWT_SECRET') else 'Not found'}")
print(f"TESSERACT_CMD: {os.getenv('TESSERACT_CMD') or 'Not found'}") 