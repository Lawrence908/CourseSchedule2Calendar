# filepath: /home/chris/github/CourseSchedule2Calendar/app.py
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
            return redirect(url_for('select_provider'))
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
        
        courses = cache_entry.get('courses', [])
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
        
        # Build provider service but do NOT create events yet. Store service for later use.
        service = provider_instance.handle_callback(auth_response, None)
        
        upload_id = session.get('upload_id')
        if upload_id:
            # Store provider key and credentials in Redis
            if provider == 'apple':
                # For Apple, store the tokens directly
                redis_set_service(upload_id, provider, service)
            else:
                # For Google, store the credentials dict
                creds_dict = getattr(service._http.credentials, 'to_json', lambda: None)()
                if creds_dict:
                    creds_dict = json.loads(creds_dict)
                redis_set_service(upload_id, provider, creds_dict)
        
        # Retain courses for display; events will be created after user selection.
        session['created_events'] = []
        session['display_courses'] = courses
        session['display_filename'] = filename
        logger.info('OAuth callback completed; waiting for user course selection.')
        return redirect(url_for('show_events'))
    except Exception as e:
        logger.exception('Error handling OAuth callback')
        flash(f'Error handling OAuth callback: {str(e)}')
        return redirect(url_for('index'))

@app.route('/events')
def show_events():
    try:
        created_events = session.get('created_events', [])
        courses = session.get('display_courses', [])
        filename = session.get('display_filename', None)
        if not courses:
            flash('No courses found. Please upload a PDF first.')
            return redirect(url_for('index'))
        return render_template('events.html', courses=courses, filename=filename, created_events=created_events)
    except Exception as e:
        logger.exception('Error displaying events page')
        flash(f'Error displaying events page: {str(e)}')
        return redirect(url_for('index'))

# ---------- New route: create events for selected courses ----------

@app.route('/create-events', methods=['POST'])
def create_selected_events():
    try:
        selected_raw = request.form.get('selected', '')
        selected_indices = [s for s in selected_raw.split(',') if s]
        if not selected_indices:
            flash('Please select at least one course to create events.')
            return redirect(url_for('show_events'))

        courses = session.get('display_courses', [])
        upload_id = session.get('upload_id')
        service_entry = redis_get_service(upload_id)
        if not service_entry:
            flash('Session expired. Please restart the authorization process.')
            return redirect(url_for('index'))

        provider_key = service_entry['provider']
        provider_instance = CALENDAR_PROVIDERS[provider_key]
        
        created_events = []
        for idx_str in selected_indices:
            try:
                idx = int(idx_str)
            except ValueError:
                continue
            if 0 <= idx < len(courses):
                course = courses[idx]
                try:
                    logger.info('Creating event (user-selected) with data: %r', course)
                    event = provider_instance.create_event(service_entry, course)
                    
                    if provider_key == 'apple':
                        # For Apple, return the ICS file for download
                        return Response(
                            event['ics_data'],
                            mimetype='text/calendar',
                            headers={
                                'Content-Disposition': f'attachment; filename="{event["filename"]}"'
                            }
                        )
                    else:
                        created_events.append(event)
                except Exception as event_exc:
                    logger.exception('Error creating event for course: %r', course)
                    flash(f"Error creating event for {course.get('Course', 'Unknown Course')}: {str(event_exc)}")

        session['created_events'] = created_events
        if created_events:
            flash(f'Successfully created {len(created_events)} events in your calendar!')
        else:
            flash('No events were created.')
        return redirect(url_for('show_events'))
    except Exception as e:
        logger.exception('Error creating selected events')
        flash(f'Error creating selected events: {str(e)}')
        return redirect(url_for('show_events'))

@app.route('/clear-session')
def clear_session():
    session.clear()
    flash('Session cleared!')
    return redirect(url_for('index'))

# Route: Send email summary
@app.route('/send-email-summary', methods=['POST'])
def send_email_summary():
    email = request.form.get('email')
    # Only include user-selected (created) events
    created_events = session.get('created_events', [])
    filename = session.get('display_filename', 'CourseSchedule.pdf')
    if not email or not created_events:
        flash('Missing email or created event data.')
        return redirect(url_for('show_events'))
    # Store email in Redis set
    redis_client.sadd('emails', email)
    # Improved subject
    subject = "Schedule2Calendar - Your Course Calendar Events"
    # Improved HTML body
    from flask import render_template_string
    html_body = render_template_string("""
        <h2>Your Course Events from {{ filename }}</h2>
        <ul>
        {% for c in events %}
            <li>
                <b>{{ c['summary'] }}</b><br>
                <span>{{ c.get('description', '') }}</span><br>
                <span>{{ c.get('location', '') }}</span><br>
                {% if c.get('start') and c['start'].get('dateTime') and c.get('end') and c['end'].get('dateTime') %}
                    <span>{{ c['start']['dateTime'] }} - {{ c['end']['dateTime'] }}</span>
                {% endif %}
            </li>
        {% endfor %}
        </ul>
        <p>Thank you for using Schedule2Calendar!</p>
    """, events=created_events, filename=filename)
    # Fallback plain text
    text_body = f"Here are your course events from {filename}:\n\n"
    for c in created_events:
        text_body += f"{c.get('summary', '')}: {c.get('description', '')} at {c.get('location', '')} "
        if c.get('start') and c['start'].get('dateTime') and c.get('end') and c['end'].get('dateTime'):
            text_body += f"({c['start']['dateTime']} to {c['end']['dateTime']})"
        text_body += "\n"
    try:
        msg = Message(subject, recipients=[email])
        msg.body = text_body
        msg.html = html_body
        mail.send(msg)
        flash('Email sent successfully!')
    except Exception as e:
        logger.exception('Error sending email')
        flash(f'Error sending email: {str(e)}')
    return redirect(url_for('show_events'))

# Route: Download ICS file
@app.route('/download-ics', methods=['POST'])
def download_ics():
    courses = session.get('display_courses', [])
    filename = session.get('display_filename', 'CourseSchedule.ics')
    if not courses:
        flash('No courses to export.')
        return redirect(url_for('show_events'))
    cal = Calendar()
    for c in courses:
        e = Event()
        e.name = f"{c['Course']} ({c['Section']})"
        e.begin = _ics_start_datetime(c)
        e.end = _ics_end_datetime(c)
        e.location = c['Location']
        e.description = f"Instructor: {c['Instructor']}, Status: {c['Status']}, Mode: {c['DeliveryMode']}"
        cal.events.add(e)
    # Ensure the filename ends with .ics, not .pdf or .PDF
    ics_filename = filename.replace('.pdf', '.ics').replace('.PDF', '.ics')
    if not ics_filename.lower().endswith('.ics'):
        ics_filename += '.ics'
    return Response(str(cal), mimetype='text/calendar', headers={
        'Content-Disposition': f'attachment; filename="{ics_filename}"'
    })

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
        cal.events.add(e)
    from flask import Response
    return Response(str(cal), mimetype='text/calendar', headers={
        'Content-Disposition': f'attachment; filename="{filename.replace('.pdf', '.ics').replace('.PDF', '.ics')}"'
    })

# Privacy route
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

if __name__ == '__main__':
    app.run(debug=True)