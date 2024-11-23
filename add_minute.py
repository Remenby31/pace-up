import requests
import json
import sys
from typing import Optional

def advance_time(minutes: int = 10, base_url: str = "https://pace-up.duckdns.org") -> Optional[dict]:
    """
    Envoie une requête GET pour faire avancer la simulation d'un certain nombre de minutes
    
    Args:
        minutes (int): Nombre de minutes à ajouter (défaut: 10)
        base_url (str): URL de base de l'API
    
    Returns:
        dict: Réponse de l'API ou None en cas d'erreur
    """
    endpoint = "{}/api/activity/add_time/{}".format(base_url, minutes)

    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        
        try:
            result = response.json()
            print("✓ Temps avancé de {} minutes".format(minutes))
            return result
        except requests.exceptions.JSONDecodeError:
            print("Réponse invalide du serveur: {}".format(response.text))
            return None
        
    except requests.HTTPError as http_err:
        print("Erreur HTTP {}".format(response.status_code))
        try:
            error_data = response.json()
            print("Message d'erreur: {}".format(error_data['message']))
        except:
            print("Contenu de la réponse: {}".format(response.text[:200]))
    except requests.ConnectionError:
        print("Erreur de connexion: Impossible de se connecter à {}".format(base_url))
        print("Vérifiez que le serveur est accessible et que vous avez une connexion internet")
    except Exception as e:
        print("Erreur inattendue: {}".format(str(e)))
    
    return None

def validate_minutes(minutes_str: str) -> Optional[int]:
    """
    Valide et convertit l'argument minutes
    
    Args:
        minutes_str: La valeur à valider
        
    Returns:
        int ou None en cas d'erreur
    """
    try:
        minutes = int(minutes_str)
        if minutes <= 0:
            print("Erreur: Le nombre de minutes doit être positif")
            return None
        if minutes > 1440:  # 24 heures
            print("Attention: Vous ajoutez plus de 24 heures")
        return minutes
    except ValueError:
        print("Erreur: L'argument doit être un nombre entier de minutes")
        return None

if __name__ == "__main__":
    # Permet de spécifier un nombre de minutes différent en argument
    minutes = 10
    if len(sys.argv) > 1:
        validated_minutes = validate_minutes(sys.argv[1])
        if validated_minutes is None:
            sys.exit(1)
        minutes = validated_minutes

    # Affiche les informations de la requête
    print("Envoi de la requête pour ajouter {} minutes...".format(minutes))
    print("URL: https://pace-up.duckdns.org/api/activity/add_time/{}".format(minutes))
    
    result = advance_time(minutes)
    if result:
        print("\nRéponse de l'API:")
        print(json.dumps(result, indent=2))