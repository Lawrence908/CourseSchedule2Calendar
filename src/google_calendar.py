import datetime
from googleapiclient.discovery import build

def create_event(service, course):
    start_datetime = convert_to_datetime(course['start_date'], course['start_time'])
    end_datetime = convert_to_datetime(course['start_date'], course['end_time'])
    
    # Create recurrence rule based on days and end date
    days_mapping = {"Mo": "MO", "Tu": "TU", "We": "WE", "Th": "TH", "Fr": "FR", "Sa": "SA", "Su": "SU"}
    days = ','.join([days_mapping[day] for day in course['days']])
    
    recurrence_rule = [
        f"RRULE:FREQ=WEEKLY;BYDAY={days};UNTIL={convert_to_google_date(course['end_date'])}"
    ]

    event = {
        'summary': course['title'],
        'location': course['location'],
        'description': course['description'],
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': 'America/Vancouver',
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': 'America/Vancouver',
        },
        'recurrence': recurrence_rule,
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f'Event created: {event.get("htmlLink")}')

def convert_to_datetime(date_str, time_str):
    # Assuming date format is MM/DD/YYYY
    return datetime.datetime.strptime(f"{date_str} {time_str}", '%m/%d/%Y %H:%M')

def convert_to_google_date(date_str):
    # Converts date to the format YYYYMMDD for the RRULE UNTIL
    dt = datetime.datetime.strptime(date_str, '%m/%d/%Y')
    return dt.strftime('%Y%m%dT000000Z')



import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_calendar():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service
