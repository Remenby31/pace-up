from icalendar import Calendar, Event, vText
from datetime import datetime, timedelta
from uuid import uuid4
import pytz
from session_manager import get_sorted_sessions

class CalendarManager:
    def __init__(self):
        self.timezone = pytz.timezone('Europe/Paris')

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
        
        # Parse the session date and create start/end times
        start_time = datetime.strptime(session['date'], "%Y-%m-%d %H:%M")
        start_time = self.timezone.localize(start_time)
        
        # Estimate duration based on distance and type
        # Assuming average pace of 6min/km for easy runs, 5min/km for tempo
        pace_multiplier = 6
        if 'tempo' in session['type_de_seance'].lower():
            pace_multiplier = 5
        elif 'intervalle' in session['type_de_seance'].lower():
            pace_multiplier = 5.5
            
        duration_minutes = int(session['distance'] * pace_multiplier)
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Create unique identifier
        uid = str(uuid4())
        
        # Set event properties
        event.add('summary', f"{session['type_de_seance']} - {session['distance']}km")
        event.add('dtstart', start_time)
        event.add('dtend', end_time)
        event.add('dtstamp', datetime.now(self.timezone))
        event.add('uid', uid)
        
        # Add detailed description
        description = (
            f"Type: {session['type_de_seance']}\n"
            f"Distance: {session['distance']}km\n"
            f"Description: {session['description']}"
        )
        event.add('description', description)
        
        # Add location if specified (could be enhanced in the future)
        event.add('location', vText('Extérieur'))
        
        # Add other metadata
        event.add('categories', 'Running,Training')
        event.add('status', 'CONFIRMED')
        
        return event

    def generate_ics(self):
        """Generate an ICS file content from all training sessions"""
        cal = self._create_calendar()
        
        # Get all sessions and sort them
        sessions = get_sorted_sessions()
        
        # Add each session as an event
        for session in sessions:
            event = self._create_event(session)
            cal.add_component(event)
            
        return cal.to_ical()

    def generate_ics_feed_url(self, base_url):
        """Generate the URL for the ICS feed"""
        return f"{base_url}/calendar.ics"