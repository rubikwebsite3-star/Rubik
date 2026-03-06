import os
import sys

# Add current directory to path so we can import firebase_config
sys.path.append(os.getcwd())
from firebase_config import db

def add_admin(username, password):
    try:
        # Check if username already exists
        existing = db.collection("admins").where("username", "==", username).limit(1).get()
        if existing:
            print(f"Error: Admin '{username}' already exists.")
            return

        # Add new admin
        db.collection("admins").add({
            "username": username,
            "password": password
        })
        print(f"Successfully added admin: {username}")
    except Exception as e:
        print(f"Error adding admin: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python add_admin.py <username> <password>")
    else:
        add_admin(sys.argv[1], sys.argv[2])
