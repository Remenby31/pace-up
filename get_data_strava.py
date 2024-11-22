import requests
import json
import os
import dotenv
import time
from datetime import datetime
from typing import List, Dict, Optional

# Load environment variables
dotenv.load_dotenv()

def get_initial_tokens(client_id: str, client_secret: str, code: str) -> Dict:
    """Get initial access and refresh tokens using the authorization code."""
    auth_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': str(client_id),  # Conversion en string
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.post(auth_url, data=payload)
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get tokens: {str(e)}")

def save_tokens(tokens: Dict, filename: str = "strava_tokens.json") -> None:
    """Save tokens to a file."""
    with open(filename, 'w') as f:
        json.dump(tokens, f)

def load_tokens(filename: str = "strava_tokens.json") -> Dict:
    """Load tokens from a file."""
    with open(filename, 'r') as f:
        return json.load(f)

class StravaActivityFetcher:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tokens = None
        self.base_url = "https://www.strava.com/api/v3"

    def refresh_access_token(self) -> None:
        """Refreshes the access token using the refresh token."""
        auth_url = "https://www.strava.com/oauth/token"
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.tokens['refresh_token'],
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(auth_url, data=payload)
            response.raise_for_status()
            self.tokens = response.json()
            save_tokens(self.tokens)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to refresh token: {str(e)}")

    def fetch_activities(self, per_page: int = 100) -> List[Dict]:
        """Fetches all activities from Strava."""
        if not self.tokens:
            try:
                self.tokens = load_tokens()
            except FileNotFoundError:
                raise Exception("No tokens found. Please run authentication first.")

        activities = []
        page = 1
        
        while True:
            params = {
                'per_page': per_page,
                'page': page
            }
            headers = {'Authorization': f'Bearer {self.tokens["access_token"]}'}
            
            try:
                response = requests.get(f"{self.base_url}/athlete/activities", 
                                     headers=headers, params=params)
                response.raise_for_status()
                page_activities = response.json()
                
                if not page_activities:
                    break
                    
                activities.extend(page_activities)
                page += 1
                time.sleep(1)  # Respect rate limits
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 401:
                    # Token expired, refresh and retry
                    self.refresh_access_token()
                    continue
                if response.status_code == 429:  # Rate limit exceeded
                    time.sleep(15 * 60)  # Wait 15 minutes
                    continue
                raise Exception(f"Failed to fetch activities: {str(e)}")
                
        return activities

    def save_activities(self, activities: List[Dict], folder_path: str = "strava_run") -> None:
        """Saves activities to JSON files in the specified folder."""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            
        # Save all activities in a single file
        all_activities_path = os.path.join(folder_path, "all_activities.json")
        with open(all_activities_path, 'w') as f:
            json.dump(activities, f, indent=2)
            
        # Save each activity in a separate file
        for activity in activities:
            activity_date = datetime.strptime(activity['start_date'], "%Y-%m-%dT%H:%M:%SZ")
            filename = f"{activity_date.strftime('%Y%m%d')}_{activity['id']}.json"
            filepath = os.path.join(folder_path, filename)
            
            with open(filepath, 'w') as f:
                json.dump(activity, f, indent=2)

def main():
    client_id = os.environ.get("STRAVA_CLIENT_ID")
    client_secret = os.environ.get("STRAVA_CLIENT_SECRET")
    
    # Authentification initiale déjà faite, on peut commenter ces lignes
    # code = "0c003e4433266a52b5155428becfc243d8261938"
    # tokens = get_initial_tokens(client_id, client_secret, code)
    # save_tokens(tokens)
    
    fetcher = StravaActivityFetcher(client_id, client_secret)
    activities = fetcher.fetch_activities()
    fetcher.save_activities(activities)


if __name__ == "__main__":
    main()