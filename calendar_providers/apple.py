from typing import Dict, Any, Tuple
import jwt
import time
import requests
from .base import CalendarProvider
import logging
import os
from datetime import datetime, timedelta
from ics import Calendar, Event, Organizer, Geo
import re

logger = logging.getLogger(__name__)

class AppleCalendarProvider(CalendarProvider):
    """Apple Calendar provider implementation."""
    
    SCOPES = ['name', 'email']  # Apple Sign In scopes
    
    def __init__(self):
        self.client_id = os.getenv('APPLE_CLIENT_ID')
        self.team_id = os.getenv('APPLE_TEAM_ID')
        self.key_id = os.getenv('APPLE_KEY_ID')
        self.private_key_path = os.getenv('APPLE_PRIVATE_KEY_PATH')
        self.redirect_uri = os.getenv('APPLE_REDIRECT_URI', 'http://localhost:5000/oauth2callback')
        
        if not all([self.client_id, self.team_id, self.key_id, self.private_key_path]):
            logger.warning("Missing required Apple OAuth configuration")
    
    def get_auth_url(self) -> Tuple[str, str, Any]:
        """Get the Apple OAuth URL."""
        # Since we're not using Apple OAuth anymore, we'll just return a dummy URL
        # that will redirect to the event selection page
        return "http://localhost:5000/events", "dummy_state", None
    
    def handle_callback(self, auth_response: str, flow: Any) -> Any:
        """Handle the OAuth callback and return the service."""
        # Since we're not using Apple OAuth anymore, we'll just return None
        return None
    
    def create_event(self, service: Any, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an event in Apple Calendar."""
        try:
            # Since Apple doesn't provide a direct Calendar API,
            # we'll generate an ICS file for the user to import
            from ics import Calendar, Event
            
            cal = Calendar()
            event = Event()
            
            # Extract building and room information
            building_room = event_data['Location'].split()[-2:]
            building = building_room[0]
            room = building_room[1]
            
            # Set event details
            event.name = f"{event_data['Course']} - {event_data['Section']}"
            event.begin = self._convert_to_datetime(event_data['StartDate'], event_data['Start'], event_data['Section'][:3])
            event.end = self._convert_to_datetime(event_data['StartDate'], event_data['End'], event_data['Section'][:3])
            
            # Set location with full address
            location = "Vancouver Island University, 900 Fifth St, Nanaimo, BC V9R 5S5, Canada"
            event.location = f"{location} - Building {building}, Room {room}"
            
            # Add detailed description
            description = (
                f"Course: {event_data['Course']}\n"
                f"Section: {event_data['Section']}\n"
                f"Instructor: {event_data['Instructor']}\n"
                f"Status: {event_data['Status']}\n"
                f"Delivery Mode: {event_data['DeliveryMode']}\n"
                f"Building: {building}\n"
                f"Room: {room}\n"
                f"Days: {event_data['Days']}\n"
                f"Time: {event_data['Start']} - {event_data['End']}"
            )
            event.description = description
            
            # Add recurrence rule
            days_mapping = {"Mo": "MO", "Tu": "TU", "We": "WE", "Th": "TH", "Fr": "FR", "Sa": "SA", "Su": "SU"}
            days = ','.join([days_mapping.get(day, '') for day in event_data['Days'].split() if day in days_mapping])
            until_date = self._convert_to_google_date(event_data['EndDate'], event_data['Section'][:3])
            rrule_str = f"FREQ=WEEKLY;BYDAY={days};UNTIL={until_date}"
            event.extra.append(('RRULE', rrule_str))
            
            # Add organizer (university)
            event.organizer = Organizer(
                common_name="Vancouver Island University",
                email="info@viu.ca"
            )
            
            # Add URL to VIU website
            event.url = "https://www.viu.ca"
            
            # Add categories/tags
            event.categories = ["Education", "Course"]
            
            # Add status
            event.status = "CONFIRMED"
            
            # Add classification (public)
            event.classification = "PUBLIC"
            
            # Add priority
            event.priority = 5  # Normal priority
            
            # Add sequence number (for updates)
            event.sequence = 0
            
            # Add transparency (opaque - blocks time)
            event.transparent = False
            
            cal.events.add(event)
            
            # Return the ICS data
            return {
                'ics_data': cal.serialize(),
                'filename': f"{event_data['Course']}_{event_data['Section']}.ics"
            }
        except Exception as e:
            logger.error(f"Error creating Apple Calendar event: {str(e)}")
            raise
    
    def _convert_to_datetime(self, date_str: str, time_str: str, semester: str, days: str = None) -> datetime:
        """Convert date and time strings to datetime object."""
        year = int('20' + semester[1:3])
        dt = datetime.strptime(f"{date_str} {year} {time_str}", '%d-%b %Y %H:%M')
        return dt
    
    def _convert_to_google_date(self, date_str: str, semester: str) -> str:
        """Convert date string to Google Calendar format."""
        year = int('20' + semester[1:3])
        dt = datetime.strptime(date_str, '%d-%b').replace(year=year)
        return dt.strftime('%Y%m%dT000000Z')
    
    def get_provider_name(self) -> str:
        return "Apple Calendar"
    
    def get_provider_icon(self) -> str:
        return "/static/apple-calendar.png"

    def get_provider_key(self) -> str:
        return "apple" 