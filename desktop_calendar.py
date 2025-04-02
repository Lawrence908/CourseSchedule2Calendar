import os
import pickle
import datetime
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pdf_parser import extract_text_from_pdf, parse_schedule

# Google API scope for Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_calendar():
    """Authenticate and return the Google Calendar service."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use InstalledAppFlow to handle desktop authentication
            flow = InstalledAppFlow.from_client_secrets_file('client_secret_165503894384-m368d8ts9aod6kpgrps2l4j2klk1veie.apps.googleusercontent.com.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('calendar', 'v3', credentials=creds)

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

def create_event(service, course):
    # Map days to Google Calendar format
    days_mapping = {"Mo": "MO", "Tu": "TU", "We": "WE", "Th": "TH", "Fr": "FR", "Sa": "SA", "Su": "SU"}

    # Debugging Days
    print(f"Processing Days: {course['Days']}")
    
    # Validate and map days
    days = ','.join([days_mapping.get(day, '') for day in course['Days'].split() if day in days_mapping])
    if not days:
        raise ValueError(f"No valid days found for course: {course['Course']} with Days: {course['Days']}")
    
    recurrence_rule = [
        f"RRULE:FREQ=WEEKLY;BYDAY={days};UNTIL={convert_to_google_date(course['EndDate'], course['Section'][:3])}"
    ]

    # Extract building and room
    building_room = course['Location'].split()[-2:]
    building = building_room[0]
    room = building_room[1]
    semester = course['Section'][:3]
    section = course['Section'][3:]

    # Convert dates and times
    start_datetime = convert_to_datetime(course['StartDate'], course['Start'], semester, course['Days'])
    end_datetime = convert_to_datetime(course['StartDate'], course['End'], semester, course['Days'])

    # Event summary and location
    summary = f"{course['Course']} - B{building} R{room} - {section}"
    location = "Vancouver Island University, 900 Fifth St, Nanaimo, BC V9R 5S5, Canada" if course['Location'].startswith("Nanaimo") else course['Location']

    # Build event dictionary
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

    # Insert the event into Google Calendar
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    print(f'Event created: {created_event.get("htmlLink")}')
    
    return created_event


def main():
    service = authenticate_google_calendar()
    pdf_file = input("Enter the path to your course schedule PDF: ").strip()
    if not os.path.exists(pdf_file):
        print("Error: File not found.")
        return
    text = extract_text_from_pdf(pdf_file)
    courses = parse_schedule(text)
    if not courses:
        print("No courses found in the PDF.")
        return
    print("Courses found in the PDF:")
    for course in courses:
        print(f"- {course['Course']} on {course['Days']} at {course['Start']} - {course['End']}")
    confirm = input("Do you want to add these courses to your Google Calendar? (yes/no): ").strip().lower()
    if confirm == "yes":
        for course in courses:
            try:
                create_event(service, course)
            except Exception as e:
                print(f"Error adding course {course['Course']} on {course['Days']}: {e}")
        print("All events have been added to your Google Calendar!")



if __name__ == '__main__':
    main()
