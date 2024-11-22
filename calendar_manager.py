from icalendar import Calendar, Event, vText
from datetime import datetime, timedelta
from uuid import uuid4
import pytz
from session_manager import get_sorted_sessions
import os


class CalendarManager:
    def __init__(self):
        self.timezone = pytz.timezone('Europe/Paris')
        self.calendar_dir = 'calendar'
        os.makedirs(self.calendar_dir, exist_ok=True)

    def get_calendar_path(self, user_token):
        """Get the calendar file path for a specific user"""
        return os.path.join(self.calendar_dir, f'calendar_{user_token}.ics')

    def _create_calendar(self):
        """Create a new calendar object with basic properties"""
        cal = Calendar()
        cal.add('prodid', '-//Running Training Program//FR')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', 'Programme Entrainement Course')
        cal.add('x-wr-timezone', 'Europe/Paris')
        return cal

    def _create_event(self, session):
        """Create an iCalendar event from a training session"""
        event = Event()
        
        start_time = datetime.strptime(session['date'], "%Y-%m-%d %H:%M")
        start_time = self.timezone.localize(start_time)
        
        pace_multiplier = 6
        if 'tempo' in session['type_de_seance'].lower():
            pace_multiplier = 5
        elif 'intervalle' in session['type_de_seance'].lower():
            pace_multiplier = 5.5
            
        duration_minutes = int(session['distance'] * pace_multiplier)
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        event.add('summary', f"{session['type_de_seance']} - {session['distance']}km")
        event.add('dtstart', start_time)
        event.add('dtend', end_time)
        event.add('dtstamp', datetime.now(self.timezone))
        event.add('uid', str(uuid4()))
        
        description = (
            f"Type: {session['type_de_seance']}\n"
            f"Distance: {session['distance']}km\n"
            f"Description: {session['description']}"
        )
        event.add('description', description)
        event.add('location', vText('Extérieur'))
        event.add('categories', 'Running,Training')
        event.add('status', 'CONFIRMED')
        
        return event

    def generate_ics(self, user_token):
        """Generate an ICS file content for a specific user"""
        cal = self._create_calendar()
        sessions = get_sorted_sessions(user_token)
        
        for session in sessions:
            event = self._create_event(session)
            cal.add_component(event)
            
        # Save to user-specific file
        calendar_path = self.get_calendar_path(user_token)
        with open(calendar_path, 'wb') as f:
            f.write(cal.to_ical())
            
        return cal.to_ical()

    def get_calendar_content(self, user_token):
        """Get the calendar content for a specific user"""
        calendar_path = self.get_calendar_path(user_token)
        if os.path.exists(calendar_path):
            with open(calendar_path, 'rb') as f:
                return f.read()
        return None

    def generate_ics_feed_url(self, base_url, user_token):
        """Generate the URL for the user's ICS feed"""
        return f"{base_url}/calendar/{user_token}/calendar.ics"

    def delete_calendar(self, user_token):
        """Delete a user's calendar file"""
        calendar_path = self.get_calendar_path(user_token)
        if os.path.exists(calendar_path):
            os.remove(calendar_path)