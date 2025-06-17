import datetime
from googleapiclient.discovery import build
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from dotenv import load_dotenv

from pdf_parser import extract_text_from_pdf, parse_schedule

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_event(service, course):
    days_mapping = {"Mo": "MO", "Tu": "TU", "We": "WE", "Th": "TH", "Fr": "FR", "Sa": "SA", "Su": "SU"}
    days = ','.join([days_mapping.get(day, '') for day in course['Days'].split() if day in days_mapping])
    if not days:
        raise ValueError(f"No valid days found for course: {course['Course']} with Days: {course['Days']}")
    recurrence_rule = [
        f"RRULE:FREQ=WEEKLY;BYDAY={days};UNTIL={convert_to_google_date(course['EndDate'], course['Section'][:3])}"
    ]
    building_room = course['Location'].split()[-2:]
    building = building_room[0]
    room = building_room[1]
    semester = course['Section'][:3]
    start_datetime = convert_to_datetime(course['StartDate'], course['Start'], semester, course['Days'])
    end_datetime = convert_to_datetime(course['StartDate'], course['End'], semester, course['Days'])
    summary = f"{course['Course']} - B{building} R{room}"
    location = "Vancouver Island University, 900 Fifth St, Nanaimo, BC V9R 5S5, Canada"
    event = {
        'summary': summary,
        'location': location,
        'description': f"Instructor: {course['Instructor']}, Status: {course['Status']}, DeliveryMode: {course['DeliveryMode']}",
        'start': {'dateTime': start_datetime.isoformat(), 'timeZone': 'America/Vancouver'},
        'end': {'dateTime': end_datetime.isoformat(), 'timeZone': 'America/Vancouver'},
        'recurrence': recurrence_rule,
    }
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    print(f'Event created: {created_event.get("htmlLink")}')
    return created_event



def convert_to_datetime(date_str, time_str, semester, days):
    # Extract year from semester (e.g., F24 -> 2024)
    year = int('20' + semester[1:3])
    start_date = datetime.datetime.strptime(f"{date_str} {year}", '%d-%b %Y')
    
    # Find the first available day of the week that the course runs on
    days_mapping = {"Mo": 0, "Tu": 1, "We": 2, "Th": 3, "Fr": 4, "Sa": 5, "Su": 6}
    course_days = [days_mapping[day] for day in days.split()]
    while start_date.weekday() not in course_days:
        start_date += datetime.timedelta(days=1)
    
    start_datetime = datetime.datetime.combine(start_date, datetime.datetime.strptime(time_str, '%H:%M').time())
    return start_datetime

def convert_to_google_date(date_str, semester):
    # Extract year from semester (e.g., F24 -> 2024)
    year = int('20' + semester[1:3])
    dt = datetime.datetime.strptime(date_str, '%d-%b').replace(year=year)
    return dt.strftime('%Y%m%dT000000Z')

def authenticate_google_calendar_cli():
    """Authenticate and return the Google Calendar service for CLI usage."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                SCOPES
            )
            creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)

def get_google_auth_url():
    """Get the Google OAuth URL for web authentication."""
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri='http://localhost:5000/oauth2callback'
    )
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    return auth_url, state, flow

def handle_google_callback(auth_response, flow):
    """Handle the OAuth callback and return the service."""
    flow.fetch_token(authorization_response=auth_response)
    creds = flow.credentials
    
    # Save credentials for future use
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)