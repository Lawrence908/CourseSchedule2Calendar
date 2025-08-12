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
from datetime import datetime, timezone, timedelta
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

# Force HTTPS for URL generation
app.config['PREFERRED_URL_SCHEME'] = 'https'

# --- Redis / session configuration ---
app.config['SESSION_TYPE'] = 'redis'

#      Use docker-compose service name "redis" unless overridden
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# A Redis *instance* is required by Flask-Session, not just the URL string
from redis import Redis as _Redis
app.config['SESSION_REDIS'] = _Redis.from_url(REDIS_URL)

Session(app)

# Initialize calendar providers
CALENDAR_PROVIDERS = {
    provider.get_provider_key(): provider
    for provider in [GoogleCalendarProvider(), AppleCalendarProvider()]
}

# Redis setup (reuse same URL)
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Global cache for uploaded course data (keyed by upload_id) - still in memory for now
UPLOAD_CACHE = {}

# Analytics tracking functions
def track_event(event_type, data=None):
    """Track analytics events in Redis with timestamps"""
    timestamp = datetime.now().isoformat()
    event_data = {
        'type': event_type,
        'timestamp': timestamp,
        'data': data or {}
    }
    
    # Store individual event
    event_id = f"analytics:event:{secrets.token_urlsafe(8)}"
    redis_client.setex(event_id, 86400 * 30, json.dumps(event_data))  # 30 days TTL
    
    # Update counters
    today = datetime.now().strftime('%Y-%m-%d')
    redis_client.hincrby(f"analytics:daily:{today}", event_type, 1)
    redis_client.hincrby("analytics:total", event_type, 1)
    
    # Track unique sessions (if session_id available)
    if 'session_id' in session:
        session_key = f"analytics:session:{session['session_id']}"
        redis_client.sadd(session_key, event_type)
        redis_client.expire(session_key, 86400 * 7)  # 7 days TTL

def get_analytics_summary():
    """Get analytics summary for dashboard"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get today's stats
    today_stats = redis_client.hgetall(f"analytics:daily:{today}")
    
    # Get total stats
    total_stats = redis_client.hgetall("analytics:total")
    
    # Get recent activity (last 7 days)
    recent_activity = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_stats = redis_client.hgetall(f"analytics:daily:{date}")
        if day_stats:
            recent_activity.append({
                'date': date,
                'stats': day_stats
            })
    
    return {
        'today': today_stats,
        'total': total_stats,
        'recent': recent_activity
    }

# Redis-backed cache helpers for OAUTH_FLOW_CACHE and EVENT_SERVICE_CACHE
def redis_set_json(key, value, ex=None):
    redis_client.set(key, json.dumps(value), ex=ex)

def redis_get_json(key):
    val = redis_client.get(key)
    if isinstance(val, (str, bytes, bytearray)) and val:
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
    """Root route - redirect to home to ensure consistent canonical URLs"""
    return redirect(url_for('home'), code=301)

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
            if file.filename is None:
                flash('No selected file')
                logger.info("No file selected. Redirecting to index.")
                return redirect(url_for('index'))
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
            
            # Track successful PDF upload
            track_event('pdf_uploaded', {
                'filename': filename,
                'courses_found': len(courses),
                'upload_id': upload_id
            })
            
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
                redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'https://schedshare.chrislawrence.ca/oauth2callback')
                logger.info(f"[OAuth2Callback] Using redirect_uri for token exchange: {redirect_uri}")
                flow = Flow.from_client_secrets_file(
                    'credentials.json',
                    scopes=GoogleCalendarProvider.SCOPES,
                    redirect_uri=redirect_uri
                )
                if code_verifier:
                    flow.code_verifier = code_verifier
                logger.info(f"[OAuth2Callback] Flow redirect_uri: {flow.redirect_uri}")
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
                
                # Track successful Google Calendar event creation
                track_event('google_events_created', {
                    'events_created': len(created_events),
                    'courses_selected': len(selected_courses),
                    'provider': 'google'
                })
                
                # Track for advanced analytics (if available)
                try:
                    from advanced_analytics import analytics
                    upload_id = session.get('upload_id', 'unknown')
                    analytics.mark_events_created(upload_id, 'google')
                except ImportError:
                    # Advanced analytics not available
                    pass
                
                flash(f"Successfully created {len(created_events)} events.", "success")
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

    # Track event creation attempt
    track_event('events_selected', {
        'provider': provider,
        'courses_selected': len(selected_courses),
        'total_courses_available': len(courses)
    })
    
    # Track for advanced analytics (if available)
    try:
        from advanced_analytics import analytics
        upload_id = session.get('upload_id', 'unknown')
        analytics.track_course_selection(selected_courses, provider, upload_id)
    except ImportError:
        # Advanced analytics not available
        pass

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
        session['trigger_ics_download'] = True  # Set one-time download flag
        flash('Your ICS file is ready for download.')
        return redirect(url_for('show_confirmation'))

    else:
        flash("Invalid provider selected.")
        return redirect(url_for('show_events'))

@app.route('/confirmation')
def show_confirmation():
    created_events = session.get('created_events', [])
    selected_courses = session.get('selected_courses', [])
    
    # For Apple/Outlook, we create a summary from selected_courses
    if not created_events and session.get('provider') == 'apple':
        created_events = [{'summary': f"{c['Course']} - {c['Section']}"} for c in selected_courses]
        session['created_events'] = created_events  # Store for email summary

    if not created_events and not selected_courses:
        flash('No events were created or your session has expired.')
        return redirect(url_for('index'))

    return render_template('confirm.html',
                           created_events=created_events,
                           courses_to_display=selected_courses,
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
    # Redirect to home instead of index to avoid potential redirect chains
    return redirect(url_for('home'))

# Route: Send email summary
@app.route('/send-email-summary', methods=['POST'])
def send_email_summary():
    email = request.form.get('email')
    created_events = session.get('created_events', [])
    
    if not email or not created_events:
        logger.warning("Email sending failed. Email provided: %s. Events in session: %s", bool(email), bool(created_events))
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
        
        # Track successful email summary
        track_event('email_summary_sent', {
            'events_count': len(created_events),
            'email_domain': email.split('@')[-1] if '@' in email else 'unknown'
        })
        
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

    # Track ICS download
    track_event('ics_downloaded', {
        'courses_count': len(courses_to_export),
        'provider': 'apple/outlook'
    })
    
    # Track for advanced analytics (if available)
    try:
        from advanced_analytics import analytics
        upload_id = session.get('upload_id', 'unknown')
        analytics.mark_events_created(upload_id, 'apple')
    except ImportError:
        # Advanced analytics not available
        pass

    cal = ICalendar()
    cal.add('prodid', '-//SchedShare//EN')
    cal.add('version', '2.0')

    for c in courses_to_export:
        try:
            e = ICalendarEvent()
            e.add('summary', f"{c.get('Course', 'N/A')} ({c.get('Section', 'N/A')})")
            # Set location to full campus address
            loc = c.get('Location', 'N/A')
            if 'Nanaimo' in loc:
                location = "Vancouver Island University, 900 Fifth St, Nanaimo, BC V9R 5S5, Canada"
            elif 'Cowichan' in loc:
                location = "Vancouver Island University, Cowichan Campus, 2011 University Way, North Cowichan, BC V9L 0C7, Canada"
            else:
                location = loc
            e.add('location', location)
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

# Privacy route
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/home')
def home():
    return render_template('home.html')

# --- SEO: sitemap.xml and robots.txt ---
@app.route('/sitemap.xml')
def sitemap_xml():
    """Generate a comprehensive sitemap for public pages."""
    try:
        # Define pages with their priorities and change frequencies
        pages = [
            {
                'url': url_for('home', _external=True),
                'priority': '1.0',
                'changefreq': 'weekly',
                'description': 'Home page'
            },
            {
                'url': url_for('upload', _external=True),
                'priority': '0.9',
                'changefreq': 'monthly',
                'description': 'Start page for uploading schedules'
            },
            {
                'url': url_for('privacy', _external=True),
                'priority': '0.3',
                'changefreq': 'yearly',
                'description': 'Privacy policy'
            },
            {
                'url': url_for('terms', _external=True),
                'priority': '0.3',
                'changefreq': 'yearly',
                'description': 'Terms of service'
            },
        ]

        now = datetime.utcnow().strftime('%Y-%m-%d')
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        ]
        
        for page in pages:
            lines.append(
                f"  <url>\n"
                f"    <loc>{page['url']}</loc>\n"
                f"    <lastmod>{now}</lastmod>\n"
                f"    <changefreq>{page['changefreq']}</changefreq>\n"
                f"    <priority>{page['priority']}</priority>\n"
                f"  </url>"
            )
        
        lines.append('</urlset>')
        return Response("\n".join(lines), mimetype='application/xml')
    except Exception as e:
        logger.exception("Failed generating sitemap.xml: %s", e)
        # Fallback empty sitemap so crawlers get a valid response
        return Response("""<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>""",
                        mimetype='application/xml')

@app.route('/robots.txt')
def robots_txt():
    """Expose robots.txt that points to the sitemap and hides non-indexable routes."""
    rules = [
        'User-agent: *',
        # Allow crawling of public pages
        'Allow: /',
        'Allow: /home',
        'Allow: /start',
        'Allow: /privacy',
        'Allow: /terms',
        'Allow: /static/',
        # Disallow operational or private routes
        'Disallow: /upload',
        'Disallow: /events',
        'Disallow: /create-events',
        'Disallow: /oauth2callback',
        'Disallow: /analytics',
        'Disallow: /advanced-analytics',
        'Disallow: /clear-session',
        'Disallow: /send-email-summary',
        'Disallow: /download-ics',
        'Disallow: /authorize/',
        'Disallow: /confirm',
        'Disallow: /select-provider',
        'Disallow: /uploads/',
        # Crawl delay for rate limiting
        'Crawl-delay: 1',
        # Point to sitemap
        f"Sitemap: {url_for('sitemap_xml', _external=True)}",
    ]
    return Response("\n".join(rules) + "\n", mimetype='text/plain')

@app.route('/analytics')
def analytics_dashboard():
    """Analytics dashboard for tracking usage metrics"""
    # Basic authentication check
    auth_token = request.args.get('token')
    expected_token = os.getenv('ANALYTICS_TOKEN', 'schedshare-analytics-2025')
    
    if auth_token != expected_token:
        return render_template('analytics_login.html')
    
    try:
        analytics = get_analytics_summary()
        
        # Calculate some derived metrics
        total_uploads = int(analytics['total'].get('pdf_uploaded', 0))
        total_events_selected = int(analytics['total'].get('events_selected', 0))
        total_google_events = int(analytics['total'].get('google_events_created', 0))
        total_ics_downloads = int(analytics['total'].get('ics_downloaded', 0))
        total_emails = int(analytics['total'].get('email_summary_sent', 0))
        
        # Calculate conversion rates
        conversion_rate = (total_events_selected / total_uploads * 100) if total_uploads > 0 else 0
        google_usage_rate = (total_google_events / total_events_selected * 100) if total_events_selected > 0 else 0
        ics_usage_rate = (total_ics_downloads / total_events_selected * 100) if total_events_selected > 0 else 0
        
        # Get today's stats
        today_uploads = int(analytics['today'].get('pdf_uploaded', 0))
        today_events = int(analytics['today'].get('events_selected', 0))
        today_google = int(analytics['today'].get('google_events_created', 0))
        today_ics = int(analytics['today'].get('ics_downloaded', 0))
        today_emails = int(analytics['today'].get('email_summary_sent', 0))
        
        return render_template('analytics.html', 
                             analytics=analytics,
                             total_uploads=total_uploads,
                             total_events_selected=total_events_selected,
                             total_google_events=total_google_events,
                             total_ics_downloads=total_ics_downloads,
                             total_emails=total_emails,
                             conversion_rate=conversion_rate,
                             google_usage_rate=google_usage_rate,
                             ics_usage_rate=ics_usage_rate,
                             today_uploads=today_uploads,
                             today_events=today_events,
                             today_google=today_google,
                             today_ics=today_ics,
                             today_emails=today_emails)
    except Exception as e:
        logger.exception("Error loading analytics dashboard")
        flash(f"Error loading analytics: {str(e)}")
        return redirect(url_for('index'))

@app.route('/advanced-analytics')
def advanced_analytics_dashboard():
    """Advanced analytics dashboard with department/time analysis"""
    # Basic authentication check
    auth_token = request.args.get('token')
    expected_token = os.getenv('ANALYTICS_TOKEN', 'schedshare-analytics-2025')
    
    if auth_token != expected_token:
        return render_template('analytics_login.html')
    
    try:
        from advanced_analytics import analytics
        
        # Get analytics data
        departments = analytics.get_department_analytics()
        time_slots = analytics.get_time_analytics()
        days = analytics.get_day_analytics()
        summary = analytics.get_summary_stats()
        
        # Calculate max for time bar scaling
        max_time_courses = max([slot['total_courses'] for slot in time_slots]) if time_slots else 0
        
        return render_template('advanced_analytics.html',
                             departments=departments,
                             time_slots=time_slots,
                             days=days,
                             summary=summary,
                             max_time_courses=max_time_courses)
    except Exception as e:
        logger.exception("Error loading advanced analytics dashboard")
        flash(f"Error loading advanced analytics: {str(e)}")
        return redirect(url_for('index'))

if __name__ == '__main__':
    # This block is for local development.
    # For production, a Gunicorn server is used as the entrypoint.
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))