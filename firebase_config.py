import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

key_path = os.getenv('FIREBASE_KEY_PATH', 'firebase_key.json')
cred = credentials.Certificate(key_path)

firebase_admin.initialize_app(cred)
db = firestore.client()
