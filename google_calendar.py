import datetime
from googleapiclient.discovery import build
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import tkinter as tk
from tkinter import messagebox

SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_event(service, course):
    # Create recurrence rule based on days and end date
    days_mapping = {"Mo": "MO", "Tu": "TU", "We": "WE", "Th": "TH", "Fr": "FR", "Sa": "SA", "Su": "SU"}
    days = ','.join([days_mapping[day] for day in course['Days'].split()])
    
    recurrence_rule = [
        f"RRULE:FREQ=WEEKLY;BYDAY={days};UNTIL={convert_to_google_date(course['EndDate'], course['Section'][:3])}"
    ]

    # Update summary
    building_room = course['Location'].split()[-2:]
    building = building_room[0]
    room = building_room[1]
    semester = course['Section'][:3]
    section = course['Section'][3:]

    # Convert date and time to datetime objects
    start_datetime = convert_to_datetime(course['StartDate'], course['Start'], semester, course['Days'])
    end_datetime = convert_to_datetime(course['StartDate'], course['End'], semester, course['Days'])
    recurrence_until = convert_to_google_date(course['EndDate'], semester)

    # Update summary
    summary = f"{course['Course']} - B{building} R{room} - {section}"

    # Update location
    if course['Location'].startswith("Nanaimo"):
        location = "Vancouver Island University, 900 Fifth St, Nanaimo, BC V9R 5S5, Canada"
    elif course['Location'].startswith("Duncan"):
        location = "Vancouver Island University, Cowichan Campus, 2011 University Way, North Cowichan, BC V9L 0C7, Canada"
    else:
        location = course['Location']  # Fallback to the original location if not Nanaimo or Duncan

    event = {
        'summary': summary,
        'location': location,
        'description': f"Instructor: {course['Instructor']}, Status: {course['Status']}, DeliveryMode: {course['DeliveryMode']}",
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

def authenticate_google_calendar():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

            if not client_id or not client_secret:
                raise ValueError("Environment variables GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set.")

            credentials = {
                "installed": {
                    "client_id": client_id,
                    "project_id": "courseschedule2calendar",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": client_secret,
                    "redirect_uris": ["http://localhost"]
                }
            }

            flow = InstalledAppFlow.from_client_config(credentials, SCOPES)
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f'Please visit this URL to authorize this application: {auth_url}')
            code = input('Enter the authorization code: ')
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

def show_schedule_gui(courses):
    root = tk.Tk()
    root.title("Course Schedule")

    for course in courses:
        course_info = f"{course['Course']} - {course['Days']} {course['Start']} - {course['End']}"
        label = tk.Label(root, text=course_info)
        label.pack()

    def on_confirm():
        if messagebox.askyesno("Confirm", "Do you want to create these events in Google Calendar?"):
            root.destroy()
            service = authenticate_google_calendar()
            for course in courses:
                create_event(service, course)
            messagebox.showinfo("Success", "Events created successfully!")

    confirm_button = tk.Button(root, text="Confirm", command=on_confirm)
    confirm_button.pack()

    root.mainloop()

if __name__ == "__main__":
    # Example courses data
    courses = [
        {'Course': 'CSCI 360', 'Section': 'F24N02', 'Location': 'Nanaimo 200 106', 'Days': 'Mo We', 'Start': '13:00', 'End': '14:30', 'StartDate': '03-SEP', 'EndDate': '06-DEC', 'Status': 'Enrolled', 'Instructor': 'KABIR HUMAYUN', 'DeliveryMode': 'Face-to-Face'},
        {'Course': 'CSCI 478', 'Section': 'F24N02', 'Location': 'Nanaimo 210 225', 'Days': 'Tu Th', 'Start': '10:00', 'End': '11:30', 'StartDate': '03-SEP', 'EndDate': '06-DEC', 'Status': 'Enrolled', 'Instructor': 'MENESES LUIS', 'DeliveryMode': 'Face-to-Face'}
    ]

    show_schedule_gui(courses)