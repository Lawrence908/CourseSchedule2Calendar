import pdfplumber
import re


def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        # Assuming the course schedule is on the second page
        page = pdf.pages[1]
        text = page.extract_text()
    return text

def parse_schedule(text):
    # Same logic as before, but without debug prints
    course_dict = {
        "Course": [],
        "Section": [],
        "Location": [],
        "Days": [],
        "Start": [],
        "End": [],
        "StartDate": [],
        "EndDate": [],
        "Status": [],
        "Instructor": [],
        "DeliveryMode": []
    }
    
    courses = []
    locations = ["Nanaimo", "Duncan"]
    days_pattern = r"(Mo|Tu|We|Th|Fr|Sa|Su)"
    lines = text.split('\n')
    
    i = 0
    while not lines[i].startswith("Course"):
        i += 1
    if lines[i].startswith("Course"):
        i += 1
    while i < len(lines):
        current_course = {key: "" for key in course_dict}
        line = lines[i].strip()
        columns = line.split()
        current_course["Course"] = columns[0] + " " + columns[1]
        current_course["Section"] = columns[2]
        current_course["Location"] = columns[3] + " " + columns[4] + " " + columns[5]
        days_list = [col for col in columns[6:-8] if re.fullmatch(days_pattern, col)]
        current_course["Days"] = ' '.join(days_list) if days_list else ""        
        current_course["Start"] = columns[-8]
        current_course["End"] = columns[-7]
        current_course["StartDate"] = columns[-6]
        current_course["EndDate"] = columns[-5]
        current_course["Status"] = columns[-4]
        current_course["Instructor"] = columns[-3] + " " + columns[-2]
        current_course["DeliveryMode"] = columns[-1]
        courses.append(current_course)
        j = i + 1
        while j < len(lines) and (lines[j].startswith(locations[0]) or lines[j].startswith(locations[1])):
            subsequent_course = {key: "" for key in course_dict}
            next_line = lines[j].strip()
            columns = next_line.split()
            subsequent_course["Course"] = current_course["Course"]
            subsequent_course["Section"] = current_course["Section"]
            subsequent_course["Location"] = columns[0] + " " + columns[1] + " " + columns[2]
            days_list = [col for col in columns[3:-5] if re.fullmatch(days_pattern, col)]
            subsequent_course["Days"] = ' '.join(days_list) if days_list else ""            
            subsequent_course["Start"] = columns[-5]
            subsequent_course["End"] = columns[-4]
            subsequent_course["StartDate"] = columns[-3]
            subsequent_course["EndDate"] = columns[-2]
            subsequent_course["Status"] = columns[-1]
            subsequent_course["Instructor"] = current_course["Instructor"]
            subsequent_course["DeliveryMode"] = current_course["DeliveryMode"]
            courses.append(subsequent_course)
            subsequent_course = {key: "" for key in course_dict}
            j += 1
        current_course = {key: "" for key in course_dict}
        i = j
    return courses
