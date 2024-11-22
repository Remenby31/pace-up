import json
from datetime import datetime
from profile_runner import profile_data
from llm_handler import generate_training_program

import os

# Constants
LIST_ACTIONS = ["create", "remove"]
INTERVAL_BETWEEN_SESSIONS = 6 * 60 * 60  # 6 hours in seconds
PROFILE_FILE = "profile.json"

class SessionValidationError(Exception):
    """Custom exception for session validation errors"""
    pass

def initialize_or_load_program():
    """Initialize new program or load existing one"""
    try:
        # Try to load existing program
        existing_program = load_program()
        
        # Check if the program has actual content
        if existing_program and "profile" in existing_program and "sessions" in existing_program:
            if existing_program["sessions"]:  # If there are sessions
                print("Programme chargé depuis le fichier existant.")
                return {
                    'success': True,
                    'profile': existing_program["profile"],
                    'program': existing_program["sessions"],
                    'explanation': "Programme chargé depuis le fichier existant.",
                    'isNew': False
                }
        
        # If no valid existing program, create new one
        print("Initialisation d'un nouveau programme.")
        program, explanation, _ = generate_training_program(profile_data)
        if program:
            create_program(profile_data, program)
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

def load_program():
    """
    Loads the training program from the profile.json file.
    If the file doesn't exist, returns empty program structure.
    """
    if not os.path.exists(PROFILE_FILE):
        return {
            "profile": {},
            "sessions": []
        }
    
    try:
        with open(PROFILE_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in profile file")
    except Exception as e:
        raise Exception(f"Error loading profile: {str(e)}")

def save_program(program_data):
    """
    Saves the training program to the profile.json file.
    Sessions are sorted chronologically before saving.
    
    Parameters:
    - program_data (dict): Dictionary containing profile and sessions data
    """
    try:
        # Create a copy to avoid modifying the original data
        sorted_program = program_data.copy()
        
        # Sort sessions by date if they exist
        if "sessions" in sorted_program:
            sorted_program["sessions"] = sorted(
                sorted_program["sessions"],
                key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M")
            )
        
        # Save the sorted program
        with open(PROFILE_FILE, 'w', encoding='utf-8') as file:
            json.dump(sorted_program, file, indent=4, ensure_ascii=False)
            
    except Exception as e:
        raise Exception(f"Error saving profile: {str(e)}")

def create_program(profile_data, sessions):
    """
    Creates a new training program with profile data and sessions.
    
    Parameters:
    - profile_data (dict): Athlete profile information
    - sessions (list): List of training sessions
    """
    program_data = {
        "profile": profile_data,
        "sessions": sessions
    }
    
    # Validate sessions before saving
    error_message = verify_json_overlap(sessions)
    if error_message:
        raise SessionValidationError(error_message)
    
    save_program(program_data)
    return program_data

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

def apply_changes(json_data):
    """
    Applies the changes specified in the JSON data to the stored sessions.
    Returns the updated program data.
    """
    program_data = load_program()
    stored_sessions = program_data["sessions"]
    
    # Verify and apply each action in the JSON data
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

    # Verify no overlapping sessions
    error_message = verify_json_overlap(stored_sessions)
    if error_message:
        raise SessionValidationError(error_message)
    
    # Update and save program
    program_data["sessions"] = stored_sessions
    save_program(program_data)
    
    return program_data

def filter_sessions_by_date(from_date=None, to_date=None):
    """
    Filters sessions by date range from the stored program.
    
    Parameters:
    - from_date (str): Start date in format "dd-mm-yyyy"
    - to_date (str): End date in format "dd-mm-yyyy"
    """
    program_data = load_program()
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

def get_sorted_sessions(sort_order='asc'):
    """
    Returns all sessions sorted by date.
    
    Parameters:
    - sort_order (str): 'asc' for ascending, 'desc' for descending
    """
    program_data = load_program()
    sessions = program_data["sessions"]
    
    return sorted(
        sessions,
        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M"),
        reverse=(sort_order.lower() == 'desc')
    )

def get_profile():
    """Returns the current profile data"""
    program_data = load_program()
    return program_data["profile"]

def update_profile(profile_data):
    """
    Updates the profile information in the stored program.
    
    Parameters:
    - profile_data (dict): New profile information
    """
    program_data = load_program()
    program_data["profile"] = profile_data
    save_program(program_data)
    return program_data

def delete_program():
    """Deletes the entire training program file"""
    if os.path.exists(PROFILE_FILE):
        os.remove(PROFILE_FILE)