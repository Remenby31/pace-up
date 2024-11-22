# app.py
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from llm_handler import process_llm_request, process_suggestions_request
from session_manager import apply_changes, get_sorted_sessions, get_profile, initialize_or_load_program
from calendar_manager import CalendarManager
from flask import Response
import urllib.parse

app = Flask(__name__, 
    static_folder='static',  # Dossier pour les fichiers statiques
    template_folder='templates'  # Dossier pour les templates
)
CORS(app)



@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

# Routes pour servir les fichiers statiques
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/init-program', methods=['POST'])
def init_program():
    """Initialize or load the training program"""
    result = initialize_or_load_program()
    return jsonify(result)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        message = request.json.get('message')
        history = request.json.get('history', [])
        
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'})
            
        json_objects, explanation, response = process_llm_request(
            message, 
            context_program=get_sorted_sessions(),
            message_history=history
        )
        
        if json_objects:
            apply_changes(json_objects)
            return jsonify({
                'success': True,
                'response': explanation if explanation else response,
                'program': get_sorted_sessions(),
                'changes_made': True
            })
        
        return jsonify({
            'success': True,
            'response': response,
            'changes_made': False
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get-program', methods=['GET'])
def get_program():
    """Get the current program"""
    try:
        return jsonify({
            'success': True,
            'profile': get_profile(),
            'program': get_sorted_sessions()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/calendar.ics')
def get_calendar():
    """Generate and return the ICS calendar file"""
    try:
        calendar_manager = CalendarManager()
        ics_content = calendar_manager.generate_ics()
        
        response = Response(ics_content)
        response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
        response.headers['Content-Disposition'] = 'inline; filename=running_program.ics'
        # Allow caching for 1 hour
        response.headers['Cache-Control'] = 'public, max-age=3600'
        
        return response
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/calendar-url')
def get_calendar_url():
    """Return the calendar subscription URL"""
    try:
        # Get the base URL of the application
        base_url = request.url_root.rstrip('/')
        calendar_manager = CalendarManager()
        
        # Generate the feed URL
        feed_url = calendar_manager.generate_ics_feed_url(base_url)
        
        # Generate URLs for different calendar services
        google_url = f"https://www.google.com/calendar/render?cid={urllib.parse.quote(feed_url)}"
        ical_url = f"webcal://{urllib.parse.urlparse(feed_url).netloc}/calendar.ics"
        
        return jsonify({
            'success': True,
            'urls': {
                'ics_feed': feed_url,
                'google_calendar': google_url,
                'ical': ical_url
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/chat-suggestions', methods=['POST'])
def get_chat_suggestions():
    """Generate multiple response suggestions for a chat message"""
    try:
        message = request.json.get('message')
        history = request.json.get('history', [])
        
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'})
            
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
        return jsonify({'success': False, 'error': str(e)})

#favicon
@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=18091)