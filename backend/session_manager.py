import json
from datetime import datetime
from profile_runner import profile_data
from llm_handler import generate_training_program
import os

# Constants
LIST_ACTIONS = ["create", "remove"]
INTERVAL_BETWEEN_SESSIONS = 6 * 60 * 60  # 6 hours in seconds
BASE_FOLDER = "profiles"

class SessionValidationError(Exception):
    """Custom exception for session validation errors"""
    pass

def get_profile_path(user_token):
    """Get the profile file path for a given user token"""
    return os.path.join(BASE_FOLDER, f"{user_token}.json")

def initialize_or_load_program(user_token):
    """Initialize new program or load existing one"""
    try:
        # Try to load existing program
        existing_program = load_program(user_token)
        
        # Check if the program has actual content
        if existing_program and "profile" in existing_program and "sessions" in existing_program:
            if existing_program["sessions"]:
                return {
                    'success': True,
                    'profile': existing_program["profile"],
                    'program': existing_program["sessions"],
                    'explanation': "Programme chargé depuis le fichier existant.",
                    'isNew': False
                }
        
        # If no valid existing program, create new one
        program, explanation, _ = generate_training_program(profile_data)
        if program:
            create_program(profile_data, program, user_token)
            return {
                'success': True,
                'profile': profile_data,
                'program': program,
                'explanation': explanation,
                'isNew': True
            }
        return {
            'success': False,
            'error': 'Failed to generate program'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def load_program(user_token):
    """Loads the training program from the user's profile file"""
    profile_path = get_profile_path(user_token)
    if not os.path.exists(profile_path):
        return {
            "profile": {},
            "sessions": []
        }
    
    try:
        with open(profile_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in profile file")
    except Exception as e:
        raise Exception(f"Error loading profile: {str(e)}")

def save_program(program_data, user_token):
    """Saves the training program to the user's profile file"""
    try:
        sorted_program = program_data.copy()
        
        if "sessions" in sorted_program:
            sorted_program["sessions"] = sorted(
                sorted_program["sessions"],
                key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M")
            )
        
        profile_path = get_profile_path(user_token)
        with open(profile_path, 'w', encoding='utf-8') as file:
            json.dump(sorted_program, file, indent=4, ensure_ascii=False)
            
    except Exception as e:
        raise Exception(f"Error saving profile: {str(e)}")

def create_program(profile_data, sessions, user_token):
    """Creates a new training program for a specific user"""
    program_data = {
        "profile": profile_data,
        "sessions": sessions
    }
    
    error_message = verify_json_overlap(sessions)
    if error_message:
        raise SessionValidationError(error_message)
    
    save_program(program_data, user_token)
    return program_data

# verify_json_action and verify_json_overlap remain unchanged as they don't need user_token

def apply_changes(json_data, user_token):
    """Applies changes to a specific user's program"""
    program_data = load_program(user_token)
    stored_sessions = program_data["sessions"]
    
    for action in json_data:
        error_message = verify_json_action(action)
        if error_message:
            raise SessionValidationError(f"Invalid JSON data: {error_message}")

        if action["type_action"] == "create":
            stored_sessions.append({
                "date": action["date"],
                "type_de_seance": action["type_de_seance"],
                "distance": action["distance"],
                "description": action["description"]
            })
        elif action["type_action"] == "remove":
            stored_sessions = [session for session in stored_sessions if session["date"] != action["date"]]

    error_message = verify_json_overlap(stored_sessions)
    if error_message:
        raise SessionValidationError(error_message)
    
    program_data["sessions"] = stored_sessions
    save_program(program_data, user_token)
    
    return program_data

def filter_sessions_by_date(user_token, from_date=None, to_date=None):
    """Filters sessions by date range for a specific user"""
    program_data = load_program(user_token)
    sessions = program_data["sessions"]
    filtered = []
    
    start_date = None
    end_date = None
    
    if from_date:
        try:
            start_date = datetime.strptime(from_date, "%d-%m-%Y")
        except ValueError:
            raise ValueError("Invalid from_date format. Use dd-mm-yyyy")
            
    if to_date:
        try:
            end_date = datetime.strptime(to_date, "%d-%m-%Y")
        except ValueError:
            raise ValueError("Invalid to_date format. Use dd-mm-yyyy")

    for session in sessions:
        session_date = datetime.strptime(session["date"], "%Y-%m-%d %H:%M")
        
        if start_date and session_date.date() < start_date.date():
            continue
        if end_date and session_date.date() > end_date.date():
            continue
            
        filtered.append(session)
    
    return filtered

def get_sorted_sessions(user_token, sort_order='asc'):
    """Returns sorted sessions for a specific user"""
    program_data = load_program(user_token)
    sessions = program_data["sessions"]
    
    return sorted(
        sessions,
        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M"),
        reverse=(sort_order.lower() == 'desc')
    )

def get_profile(user_token):
    """Returns the profile data for a specific user"""
    program_data = load_program(user_token)
    return program_data["profile"]

def update_profile(profile_data, user_token):
    """Updates the profile for a specific user"""
    program_data = load_program(user_token)
    program_data["profile"] = profile_data
    save_program(program_data, user_token)
    return program_data

def delete_program(user_token):
    """Deletes a specific user's program file"""
    profile_path = get_profile_path(user_token)
    if os.path.exists(profile_path):
        os.remove(profile_path)
        
def verify_json_action(json_data):
    """
    Verifies the structure and content of the JSON data.
    Returns an error message if verification fails.
    """
    required_keys = ["type_action", "date", "type_de_seance", "distance", "description"]
    
    # Check if all required keys are present
    if type(json_data) != dict:
        return f"Invalid JSON data. Expected a dictionary, got {type(json_data).__name__} instead."
    
    missing_keys = [key for key in required_keys if key not in json_data]
    if missing_keys:
        return f"Missing keys. Found: {', '.join(json_data.keys())}. Missing: {', '.join(missing_keys)}"
    
    # Check if "date" field is in correct format
    try:
        _ = datetime.strptime(json_data["date"], "%Y-%m-%d %H:%M")
    except ValueError:
        return "Invalid date format. Expected format is %Y-%m-%d %H:%M."
    
    # Check if "type_action" is valid
    if json_data["type_action"] not in LIST_ACTIONS:
        return f"Invalid type_action. Expected one of: {', '.join(LIST_ACTIONS)}"

    return None

def verify_json_overlap(stored_sessions):
    """
    Verifies that there are no overlapping sessions in the stored sessions.
    Returns an error message if verification fails.
    """
    for i, session1 in enumerate(stored_sessions):
        for j, session2 in enumerate(stored_sessions):
            if i != j:
                date1 = datetime.strptime(session1["date"], "%Y-%m-%d %H:%M")
                date2 = datetime.strptime(session2["date"], "%Y-%m-%d %H:%M")
                if abs((date1 - date2).total_seconds()) < INTERVAL_BETWEEN_SESSIONS:
                    return f"Overlapping sessions found. Ensure at least {INTERVAL_BETWEEN_SESSIONS // 3600} hours between sessions."
    return None
