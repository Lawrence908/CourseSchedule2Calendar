from typing import Dict, Any, Tuple
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from .base import CalendarProvider
import logging
import os
import dotenv

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

class GoogleCalendarProvider(CalendarProvider):
    """Google Calendar provider implementation."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def get_auth_url(self) -> Tuple[str, str, Any]:
        """Get the Google OAuth URL."""
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'https://schedshare.chrislawrence.ca/oauth2callback')
        if redirect_uri.startswith('http://'):
            # Force HTTPS if not already
            redirect_uri = redirect_uri.replace('http://', 'https://', 1)
        print(f"[GoogleCalendarProvider] Using redirect_uri for auth: {redirect_uri}")
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=self.SCOPES,
            redirect_uri=redirect_uri
        )
        print(f"[GoogleCalendarProvider] Flow redirect_uri: {flow.redirect_uri}")
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        return auth_url, state, flow
    
    def handle_callback(self, auth_response: str, flow: Any) -> Any:
        """Handle the OAuth callback and return the service."""
        print(f"[GoogleCalendarProvider] handle_callback flow.redirect_uri: {flow.redirect_uri}")
        flow.fetch_token(authorization_response=auth_response)
        return build('calendar', 'v3', credentials=flow.credentials)
    
    def create_event(self, service: Any, course: Dict[str, Any]) -> Dict[str, Any]:
        """Create an event in Google Calendar."""
        # Build the Google event dict from the course dict
        event = self.build_google_event(course)
        logger.info("Google event data: %r", event)
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        return created_event
    
    def build_google_event(self, course):
        # (Copy your event-building logic from your old google_calendar.py)
        # Example:
        days_mapping = {"Mo": "MO", "Tu": "TU", "We": "WE", "Th": "TH", "Fr": "FR", "Sa": "SA", "Su": "SU"}
        days = ','.join([days_mapping.get(day, '') for day in course['Days'].split() if day in days_mapping])
        recurrence_rule = [
            f"RRULE:FREQ=WEEKLY;BYDAY={days};UNTIL={self.convert_to_google_date(course['EndDate'], course['Section'][:3])}"
        ]
        building_room = course['Location'].split()[-2:]
        building = building_room[0]
        room = building_room[1]
        semester = course['Section'][:3]
        start_datetime = self.convert_to_datetime(course['StartDate'], course['Start'], semester, course['Days'])
        end_datetime = self.convert_to_datetime(course['StartDate'], course['End'], semester, course['Days'])
        summary = f"{course['Course']} - B{building} R{room}"
        location = course['Location']
        event = {
            'summary': summary,
            'location': location,
            'description': f"Instructor: {course['Instructor']}, Status: {course['Status']}, DeliveryMode: {course['DeliveryMode']}",
            'start': {'dateTime': start_datetime.isoformat(), 'timeZone': 'America/Vancouver'},
            'end': {'dateTime': end_datetime.isoformat(), 'timeZone': 'America/Vancouver'},
            'recurrence': recurrence_rule,
        }
        return event
    
    def get_provider_name(self) -> str:
        return "Google Calendar"
    
    def get_provider_icon(self) -> str:
        return "/static/google-calendar.png"

    def get_provider_key(self) -> str:
        return "google"

    def convert_to_datetime(self, date_str: str, time_str: str, semester: str, days: str):
        """Convert PDF date & time strings into a Python datetime (first matching course day)."""
        import datetime
        # Extract year from semester code (e.g. 'F24' -> 2024)
        year = int('20' + semester[1:3])
        start_date = datetime.datetime.strptime(f"{date_str} {year}", '%d-%b %Y')

        # Advance to first day that the class actually runs on
        days_mapping = {"Mo": 0, "Tu": 1, "We": 2, "Th": 3, "Fr": 4, "Sa": 5, "Su": 6}
        course_days = [days_mapping[d] for d in days.split() if d in days_mapping]
        while start_date.weekday() not in course_days:
            start_date += datetime.timedelta(days=1)

        start_datetime = datetime.datetime.combine(
            start_date, datetime.datetime.strptime(time_str, '%H:%M').time()
        )
        return start_datetime

    def convert_to_google_date(self, date_str: str, semester: str) -> str:
        """Return a YYYYMMDDT000000Z string for Google RRULE UNTIL value."""
        import datetime
        year = int('20' + semester[1:3])
        dt = datetime.datetime.strptime(date_str, '%d-%b').replace(year=year)
        return dt.strftime('%Y%m%dT000000Z') 