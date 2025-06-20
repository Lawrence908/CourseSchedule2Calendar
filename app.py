# filepath: /home/chris/github/CourseSchedule2Calendar/app.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from flask import Flask, request, redirect, url_for, render_template, flash, session, Response
from werkzeug.utils import secure_filename
import os, secrets
import logging
from pdf_parser import extract_text_from_pdf, parse_schedule
from calendar_providers.google import GoogleCalendarProvider
from calendar_providers.apple import AppleCalendarProvider
import pickle
from dotenv import load_dotenv
from config import logging as logging_config  # Import logging config
from flask_session import Session
import redis
import json
from flask_mail import Mail, Message
from ics import Calendar, Event
from datetime import datetime, timezone
from icalendar import Calendar as ICalendar
from icalendar import Event as ICalendarEvent
from datetime import datetime

# Set up logger
logger = logging.getLogger(__name__)

# For future: add more config here (e.g., REDIS_URL, SESSION_TYPE, etc.)

load_dotenv()

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = 'redis://localhost:6379/0'
Session(app)

# Initialize calendar providers
CALENDAR_PROVIDERS = {
    provider.get_provider_key(): provider
    for provider in [GoogleCalendarProvider(), AppleCalendarProvider()]
}

# Redis setup
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Global cache for uploaded course data (keyed by upload_id) - still in memory for now
UPLOAD_CACHE = {}

# Redis-backed cache helpers for OAUTH_FLOW_CACHE and EVENT_SERVICE_CACHE
def redis_set_json(key, value, ex=None):
    redis_client.set(key, json.dumps(value), ex=ex)

def redis_get_json(key):
    val = redis_client.get(key)
    if val:
        return json.loads(val)
    return None

def redis_pop_json(key):
    pipe = redis_client.pipeline()
    pipe.get(key)
    pipe.delete(key)
    val, _ = pipe.execute()
    if val:
        return json.loads(val)
    return None

# For storing provider service objects, we store only the provider key and credentials info
def redis_set_service(upload_id, provider_key, credentials_dict, ex=None):
    redis_set_json(f'service:{upload_id}', {'provider': provider_key, 'credentials': credentials_dict}, ex=ex)

def redis_get_service(upload_id):
    return redis_get_json(f'service:{upload_id}')

def redis_pop_service(upload_id):
    return redis_pop_json(f'service:{upload_id}')

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

"""
Flask-Mail config for Gmail SMTP (best for dev/testing):
Set these environment variables:
  MAIL_USERNAME=your_gmail_address@gmail.com
  MAIL_PASSWORD=your_gmail_app_password
You must use an App Password (not your main Gmail password) if 2FA is enabled.
See: https://support.google.com/accounts/answer/185833
"""
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
mail = Mail(app)

# Add Apple OAuth environment variables
APPLE_CLIENT_ID = os.getenv('APPLE_CLIENT_ID')
APPLE_TEAM_ID = os.getenv('APPLE_TEAM_ID')
APPLE_KEY_ID = os.getenv('APPLE_KEY_ID')
APPLE_PRIVATE_KEY_PATH = os.getenv('APPLE_PRIVATE_KEY_PATH')
APPLE_REDIRECT_URI = os.getenv('APPLE_REDIRECT_URI', 'http://localhost:5000/oauth2callback')

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/start')
def upload():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        logger.info(f"Upload request method: {request.method}, url: {request.url}")
        if 'file' not in request.files:
            flash('No file part')
            logger.info("No file part in request. Redirecting to index.")
            return redirect(url_for('index'))
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            logger.info("No file selected. Redirecting to index.")
            return redirect(url_for('index'))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Process the PDF and store courses in session
            text = extract_text_from_pdf(filepath)
            courses = parse_schedule(text)
            if not courses:
                flash('No courses found in the PDF.')
                logger.info("No courses found in PDF. Redirecting to index.")
                return redirect(url_for('index'))
            upload_id = secrets.token_urlsafe(16)
            UPLOAD_CACHE[upload_id] = courses
            session['upload_id'] = upload_id
            session['pdf_filename'] = filename
            logger.info('PDF uploaded and parsed: %s, found %d courses', filename, len(courses))
            return redirect(url_for('show_events'))
        flash('Invalid file type. Please upload a PDF.')
        logger.info("Invalid file type. Redirecting to index.")
        return redirect(url_for('index'))
    except Exception as e:
        logger.exception('Error during file upload or PDF parsing')
        flash(f'Error during file upload or PDF parsing: {str(e)}')
        logger.info("Exception occurred. Redirecting to index.")
        return redirect(url_for('index'))

@app.route('/select-provider')
def select_provider():
    if 'upload_id' not in session:
        flash('Please upload a PDF first.')
        return redirect(url_for('index'))
    upload_id = session['upload_id']
    courses = UPLOAD_CACHE.get(upload_id, [])
    return render_template('select_provider.html', providers=CALENDAR_PROVIDERS.values())

@app.route('/confirm')
def confirm_events():
    upload_id = session.get('upload_id')
    courses = UPLOAD_CACHE.get(upload_id, [])
    filename = session.get('pdf_filename', None)
    if not courses:
        flash('No courses found. Please upload a PDF first.')
        return redirect(url_for('index'))
    course_details = "\n".join([
        f"{course['Course']} - {course['Days']} {course['Start']} - {course['End']}"
        for course in courses
    ])
    return render_template('confirm.html', course_details=course_details, filename=filename)

@app.route('/authorize/<provider>')
def authorize(provider):
    try:
        provider = provider.lower()
        if provider not in CALENDAR_PROVIDERS:
            flash('Invalid calendar provider.')
            logger.warning('Invalid calendar provider selected: %s', provider)
            return redirect(url_for('index'))
        
        upload_id = session.get('upload_id')
        courses = UPLOAD_CACHE.get(upload_id, [])
        
        if not courses:
            flash('No courses found. Please upload a PDF first.')
            return redirect(url_for('index'))
        
        if provider == 'apple':
            # For Apple, bypass OAuth and go directly to event selection
            session['display_courses'] = courses
            session['display_filename'] = session.get('pdf_filename')
            session['created_events'] = []
            # Store a dummy service entry for Apple
            redis_set_service(upload_id, provider, None)
            logger.info('Apple provider selected, going directly to event selection')
            return redirect(url_for('show_events'))
        else:
            # For Google, proceed with OAuth flow
            courses = UPLOAD_CACHE.pop(upload_id, [])
            provider_instance = CALENDAR_PROVIDERS[provider]
            auth_url, state, flow = provider_instance.get_auth_url()
            # Store only minimal state (code_verifier if present)
            code_verifier = getattr(flow, 'code_verifier', None)
            redis_set_json(f'oauth:{state}', {
                'courses': courses,
                'filename': session.get('pdf_filename'),
                'provider': provider,
                'code_verifier': code_verifier,
            }, ex=600)
            session['state'] = state
            session['provider'] = provider
            logger.info('OAuth flow started for provider: %s, state: %s', provider, state)
            return redirect(auth_url)
    except Exception as e:
        logger.exception('Error starting OAuth flow')
        flash(f'Error starting OAuth flow: {str(e)}')
        return redirect(url_for('index'))

@app.route('/oauth2callback', methods=['GET', 'POST'])
def oauth2callback():
    try:
        if 'state' not in session or 'provider' not in session:
            flash('Invalid state. Please try again.')
            logger.warning('Invalid state in session during OAuth callback.')
            return redirect(url_for('index'))
        
        provider = session['provider']
        state = session['state']
        logger.debug('OAuth callback received for provider: %s, state: %s', provider, state)
        logger.info('Request URL: %s', request.url)
        logger.info('Session keys: %r', dict(session))
        
        if provider not in CALENDAR_PROVIDERS:
            flash('Invalid calendar provider.')
            logger.warning('Invalid provider in session during OAuth callback.')
            return redirect(url_for('index'))
        
        provider_instance = CALENDAR_PROVIDERS[provider]
        
        # Retrieve and pop minimal state from Redis
        cache_entry = redis_pop_json(f'oauth:{state}')
        if not cache_entry:
            logger.warning('State %s not found in OAUTH_FLOW_CACHE (Redis).', state)
            flash('OAuth flow expired or invalid. Please try again.')
            return redirect(url_for('index'))
        
        selected_courses = cache_entry.get('selected_courses', [])
        filename = cache_entry.get('filename')
        code_verifier = cache_entry.get('code_verifier')
        
        # Handle Apple's form_post response mode
        if provider == 'apple' and request.method == 'POST':
            auth_response = request.form.get('code')
            if not auth_response:
                flash('No authorization code received from Apple.')
                return redirect(url_for('index'))
        else:
            auth_response = request.url
        
        if provider == 'google':
            try:
                from google_auth_oauthlib.flow import Flow
                flow = Flow.from_client_secrets_file(
                    'credentials.json',
                    scopes=GoogleCalendarProvider.SCOPES,
                    redirect_uri='http://localhost:5000/oauth2callback'
                )
                if code_verifier:
                    flow.code_verifier = code_verifier
                
                service = provider_instance.handle_callback(auth_response, flow)
                
                created_events = []
                if selected_courses:
                    for course in selected_courses:
                        try:
                            created_event = provider_instance.create_event(service, course)
                            created_events.append(created_event)
                        except Exception as e:
                            logger.error(f"Error creating event for course {course.get('Course')}: {e}")
                            flash(f"Error creating event for {course.get('Course')}. It might already exist or there was an API issue.", "warning")

                session['created_events'] = created_events
                session['pdf_filename'] = filename
                session['provider'] = 'google'
                
                logger.info(f"Successfully created {len(created_events)} Google Calendar events.")
                return redirect(url_for('show_confirmation'))

            except Exception as e:
                logger.exception('Error during Google event creation')
                flash(f'An error occurred creating Google Calendar events: {str(e)}')
                return redirect(url_for('index'))
        
        # Fallback for other providers or if something went wrong
        # The old logic here was redirecting to show_events, which is not correct for the post-oauth flow.
        # Apple/ICS flow doesn't hit this callback.
        logger.warning(f"OAuth callback hit for unhandled provider: {provider}")
        flash("Authentication process for the selected provider is not correctly handled after callback.")
        return redirect(url_for('index'))

    except Exception as e:
        logger.exception('Error handling OAuth callback')
        flash(f'An error occurred: {str(e)}')
        return redirect(url_for('index'))

@app.route('/events')
def show_events():
    upload_id = session.get('upload_id')
    courses = UPLOAD_CACHE.get(upload_id, [])
    if not courses:
        flash('Your session has expired. Please upload your schedule again.')
        return redirect(url_for('index'))
    filename = session.get('pdf_filename')
    created_events = session.pop('created_events', [])
    email_sent = session.pop('email_sent', False)
    return render_template('events.html', courses=courses, filename=filename, created_events=created_events, email_sent=email_sent)

@app.route('/create-events', methods=['POST'])
def create_selected_events():
    upload_id = session.get('upload_id')
    courses = UPLOAD_CACHE.get(upload_id)
    if not courses:
        flash('Your session has expired. Please upload your schedule again.')
        return redirect(url_for('index'))

    selected_indices = request.form.get('selected', '').split(',')
    if not selected_indices or not selected_indices[0]:
        flash('You did not select any events to create.')
        return redirect(url_for('show_events'))
    
    selected_courses = [courses[int(i)] for i in selected_indices if i.isdigit() and 0 <= int(i) < len(courses)]
    session['selected_courses'] = selected_courses
    
    provider = request.form.get('provider')
    session['provider'] = provider

    if provider == 'google':
        provider_instance = CALENDAR_PROVIDERS.get(provider)
        if not provider_instance:
            flash('Invalid calendar provider selected.')
            return redirect(url_for('show_events'))
        auth_url, state, flow = provider_instance.get_auth_url()
        code_verifier = getattr(flow, 'code_verifier', None)
        redis_set_json(f'oauth:{state}', {
            'selected_courses': selected_courses,
            'filename': session.get('pdf_filename'),
            'provider': provider,
            'code_verifier': code_verifier,
        }, ex=600)
        session['state'] = state
        return redirect(auth_url)
    
    elif provider == 'apple':
        # For Apple/Outlook, we now trigger a download and then show confirmation
        # The actual download will happen via a separate request from the confirm page
        flash('Your ICS file is ready for download.')
        return redirect(url_for('show_confirmation'))

    else:
        flash("Invalid provider selected.")
        return redirect(url_for('show_events'))

@app.route('/confirmation')
def show_confirmation():
    created_events = session.get('created_events', [])
    selected_courses = session.get('selected_courses', [])
    courses = UPLOAD_CACHE.get(session.get('upload_id'), [])
    
    # For Apple/Outlook, we create a summary from selected_courses
    if not created_events and session.get('provider') == 'apple':
        created_events = [{'summary': f"{c['Course']} - {c['Section']}"} for c in selected_courses]

    if not created_events and not selected_courses:
        flash('No events were created or your session has expired.')
        return redirect(url_for('index'))

    return render_template('confirm.html',
                           created_events=created_events,
                           course_details=get_course_details_string(courses),
                           filename=session.get('pdf_filename'),
                           email_sent=session.pop('email_sent', False),
                           provider=session.get('provider'))

def get_course_details_string(courses):
    if not courses:
        return "No course details available."
    return "\n".join([
        f"{course['Course']} - {course['Days']} {course['Start']} - {course['End']}"
        for course in courses
    ])

@app.route('/clear-session')
def clear_session():
    upload_id = session.pop('upload_id', None)
    session.clear()
    flash('Session cleared!')
    return redirect(url_for('index'))

# Route: Send email summary
@app.route('/send-email-summary', methods=['POST'])
def send_email_summary():
    email = request.form.get('email')
    created_events = session.get('created_events', [])
    
    if not email or not created_events:
        flash('Could not send email. Missing data.')
        return redirect(url_for('show_confirmation'))

    html_body = render_template('email_summary.html', events=created_events)
    msg = Message("Your SchedShare Event Summary",
                  recipients=[email],
                  html=html_body)
    try:
        mail.send(msg)
        flash('Email summary sent successfully!')
        session['email_sent'] = True
    except Exception as e:
        logger.exception("Email sending failed")
        flash(f"Failed to send email: {e}")

    return redirect(url_for('show_confirmation'))

# Route: Download ICS file
@app.route('/download-ics', methods=['POST'])
def download_ics():
    courses_to_export = session.get('selected_courses', [])
    
    if not courses_to_export:
        flash('No selected courses to export. Your session might have expired.')
        return redirect(url_for('index'))

    cal = ICalendar()
    cal.add('prodid', '-//SchedShare//EN')
    cal.add('version', '2.0')

    for c in courses_to_export:
        try:
            e = ICalendarEvent()
            e.add('summary', f"{c.get('Course', 'N/A')} ({c.get('Section', 'N/A')})")
            e.add('location', c.get('Location', 'N/A'))
            e.add('description', f"Instructor: {c.get('Instructor', 'N/A')}, Status: {c.get('Status', 'N/A')}, Mode: {c.get('DeliveryMode', 'N/A')}")
            
            start_dt = _ics_start_datetime(c)
            end_dt = _ics_end_datetime(c)
            if start_dt and end_dt:
                e.add('dtstart', datetime.fromisoformat(start_dt))
                e.add('dtend', datetime.fromisoformat(end_dt))
            
            days_mapping = {"Mo": "MO", "Tu": "TU", "We": "WE", "Th": "TH", "Fr": "FR", "Sa": "SA", "Su": "SU"}
            days = [days_mapping.get(day) for day in c.get('Days', '').split() if day in days_mapping]
            
            if days:
                semester = c.get('Section', '')[:3]
                until_date_str = _ics_until_date(c['EndDate'], semester)
                until_dt = datetime.strptime(until_date_str, '%Y%m%dT%H%M%SZ')
                e.add('rrule', {'freq': 'weekly', 'byday': days, 'until': until_dt})
            
            cal.add_component(e)
        except Exception as ex:
            logger.warning(f"Could not create .ics event for course {c.get('Course')}. Error: {ex}")
            continue

    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-disposition": "attachment; filename=schedule.ics"}
    )

def _ics_start_datetime(course):
    # Returns ISO string for ics Event begin
    from datetime import datetime
    year = int('20' + course['Section'][1:3])
    dt = datetime.strptime(f"{course['StartDate']} {year} {course['Start']}", '%d-%b %Y %H:%M')
    return dt.isoformat()

def _ics_end_datetime(course):
    from datetime import datetime
    year = int('20' + course['Section'][1:3])
    dt = datetime.strptime(f"{course['StartDate']} {year} {course['End']}", '%d-%b %Y %H:%M')
    return dt.isoformat()

def _ics_until_date(date_str, semester):
    # Returns YYYYMMDDT000000Z for RRULE UNTIL
    from datetime import datetime
    year = int('20' + semester[1:3])
    dt = datetime.strptime(date_str, '%d-%b').replace(year=year)
    return dt.strftime('%Y%m%dT000000Z')

# Route: ICS direct download from select-provider
@app.route('/ics-direct', methods=['POST'])
def ics_direct():
    courses = []
    upload_id = session.get('upload_id')
    if upload_id:
        courses = UPLOAD_CACHE.get(upload_id, [])
    if not courses:
        # Try session fallback
        courses = session.get('display_courses', [])
    filename = session.get('pdf_filename', 'CourseSchedule.ics')
    if not courses:
        flash('No courses to export.')
        return redirect(url_for('index'))
    cal = Calendar()
    for c in courses:
        e = Event()
        e.name = f"{c['Course']} ({c['Section']})"
        e.begin = _ics_start_datetime(c)
        e.end = _ics_end_datetime(c)
        e.location = c['Location']
        e.description = f"Instructor: {c['Instructor']}, Status: {c['Status']}, Mode: {c['DeliveryMode']}"
        # Add RRULE for recurrence
        days_mapping = {"Mo": "MO", "Tu": "TU", "We": "WE", "Th": "TH", "Fr": "FR", "Sa": "SA", "Su": "SU"}
        days = ','.join([days_mapping.get(day, '') for day in c['Days'].split() if day in days_mapping])
        semester = c['Section'][:3]
        until_date = _ics_until_date(c['EndDate'], semester)
        if days:
            logger.info(f"Adding RRULE for course: {c['Course']} with days: {days} and until date: {until_date}")
            e.rrule = f"FREQ=WEEKLY;BYDAY={days};UNTIL={until_date}"
        # Add DTSTAMP for RFC compliance
        e.created = datetime.now(timezone.utc)
        cal.events.add(e)

    return Response(cal.serialize(), mimetype='text/calendar', headers={
        'Content-Disposition': f'attachment; filename="{filename.replace('.pdf', '.ics').replace('.PDF', '.ics')}"'
    })

# Privacy route
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/home')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)