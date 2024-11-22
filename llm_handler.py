import os, re, json
from datetime import datetime
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from llm_template_french import coach_prompt, program_generation_prompt, suggestions_prompt

# LangChain Initialization
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Create runnable chain with the coach prompt and LLM model
chain = (
    {
        "current_datetime": lambda x: x["current_datetime"],
        "input": lambda x: x["input"],
        "context_program": lambda x: x["context_program"]
    }
    | coach_prompt 
    | llm 
    | StrOutputParser()
)

# Add this new chain after the existing chain
program_generation_chain = (
    {
        "age": lambda x: x["profile_data"]["age"],
        "poids": lambda x: x["profile_data"]["poids"],
        "taille": lambda x: x["profile_data"]["taille"],
        "frequence_hebdomadaire": lambda x: x["profile_data"]["frequence_hebdomadaire"],
        "meilleure_distance_recente": lambda x: x["profile_data"]["meilleure_distance_recente"],
        "objectif_principal": lambda x: x["profile_data"]["objectif_principal"],
        "distance_cible": lambda x: x["profile_data"]["distance_cible"],
        "chrono_cible": lambda x: x["profile_data"]["chrono_cible"],
        "temps_actuel_5km": lambda x: x["profile_data"]["temps_actuel_5km"],
        "temps_actuel_10km": lambda x: x["profile_data"]["temps_actuel_10km"],
        "jours_disponibles_par_semaine": lambda x: x["profile_data"]["jours_disponibles_par_semaine"],
        "jour_sortie_longue": lambda x: x["profile_data"]["jour_sortie_longue"],
        "current_date": lambda x: x["current_date"],
        "goal_date": lambda x: x["profile_data"]["goal_date"]

    }
    | program_generation_prompt 
    | llm 
    | StrOutputParser()
)


def generate_training_program(profile_data):
    """
    Generates a complete training program based on athlete profile data.
    
    Parameters:
    - profile_data (dict): Dictionary containing athlete profile information
    
    Returns:
    - tuple: (list of training sessions as JSON objects, explanation string, full response text)
    """
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    try:
        print("Generating training program...")
        response = program_generation_chain.invoke({
            "profile_data": profile_data,
            "current_date": current_date
        })

        print(response)
        
        try:
            json_objects = extract_training_sessions(response)
            explanation = extract_brief_explanation(response)

            print(f"{len(json_objects)} training sessions generated.")
            
            # Validate all sessions
            for session in json_objects:
                if not validate_date_format(session["date"]):
                    raise ValueError(f"Invalid date format in program: {session['date']}")
                
                # Add additional validation if needed
                if not isinstance(session["distance"], (int, float)):
                    raise ValueError("Distance must be a number")
                
                if not session["type_de_seance"] or not session["description"]:
                    raise ValueError("Session type and description are required")
            
            return json_objects, explanation, response
            
        except ValueError as e:
            print(f"Warning: Error in program generation: {str(e)}")
            return None, None, response
            
    except Exception as e:
        raise Exception(f"Failed to generate training program: {str(e)}")


import json
import re

def extract_json_objects(response_text):
    """
    Extraits les objets JSON d'une réponse LLM texte de façon récursive.
    Retourne une liste d'objets JSON parsés si disponible.
    """
    # Définir les clés requises
    REQUIRED_KEYS = {"type_action", "date", "type_de_seance", "distance", "description"}
    
    def is_valid_json_object(obj):
        """
        Vérifie si l'objet JSON contient toutes les clés requises
        et ajoute les clés manquantes avec des valeurs par défaut si nécessaire
        """
        if not isinstance(obj, dict):
            return False, None
            
        # Si c'est une action de suppression, on accepte les champs vides
        if obj.get('type_action') == 'remove':
            # On s'assure que la date est présente
            if 'date' not in obj:
                return False, None
                
            # On crée un nouvel objet avec toutes les clés requises
            complete_obj = {
                'type_action': 'remove',
                'date': obj['date'],
                'type_de_seance': '',
                'distance': 0,
                'description': ''
            }
            return True, complete_obj
            
        # Pour les autres actions, on vérifie toutes les clés
        if not all(key in obj for key in REQUIRED_KEYS):
            return False, None
            
        # Vérifier que les valeurs ne sont pas vides pour create
        if obj.get('type_action') == 'create':
            if not all(obj[key] for key in ['date', 'type_de_seance', 'description']):
                return False, None
            if not isinstance(obj['distance'], (int, float)) or obj['distance'] <= 0:
                return False, None
                
        return True, obj

    def parse_json_content(content):
        """
        Fonction récursive qui parse le contenu JSON et retourne une liste d'objets
        """
        if isinstance(content, list):
            result = []
            for item in content:
                result.extend(parse_json_content(item))
            return result
        elif isinstance(content, dict):
            is_valid, validated_obj = is_valid_json_object(content)
            return [validated_obj] if is_valid else []
        else:
            try:
                parsed = json.loads(content)
                return parse_json_content(parsed)
            except (json.JSONDecodeError, TypeError):
                return []

    try:
        # Essayer de parser directement le texte comme JSON
        try:
            return parse_json_content(json.loads(response_text))
        except json.JSONDecodeError:
            pass
        
        # Chercher les blocs JSON dans le format markdown
        json_blocks = re.findall(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        
        if json_blocks:
            result = []
            for block in json_blocks:
                # Gérer les blocs contenant plusieurs objets
                if block.strip().startswith('{') and block.count('{') > 1:
                    block = f"[{block}]"
                try:
                    parsed = json.loads(block)
                    result.extend(parse_json_content(parsed))
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse JSON block: {e}")
                    continue
            
            if result:
                return result
        
        # Chercher les objets JSON sans balises markdown
        json_pattern = r'(\{[^{}]*\})'
        json_objects = re.finditer(json_pattern, response_text, re.DOTALL)
        
        result = []
        for match in json_objects:
            try:
                parsed = json.loads(match.group(0))
                is_valid, validated_obj = is_valid_json_object(parsed)
                if is_valid:
                    result.append(validated_obj)
            except json.JSONDecodeError:
                continue
        
        if not result:
            return []
            #raise ValueError("No valid JSON objects found in the response text.")
            
        return result
            
    except Exception as e:
        raise ValueError(f"Error parsing JSON objects: {e}")

def extract_training_sessions(response_text):
    """
    Extraits les sessions d'entraînement d'une réponse LLM texte.
    """
    REQUIRED_KEYS = {"date", "type_de_seance", "distance", "description"}
    
    def is_valid_session(obj):
        if not isinstance(obj, dict):
            return False, None
            
        if not all(key in obj for key in REQUIRED_KEYS):
            return False, None
            
        if not all(obj[key] for key in ['date', 'type_de_seance', 'description']):
            return False, None
        if not isinstance(obj['distance'], (int, float)) or obj['distance'] <= 0:
            return False, None
            
        return True, obj

    def parse_json_content(content):
        if isinstance(content, list):
            result = []
            for item in content:
                result.extend(parse_json_content(item))
            return result
        elif isinstance(content, dict):
            is_valid, validated_obj = is_valid_session(content)
            return [validated_obj] if is_valid else []
        else:
            try:
                parsed = json.loads(content)
                return parse_json_content(parsed)
            except (json.JSONDecodeError, TypeError):
                return []

    try:
        try:
            return parse_json_content(json.loads(response_text))
        except json.JSONDecodeError:
            pass
        
        json_blocks = re.findall(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        if json_blocks:
            result = []
            for block in json_blocks:
                if block.strip().startswith('{') and block.count('{') > 1:
                    block = f"[{block}]"
                try:
                    parsed = json.loads(block)
                    result.extend(parse_json_content(parsed))
                except json.JSONDecodeError:
                    continue
            if result:
                return result
        
        json_pattern = r'(\{[^{}]*\})'
        json_objects = re.finditer(json_pattern, response_text)
        
        result = []
        for match in json_objects:
            try:
                parsed = json.loads(match.group(0))
                is_valid, validated_obj = is_valid_session(parsed)
                if is_valid:
                    result.append(validated_obj)
            except json.JSONDecodeError:
                continue
        
        return result
            
    except Exception as e:
        raise ValueError(f"Error parsing JSON objects: {e}")



def extract_brief_explanation(response_text):
    """
    Extracts a brief explanation from the response text.
    """
    explanation = None
    try:
        explanation = re.search(r"Explanation:(.*)", response_text, re.DOTALL).group(1).strip()
        # On enelve les ** si présents
        explanation = explanation.replace("**", "").strip()
    except AttributeError:
        pass
    return explanation

def validate_date_format(date_str):
    """
    Validates that the date string matches the required format (YYYY-MM-DD HH:mm)
    and that minutes are in increments of 5
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        if date_obj.minute % 5 != 0:
            raise ValueError("Minutes must be in increments of 5")
        return True
    except ValueError as e:
        return False

def format_context_program(context_program):
    """
    Formats the context program for better readability in the prompt.
    """
    if isinstance(context_program, str):
        try:
            context_program = json.loads(context_program)
        except json.JSONDecodeError:
            return context_program

    if isinstance(context_program, dict):
        return json.dumps(context_program, indent=2)
    elif isinstance(context_program, list):
        return json.dumps(context_program, indent=2)
    else:
        return str(context_program)

def process_llm_request(user_input, context_program=None, message_history=None):
    """
    Process the user input through the LLM chain and extract JSON objects.
    
    Parameters:
    - user_input (str): The user's request
    - context_program (dict/list/str): The current training program in JSON format
    - message_history (list): List of previous messages with roles and content
    """
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Format the context program
    formatted_context = format_context_program(context_program) if context_program else "No existing training sessions."
    
    # Format message history
    history_context = ""
    if message_history:
        history_context = "\nPrevious messages:\n" + "\n".join(
            f"{msg['role']}: {msg['content']}" 
            for msg in message_history[-10:]  # Last 10 messages
        )
    
    try:
        response = chain.invoke({
            "current_datetime": current_datetime,
            "input": f"{history_context}\n\nCurrent request: {user_input}",
            "context_program": formatted_context
        })
        
        try:
            json_objects = extract_json_objects(response)
            explanation = extract_brief_explanation(response)
            return json_objects, explanation, response
        except ValueError as e:
            print(f"Warning: {str(e)}")
            return None, None, response
            
    except Exception as e:
        raise Exception(f"Failed to process training request: {str(e)}")


# Créer une nouvelle chaîne pour les suggestions
suggestions_chain = (
    {
        "current_datetime": lambda x: x["current_datetime"],
        "chat_history": lambda x: x["chat_history"],
        "input": lambda x: x["input"],
        "context_program": lambda x: x["context_program"]
    }
    | suggestions_prompt 
    | llm 
    | StrOutputParser()
)

def extract_suggestions(response_text):
    """
    Extrait les trois suggestions d'une réponse LLM.
    """
    suggestions = []
    current_suggestion = ""
    current_number = None
    
    lines = response_text.split('\n')
    
    for line in lines:
        if line.startswith('SUGGESTION_'):
            if current_suggestion and current_number:
                suggestions.append({
                    'number': current_number,
                    'content': current_suggestion.strip()
                })
            current_number = int(line.split('_')[1].split(':')[0])
            current_suggestion = ""
        else:
            current_suggestion += line + "\n"
    
    # Ajouter la dernière suggestion
    if current_suggestion and current_number:
        suggestions.append({
            'number': current_number,
            'content': current_suggestion.strip()
        })
    
    return suggestions

def process_suggestions_request(user_input, context_program=None, message_history=None):
    """
    Génère trois suggestions de réponse pour une demande utilisateur.
    """
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Formater l'historique du chat
    formatted_history = "Pas d'historique." if not message_history else "\n".join(
        f"{msg['role']}: {msg['content']}" 
        for msg in message_history[-5:]  # Derniers 5 messages
    )
    
    # Formater le contexte du programme
    formatted_context = format_context_program(context_program) if context_program else "Pas de sessions d'entraînement."
    
    try:
        response = suggestions_chain.invoke({
            "current_datetime": current_datetime,
            "chat_history": formatted_history,
            "input": user_input,
            "context_program": formatted_context
        })
        
        suggestions = extract_suggestions(response)
        
        # Pour chaque suggestion, extraire les objets JSON si présents
        for suggestion in suggestions:
            content = suggestion['content']
            json_objects = extract_json_objects(content)
            if json_objects:
                suggestion['json_objects'] = json_objects
        
        return suggestions
        
    except Exception as e:
        raise Exception(f"Failed to generate suggestions: {str(e)}")