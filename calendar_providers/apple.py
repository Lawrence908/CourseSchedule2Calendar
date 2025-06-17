from typing import Dict, Any, Tuple
import jwt
import time
import requests
from .base import CalendarProvider
import logging
import os
from datetime import datetime, timedelta

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
    
    def _generate_client_secret(self) -> str:
        """Generate a JWT client secret for Apple OAuth."""
        try:
            with open(self.private_key_path, 'r') as key_file:
                private_key = key_file.read()
            
            # JWT header
            headers = {
                'kid': self.key_id,
                'alg': 'ES256'
            }
            
            # JWT payload
            payload = {
                'iss': self.team_id,
                'iat': int(time.time()),
                'exp': int(time.time()) + 15777000,  # 6 months
                'aud': 'https://appleid.apple.com',
                'sub': self.client_id
            }
            
            # Sign the JWT
            client_secret = jwt.encode(
                payload,
                private_key,
                algorithm='ES256',
                headers=headers
            )
            
            return client_secret
        except Exception as e:
            logger.error(f"Error generating Apple client secret: {str(e)}")
            raise
    
    def get_auth_url(self) -> Tuple[str, str, Any]:
        """Get the Apple OAuth URL."""
        try:
            # Generate state for CSRF protection
            state = os.urandom(16).hex()
            
            # Construct authorization URL
            auth_url = (
                'https://appleid.apple.com/auth/authorize'
                f'?client_id={self.client_id}'
                f'&redirect_uri={self.redirect_uri}'
                '&response_type=code'
                f'&scope={" ".join(self.SCOPES)}'
                '&response_mode=form_post'
                f'&state={state}'
            )
            
            # Store state in Redis (handled by app.py)
            return auth_url, state, None
        except Exception as e:
            logger.error(f"Error generating Apple auth URL: {str(e)}")
            raise
    
    def handle_callback(self, auth_response: str, flow: Any) -> Any:
        """Handle the OAuth callback and return the service."""
        try:
            # Extract code from form data
            code = auth_response.split('code=')[1].split('&')[0]
            
            # Generate client secret
            client_secret = self._generate_client_secret()
            
            # Exchange code for tokens
            token_url = 'https://appleid.apple.com/auth/token'
            token_data = {
                'client_id': self.client_id,
                'client_secret': client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri
            }
            
            response = requests.post(token_url, data=token_data)
            response.raise_for_status()
            tokens = response.json()
            
            # Store tokens in Redis (handled by app.py)
            return {
                'access_token': tokens.get('access_token'),
                'refresh_token': tokens.get('refresh_token'),
                'id_token': tokens.get('id_token')
            }
        except Exception as e:
            logger.error(f"Error handling Apple callback: {str(e)}")
            raise
    
    def create_event(self, service: Any, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an event in Apple Calendar."""
        try:
            # Since Apple doesn't provide a direct Calendar API,
            # we'll generate an ICS file for the user to import
            from ics import Calendar, Event
            
            cal = Calendar()
            event = Event()
            
            # Set event details
            event.name = f"{event_data['Course']} - {event_data['Section']}"
            event.begin = self._convert_to_datetime(event_data['StartDate'], event_data['Start'], event_data['Section'][:3])
            event.end = self._convert_to_datetime(event_data['StartDate'], event_data['End'], event_data['Section'][:3])
            event.location = event_data['Location']
            event.description = (
                f"Instructor: {event_data['Instructor']}\n"
                f"Status: {event_data['Status']}\n"
                f"Delivery Mode: {event_data['DeliveryMode']}"
            )
            
            # Add recurrence rule
            days_mapping = {"Mo": "MO", "Tu": "TU", "We": "WE", "Th": "TH", "Fr": "FR", "Sa": "SA", "Su": "SU"}
            days = ','.join([days_mapping.get(day, '') for day in event_data['Days'].split() if day in days_mapping])
            until_date = self._convert_to_google_date(event_data['EndDate'], event_data['Section'][:3])
            event.rrule = f"FREQ=WEEKLY;BYDAY={days};UNTIL={until_date}"
            
            cal.events.add(event)
            
            # Return the ICS data
            return {
                'ics_data': str(cal),
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