import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase

# Initialize Pyrebase for Firebase Authentication (Client SDK)
def initialize_pyrebase():
    firebase_config = {
        "apiKey": "",
        "authDomain": "",
        "projectId": "",
        "storageBucket": "",
        "messagingSenderId": "",
        "appId": "",
        "databaseURL": ""
    }
    firebase = pyrebase.initialize_app(firebase_config)
    return firebase

def initialize_firebase_admin():
    cred = credentials.Certificate("service_account.json")
    firebase_admin.initialize_app(cred)
    return firestore.client()

# Initialize Firestore and Auth clients
initialize_firebase_admin()
firebase = initialize_pyrebase()
auth = firebase.auth()
db = firestore.client()