import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase

# Initialize Pyrebase for Firebase Authentication (Client SDK)
def initialize_pyrebase():
    firebase_config = {
        "apiKey": "AIzaSyDUVn-gRRBTYmmyOAGjxQYJafPCc3uk7Jg",
        "authDomain": "fcore-1337.firebaseapp.com",
        "projectId": "fcore-1337",
        "storageBucket": "fcore-1337.appspot.com",
        "messagingSenderId": "40848952203",
        "appId": "1:40848952203:web:74cf4a7e254a2e6160bd8e",
        "databaseURL": "https://fcore-1337.firebaseio.com"
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