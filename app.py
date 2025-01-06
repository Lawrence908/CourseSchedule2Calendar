# filepath: /home/chris/github/CourseSchedule2Calendar/app.py
from flask import Flask, request, redirect, url_for, render_template, flash, session
from werkzeug.utils import secure_filename
import os
from pdf_parser import extract_text_from_pdf, parse_schedule
from google_calendar import authenticate_google_calendar, create_event
import pickle
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv

load_dotenv()

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'supersecretkey'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        flash(f'Selected file: {filename}')
        return redirect(url_for('process_file', filename=filename))
    else:
        flash('Invalid file type')
        return redirect(request.url)

@app.route('/process/<filename>')
def process_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        text = extract_text_from_pdf(file_path)
        courses = parse_schedule(text)
        if not courses:
            flash('No course details were found in the PDF.')
            return redirect(url_for('index'))
        
        # Display course details for confirmation
        course_details = "\n".join([f"{course['Course']} - {course['Days']} {course['Start']} - {course['End']}" for course in courses])
        session['courses'] = courses
        return render_template('confirm.html', course_details=course_details)
    except Exception as e:
        flash(f'An error occurred: {e}')
        return redirect(url_for('index'))

@app.route('/authorize')
def authorize():
    auth_url, state = authenticate_google_calendar()
    session['state'] = state
    return redirect(auth_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session.get('state')
    if not state:
        return redirect(url_for('index'))

    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/calendar'],
        state=state,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    courses = session.get('courses', [])
    for course in courses:
        create_event(service, course)
    flash('All events have been created in your Google Calendar.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(host='localhost', port=5000, debug=True)