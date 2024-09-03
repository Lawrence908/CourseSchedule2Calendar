import pdfplumber
import re

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        # Assuming the course schedule is on the second page
        page = pdf.pages[1]
        text = page.extract_text()
    return text

def parse_schedule(text):
    # Regex pattern adjusted to capture all necessary fields from the table
    pattern = (
        r"(?P<Course>[\w\s]+)\s+"
        r"(?P<Section>F24N\d{2})\s+"
        r"(?P<Location>\(Nanaimo \d+ \d+\))\s+"
        r"(?P<Days>(Mo|Tu|We|Th|Fr|Sa|Su)+)\s+"
        r"(?P<Start>\d{2}:\d{2})\s+-\s+(?P<End>\d{2}:\d{2})\s+"
        r"(?P<StartDate>\d{2}/\d{2}/\d{4})\s+-\s+(?P<EndDate>\d{2}/\d{2}/\d{4})\s+"
        r"(?P<Status>[\w\s]+)\s+"
        r"(?P<Instructor>[\w\s]+)\s+"
        r"(?P<DeliveryMode>[\w\s]+)"
    )
    
    matches = re.finditer(pattern, text)
    courses = []
    for match in matches:
        section = match.group("Section")[3:]
        location = match.group("Location").replace("(Nanaimo ", "B").replace(" ", " R").replace(")", "")
        days = match.group("Days").split()
        
        course = {
            'title': f"{match.group('Course')} - {section} - {location}",
            'days': days,
            'start_time': match.group("Start"),
            'end_time': match.group("End"),
            'start_date': match.group("StartDate"),
            'end_date': match.group("EndDate"),
            'location': "Vancouver Island University, 900 Fifth St, Nanaimo, BC V9R 5S5, Canada",
            'description': match.group("Instructor")
        }
        courses.append(course)
    return courses
