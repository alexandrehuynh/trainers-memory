#!/usr/bin/env python
"""
Script to securely update environment variables in .env file.
This script updates environment variables without exposing them in version control.
"""

import os
import sys
from dotenv import load_dotenv

def update_env_file(env_file_path, updates):
    """
    Update environment variables in a .env file.
    
    Args:
        env_file_path: Path to the .env file
        updates: Dictionary of key-value pairs to update
    """
    # Load existing environment
    load_dotenv(env_file_path)
    
    # Read existing .env file
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Process lines
    updated_keys = set()
    updated_lines = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            updated_lines.append(line)
            continue
            
        # Parse key=value
        if '=' in line:
            key = line.split('=')[0].strip()
            if key in updates:
                updated_lines.append(f"{key}={updates[key]}")
                updated_keys.add(key)
            else:
                updated_lines.append(line)
    
    # Add any keys that weren't already in the file
    for key, value in updates.items():
        if key not in updated_keys:
            updated_lines.append(f"{key}={value}")
    
    # Write back to file
    with open(env_file_path, 'w') as f:
        for line in updated_lines:
            f.write(f"{line}\n")
    
    print(f"Updated {env_file_path} with keys: {', '.join(updates.keys())}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python update_env.py PATH_TO_ENV_FILE KEY1=VALUE1 [KEY2=VALUE2 ...]")
        return
    
    env_file_path = sys.argv[1]
    updates = {}
    
    for arg in sys.argv[2:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            updates[key] = value
    
    update_env_file(env_file_path, updates)

if __name__ == "__main__":
    main() 