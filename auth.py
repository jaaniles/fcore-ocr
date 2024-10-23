import json
import os
import asyncio

from firebase import auth

# Path to save the session token
session_file = "./local_cache/session.json"

# Save session to a file
def save_session(user):
    with open(session_file, 'w') as f:
        json.dump(user, f)

# Load session from a file
def load_session():
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            return json.load(f)
    return None

# Refresh the token if it's expired
def refresh_session(user):
    try:
        refreshed_user = auth.refresh(user['refreshToken'])
        save_session(refreshed_user)  # Update session with refreshed token
        return refreshed_user
    except Exception as e:
        print(f"Failed to refresh token: {e}")
        return None

# Synchronous function for restoring session
def sync_restore_session(session):
    if session:
        try:
            # Refresh the session to validate or renew the token
            user = refresh_session(session)
            if user:
                return user
        except Exception as e:
            print(f"Error restoring session: {e}")
    return None

# Asynchronous wrapper around restore_session
async def restore_session(session):
    if not session:
        return None

    loop = asyncio.get_event_loop()
    try:
        # Run the synchronous restore_session in the background using asyncio's executor
        user = await loop.run_in_executor(None, sync_restore_session, session)
        return user
    except Exception as e:
        print(f"Error in async restore session: {e}")
        return None

# Load credentials from file
def load_credentials():
    with open('credentials.json', 'r') as file:
        credentials_data = json.load(file)
    return credentials_data["email"], credentials_data["password"]


def sync_authenticate_user(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return user
    except Exception as e:
        raise e

# Asynchronous function to authenticate the user
async def authenticate_user(email, password):
    loop = asyncio.get_event_loop()
    try:
        # Run the synchronous authentication function in an executor (separate thread)
        user = await loop.run_in_executor(None, sync_authenticate_user, email, password)
        save_session(user)  # Save the session after successful authentication
        print("Successfully authenticated")
        return user
    except Exception as e:
        print(f"Authentication failed: {e}")
        return None

# Helper function for restoring session or authenticating the user
async def restore_or_authenticate(session):
    # Try restoring session
    user = await restore_session(session)

    # If session restoration fails, authenticate
    if not user:
        print("Restoring session failed. Starting fresh authentication.")
        email, password = load_credentials()  # Load credentials from a local file
        user = await authenticate_user(email, password)  # Authenticate the user

    return user