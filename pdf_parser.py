import pdfplumber
import re

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        # Assuming the course schedule is on the second page
        page = pdf.pages[1]
        text = page.extract_text()
    return text

def parse_schedule(text):
    # Refined regex patterns to capture course details and subsequent lines without course and section
    course_pattern = (
        r"(?P<Course>[A-Z]{4} \d{3})\s+"  # Course code
        r"(?P<Section>F24N\d{2})\s+"  # Section
        r"(?P<Location>Nanaimo \d{3} \d{3})\s+"  # Location
        r"(?P<Days>(?:Mo|Tu|We|Th|Fr|Sa|Su)+(?: (?:Mo|Tu|We|Th|Fr|Sa|Su))*)\s+"  # Days
        r"(?P<Start>\d{2}:\d{2})\s+"  # Start time
        r"(?P<End>\d{2}:\d{2})\s+"  # End time
        r"(?P<StartDate>\d{2}-[A-Z]{3})\s+"  # Start date
        r"(?P<EndDate>\d{2}-[A-Z]{3})\s+"  # End date
        r"(?P<Status>Enrolled)\s+"  # Status
        r"(?P<Instructor>[A-Z\s]+)\s+"  # Instructor
        r"(?P<DeliveryMode>Face-to-Face)"  # Delivery mode
    )
    
    subsequent_pattern = (
        r"(?P<Location>Nanaimo \d{3} \d{3})\s+"  # Location
        r"(?P<Days>(?:Mo|Tu|We|Th|Fr|Sa|Su)+(?: (?:Mo|Tu|We|Th|Fr|Sa|Su))*)\s+"  # Days
        r"(?P<Start>\d{2}:\d{2})\s+"  # Start time
        r"(?P<End>\d{2}:\d{2})\s+"  # End time
        r"(?P<StartDate>\d{2}-[A-Z]{3})\s+"  # Start date
        r"(?P<EndDate>\d{2}-[A-Z]{3})\s+"  # End date
        r"(?P<Status>Enrolled)\s+"  # Status
        r"(?P<DeliveryMode>Face-to-Face)"  # Delivery mode
    )
    
    courses = []
    last_course = None
    last_section = None

    # Debugging: Print the extracted text
    print("Extracted Text:\n", text)

    for line in text.split('\n'):
        # Debugging: Print each line being processed with exact characters
        print(f"Processing line: {repr(line)}")
        
        course_match = re.match(course_pattern, line)
        subsequent_match = re.match(subsequent_pattern, line)
        
        if course_match:
            course = course_match.groupdict()
            last_course = course['Course']
            last_section = course['Section']
            courses.append(course)
            # Debugging: Print each matched course
            print("Matched Course:\n", course)
        elif subsequent_match and last_course and last_section:
            course = subsequent_match.groupdict()
            course['Course'] = last_course
            course['Section'] = last_section
            courses.append(course)
            # Debugging: Print each matched subsequent entry
            print("Matched Subsequent Entry:\n", course)
        else:
            # Debugging: Print if no match is found
            print("No match found for line.")
    
    # Debugging: Print the number of matches found
    print(f"Number of matches found: {len(courses)}")
    
    return courses

# Example usage
if __name__ == "__main__":
    pdf_path = "path_to_your_pdf.pdf"
    text = extract_text_from_pdf(pdf_path)
    courses = parse_schedule(text)
    if not courses:
        print("No course details were found in the PDF.")
    else:
        print("Courses found:\n", courses)