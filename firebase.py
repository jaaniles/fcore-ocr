import json
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase

def load_config():
    with open('firebase_config.json') as config_file:
        return json.load(config_file)

# Initialize Pyrebase for Firebase Authentication (Client SDK)
def initialize_pyrebase(config):
    firebase_config = config['firebase']

    firebase = pyrebase.initialize_app(firebase_config)
    return firebase

def initialize_firebase_admin():
    cred = credentials.Certificate("service_account.json")
    firebase_admin.initialize_app(cred)
    return firestore.client()

firebase_config = load_config()

# Initialize Firestore and Auth clients
initialize_firebase_admin()
firebase = initialize_pyrebase(firebase_config)
auth = firebase.auth()
db = firestore.client()