from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for, make_response, Response
from flask_sock import Sock
from threading import Event
import time
import json
import requests
from datetime import datetime
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from llm_handler import process_llm_request, process_suggestions_request
from session_manager import apply_changes, get_sorted_sessions, get_profile, initialize_or_load_program
from calendar_manager import CalendarManager
from flask_restx import Api, Resource, fields
from functools import wraps
from flask import Response
from activity_simulator import ActivitySimulator
import urllib.parse
from auth import AuthManager
import secrets

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)
sock = Sock(app)

app.secret_key = secrets.token_hex(32)  # Clé secrète pour les sessions
csrf = CSRFProtect(app)  # Activation de la protection CSRF
CORS(app)

key_static = 'avatVRKqyldREW2vwYeBd9ltNboJGPsXRetLipCxyLY'

auth_manager = AuthManager()


def check_user_session():
    jwt = session.get('user_token')
    if not jwt or not auth_manager.verify_token(jwt):
        return redirect(url_for('login'))
    return None

@app.before_request
def check_login():
    # Exclude login/static routes from check
    if request.endpoint and request.endpoint not in ['login', 'static', 'favicon', 'test', 'register', 'get_activity_data', 'reset_simulation', 'get_status', 'add_time', 'get_distance', 'get_pace', 'get_time', 'api_chat']:
        redirect_response = check_user_session()
        if redirect_response:
            return redirect_response

# Décorateur pour vérifier l'authentification
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_token' not in session:
            print("Authentication required")
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# === Routes d'authentification ===

@app.route('/')
def index():
    """Route principale - redirige vers le dashboard si connecté"""
    if 'user_token' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Gestion de la connexion"""
    if 'user_token' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        return render_template('login.html')
    
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Format de requête invalide'}), 400

    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'success': False, 'message': 'Données manquantes'}), 400

    success, result = auth_manager.login(data['username'], data['password'])
    if success:
        session['user_token'] = result
        session.permanent = True  # Cookie de session persistant
        return jsonify({'success': True, 'redirect': url_for('dashboard')})
    
    return jsonify({'success': False, 'message': result}), 401

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Gestion de l'inscription"""
    if 'user_token' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        return render_template('register.html')
    
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Format de requête invalide'}), 400

    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'success': False, 'message': 'Données manquantes'}), 400

    success, message = auth_manager.register(data['username'], data['password'])
    if success:
        return jsonify({'success': True, 'message': message})
    
    return jsonify({'success': False, 'message': message}), 400

@app.route('/logout')
def logout():
    """Déconnexion de l'utilisateur"""
    session.clear()
    return redirect(url_for('login'))

# === Routes protégées ===

@app.route('/dashboard')
@login_required
def dashboard():
    """Page du tableau de bord"""
    return render_template('dashboard.html')

@app.route('/init-program', methods=['GET'])
@login_required
def init_program():
    """Initialize or load the training program"""
    jwt = session.get('user_token')
    user_token = auth_manager.get_user_token_from_jwt(jwt)
    result = initialize_or_load_program(user_token)
    return jsonify(result)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'success': True, 'message': 'Mams le boss'})

@app.route('/chat', methods=['POST'])
@login_required
def chat():
   try:
       if not request.is_json:
           return jsonify({'success': False, 'error': 'Format de requête invalide'}), 400

       data = request.get_json()
       message = data.get('message')
       history = data.get('history', [])
       jwt = session.get('user_token')
       user_token = auth_manager.get_user_token_from_jwt(jwt)
       
       if not message:
           return jsonify({'success': False, 'error': 'Message manquant'}), 400
           
       json_objects, explanation, response = process_llm_request(
           message, 
           context_program=get_sorted_sessions(user_token),
           message_history=history
       )
       
       if json_objects:
           apply_changes(json_objects, user_token)
           return jsonify({
               'success': True, 
               'response': explanation if explanation else response,
               'program': get_sorted_sessions(user_token=user_token),
               'changes_made': True
           })
       
       return jsonify({
           'success': True,
           'response': response,
           'changes_made': False
       })
       
   except Exception as e:
       return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get-program', methods=['GET'])
@login_required
def get_program():
    """Récupération du programme"""
    try:
        return jsonify({
            'success': True,
            'profile': get_profile(),
            'program': get_sorted_sessions()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/calendar/<user_token>/calendar.ics')
def get_calendar(user_token):
    """Génération du calendrier ICS pour un utilisateur spécifique"""
    try:
        jwt = session.get('user_token')
        verified_user_token = auth_manager.get_user_token_from_jwt(jwt)
        
        if verified_user_token != user_token:
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
            
        calendar_manager = CalendarManager()
        ics_content = calendar_manager.generate_ics(user_token)
        
        response = Response(ics_content)
        response.headers.update({
            'Content-Type': 'text/calendar; charset=utf-8',
            'Content-Disposition': f'inline; filename=running_program_{user_token}.ics',
            'Cache-Control': 'public, max-age=3600'
        })
        
        return response
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/calendar-url')
@login_required
def get_calendar_url():
    """URLs du calendrier pour l'utilisateur connecté"""
    try:
        jwt = session.get('user_token')
        user_token = auth_manager.get_user_token_from_jwt(jwt)
        
        base_url = request.url_root.rstrip('/')
        calendar_manager = CalendarManager()
        feed_url = calendar_manager.generate_ics_feed_url(base_url, user_token)
        
        return jsonify({
            'success': True,
            'urls': {
                'ics_feed': feed_url,
                'google_calendar': f"https://www.google.com/calendar/render?cid={urllib.parse.quote(feed_url)}",
                'ical': f"webcal://{urllib.parse.urlparse(feed_url).netloc}/calendar/{user_token}/calendar.ics"
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/chat-suggestions', methods=['POST'])
@login_required
def get_chat_suggestions():
    """Suggestions pour le chat"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Format de requête invalide'}), 400

        data = request.get_json()
        message = data.get('message')
        history = data.get('history', [])
        
        if not message:
            return jsonify({'success': False, 'error': 'Message manquant'}), 400
            
        suggestions = process_suggestions_request(
            message, 
            context_program=get_sorted_sessions(),
            message_history=history
        )
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/user-token', methods=['GET'])
@login_required
def get_user_token():
    """Returns the user token for the authenticated user"""
    try:
        jwt = session.get('user_token')
        user_token = auth_manager.get_user_token_from_jwt(jwt)
        return jsonify({
            'success': True,
            'user_token': user_token
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/auth-token', methods=['GET'])
@login_required
def get_auth_token():
    """Returns the JWT auth token for API requests"""
    try:
        jwt = session.get('user_token')
        return jsonify({
            'success': True,
            'auth_token': jwt
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# === Routes de l'API ===

# API key management
@app.route('/api/generate-key', methods=['POST'])
def api_generate_api_key():
    return jsonify({'success': True, 'api_key': key_static})

# Program routes
@app.route('/api/init-program', methods=['GET'])
def api_init_program():
    return jsonify(initialize_or_load_program(key_static))

@app.route('/api/chat', methods=['GET'])
def api_chat():
    # Récupérer les paramètres de l'URL
    message = request.args.get('message')
    history = request.args.getlist('history')  # Pour gérer plusieurs valeurs
    
    if not message:
        return jsonify({'success': False, 'error': 'Missing message'}), 400
        
    json_objects, explanation, response = process_llm_request(
        message, 
        context_program=get_sorted_sessions(key_static),
        message_history=history
    )
    
    if json_objects:
        apply_changes(json_objects, key_static)
        return jsonify({
            'success': True, 
            'response': explanation if explanation else response,
            'program': get_sorted_sessions(key_static),
            'changes_made': True
        })
    
    return jsonify({
        'success': True,
        'response': response,
        'changes_made': False
    })


@app.route('/api/program', methods=['GET'])
def api_get_program():
    return jsonify({
        'success': True,
        'profile': get_profile(key_static),
        'program': get_sorted_sessions(key_static)
    })

@app.route('/api/calendar/<user_id>/calendar.ics')
def api_get_calendar(user_id):
    try:
        calendar_manager = CalendarManager()
        ics_content = calendar_manager.generate_ics(user_id, key_static)
        
        response = Response(ics_content)
        response.headers.update({
            'Content-Type': 'text/calendar; charset=utf-8',
            'Content-Disposition': f'inline; filename=running_program_{user_id}.ics',
            'Cache-Control': 'public, max-age=3600'
        })
        return response
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calendar-url/<user_id>')
def api_get_calendar_url(user_id):
    try:
        base_url = request.url_root.rstrip('/')
        calendar_manager = CalendarManager()
        feed_url = calendar_manager.generate_ics_feed_url(base_url, user_id)
        
        return jsonify({
            'success': True,
            'urls': {
                'ics_feed': feed_url,
                'google_calendar': f"https://www.google.com/calendar/render?cid={urllib.parse.quote(feed_url)}",
                'ical': f"webcal://{urllib.parse.urlparse(feed_url).netloc}/api/calendar/{user_id}/calendar.ics"
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat-suggestions', methods=['POST'])
def api_get_chat_suggestions():
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Invalid request format'}), 400

    data = request.get_json()
    message = data.get('message')
    history = data.get('history', [])
    
    if not message:
        return jsonify({'success': False, 'error': 'Missing message'}), 400
        
    suggestions = process_suggestions_request(
        message, 
        context_program=get_sorted_sessions(key_static),
        message_history=history
    )
    
    return jsonify({
        'success': True,
        'suggestions': suggestions
    })

# === Demo simulation ===

# Initialisation du simulateur
simulator = ActivitySimulator("data/mams_semi_boulogne.csv")
simulator.start_simulation()

@app.route('/api/activity/data', methods=['GET'])
def get_activity_data():
    """
    Endpoint pour obtenir les données de l'activité jusqu'au temps actuel
    
    Returns:
        JSON {
            "timestamp": List[str],
            "pace_min_per_km": List[float],
            "elevation_meters": List[float],
            "heart_rate_bpm": List[int]
        }
    """
    data = simulator.get_simulation_data()
    if data is None:
        return jsonify({
            "error": "Simulation not running or no data available"
        }), 404
    return jsonify(data)

@app.route('/api/activity/reset', methods=['GET'])
def reset_simulation():
    """Endpoint pour réinitialiser la simulation"""
    simulator.reset()
    return jsonify({"message": "Simulation reset successfully"})

@app.route('/api/activity/status', methods=['GET'])
def get_status():
    """
    Endpoint pour obtenir le statut de la simulation et les métadonnées
    """
    data = simulator.get_simulation_data()
    if data is None:
        return jsonify({
            "status": "no_data",
            "total_points": 0,
            "current_points": 0
        })
    
    return jsonify({
        "status": "running",
        "total_points": len(simulator.df_full),
        "current_points": len(data['timestamp']),
        "progress_percent": round(len(data['timestamp']) / len(simulator.df_full) * 100, 1)
    })

@app.route('/api/activity/add_time/<int:minutes>', methods=['GET'])
def add_time(minutes: int):
    """
    Endpoint pour faire progresser la simulation de X minutes
    
    Args:
        minutes (int): Nombre de minutes à ajouter
    
    Returns:
        JSON {
            "message": str
        }
    """
    if minutes <= 0:
        return jsonify({'error': 'Minutes must be positive'}), 400

    simulator.force_progress(minutes)
    return jsonify({"message": f"Simulation progressed by {minutes} minutes"})

@app.route('/api/activity/distance', methods=['GET'])
def get_distance():
    """
    Endpoint pour obtenir la distance totale parcourue
    
    Returns:
        JSON {
            "distance_km": float
        }
    """
    distance = simulator.get_current_distance()
    if distance is None:
        return jsonify({"error": "Simulation not running or no data available"}), 404
    return jsonify({"distance_km": distance})

@app.route('/api/activity/pace', methods=['GET'])
def get_pace():
    """
    Endpoint pour obtenir l'allure actuelle
    
    Returns:
        JSON {
            "pace_min_per_km": float
        }
    """
    pace = simulator.get_current_pace()
    if pace is None:
        return jsonify({"error": "Simulation not running or no data available"}), 404
    return jsonify({"pace_min_per_km": pace})

@app.route('/api/activity/time', methods=['GET'])
def get_time():
    """
    Endpoint pour obtenir le temps actuel de la simulation
    
    Returns:
        JSON {
            "time": str
        }
    """
    time = simulator.get_current_time()
    if time is None:
        return jsonify({"error": "Simulation not running or no data available"}), 404
    return jsonify({"time": time})

# === Web socket ===

class DistanceStreamer:
    def __init__(self, simulator):
        self.simulator = simulator
        self._stop_event = Event()
        
    def stream_distance(self, ws):
        """Envoie la distance en continu via WebSocket"""
        while not self._stop_event.is_set():
            try:
                distance = self.simulator.get_current_distance()
                if distance is not None:
                    # Format spécifique pour FlutterFlow
                    message = {
                        "data": {
                            "distance_km": distance
                        },
                        "type": "data",  # Type requis par FlutterFlow
                        "timestamp": int(time.time() * 1000)  # Timestamp en millisecondes
                    }
                    ws.send(json.dumps(message))
                time.sleep(2)  # Pause de 2 secondes entre chaque envoi
            except Exception as e:
                error_message = {
                    "type": "error",
                    "data": {"message": str(e)},
                    "timestamp": int(time.time() * 1000)
                }
                ws.send(json.dumps(error_message))
                break
                
    def stop(self):
        """Arrête le streaming"""
        self._stop_event.set()

@sock.route('/ws/distance')
def distance_sock(ws):
    """
    WebSocket endpoint pour le streaming de la distance
    Compatible avec FlutterFlow
    """
    streamer = DistanceStreamer(simulator)
    
    try:
        # Envoie un message initial de connexion
        connect_message = {
            "type": "connection",
            "data": {"status": "connected"},
            "timestamp": int(time.time() * 1000)
        }
        ws.send(json.dumps(connect_message))
        
        # Démarre le streaming
        streamer.stream_distance(ws)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        streamer.stop()


# === Routes statiques ===

@app.route('/favicon.ico')
def favicon():
    """Route pour le favicon"""
    return app.send_static_file('favicon.ico')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Route pour les fichiers statiques"""
    return send_from_directory(app.static_folder, filename)

# === Configuration de sécurité ===

@app.after_request
def add_security_headers(response):
    """Ajout des headers de sécurité"""
    response.headers.update({
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; "
                                 "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.tailwindcss.com; "
                                 "font-src 'self' https://cdnjs.cloudflare.com; "
                                 "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com"
    })
    return response


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=18091)