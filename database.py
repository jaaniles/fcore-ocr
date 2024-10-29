from firebase import db

def get_user_teams(user_id):
    try:
        teams_ref = db.collection('team')
        query = teams_ref.where('userId', '==', user_id).stream()

        user_teams = []
        for doc in query:
            team_data = doc.to_dict()
            team_data['id'] = doc.id
            user_teams.append(team_data)

        if not user_teams:
            print(f"No teams found for user ID: {user_id}")
        else:
            print(f"Found {len(user_teams)} teams for user ID: {user_id}")
        
        return user_teams

    except Exception as e:
        print(f"Error fetching user teams: {e}")
        return None
    
def save_to_collection(collection_name, data):
    """
    Saves data to a specified Firestore collection.
    
    Parameters:
        collection_name (str): The name of the Firestore collection.
        data (dict): The data to save.
        
    Returns:
        str: Document ID of the saved document, or None if there was an error.
    """
    try:
        doc_ref = db.collection(collection_name).add(data)
        print(f"Data saved to {collection_name} with ID: {doc_ref[1].id}")
        return doc_ref[1].id  # Return the document ID

    except Exception as e:
        print(f"Error saving to {collection_name}: {e}")
        return None