import pdfplumber

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        # Assuming the course schedule is on the second page
        page = pdf.pages[1]
        text = page.extract_text()
    return text

def parse_schedule(text):
    
    
    
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

    # Debugging: Print the extracted text
    # print("Extracted Text:\n", text)

    # Define the locations to look for in the text
    locations = ["Nanaimo", "Duncan"]
    
    # Define the regex pattern for days of the week
    days_pattern = r"(?P<Days>(?:Mo|Tu|We|Th|Fr|Sa|Su)+(?: (?:Mo|Tu|We|Th|Fr|Sa|Su))*)"

    lines = text.split('\n')
    
    i = 0
    while not lines[i].startswith("Course"):
        i += 1
    if lines[i].startswith("Course"):
        i += 1
    while i < len(lines):
        # Initialize the current course dictionary
        current_course = {key: "" for key in course_dict} # Initialize an empty course dictionary
        
        line = lines[i].strip()
        print(f"Processing line: {repr(line)}")
        columns = line.split()
        
        current_course["Course"] = columns[0] + " " + columns[1]
        current_course["Section"] = columns[2]
        current_course["Location"] = columns[3] + " " + columns[4] + " " + columns[5]
        current_course["Days"] = ' '.join(columns[6:-8])
        current_course["Start"] = columns[-8]
        current_course["End"] = columns[-7]
        current_course["StartDate"] = columns[-6]
        current_course["EndDate"] = columns[-5]
        current_course["Status"] = columns[-4]
        current_course["Instructor"] = columns[-3] + " " + columns[-2]
        current_course["DeliveryMode"] = columns[-1]
        
        # Append the current course to the list of courses
        courses.append(current_course)
        
        # Look ahead to see if the next line is a location
        j = i + 1
        while j < len(lines) and (lines[j].startswith(locations[0]) or lines[j].startswith(locations[1])):
            # Initialize a subsequent course dictionary
            subsequent_course = {key: "" for key in course_dict}
            
            next_line = lines[j].strip()
            print(f"Processing line: {repr(next_line)}")
            columns = next_line.split()
            
            subsequent_course["Course"] = current_course["Course"]
            subsequent_course["Section"] = current_course["Section"]
            subsequent_course["Location"] = columns[0] + " " + columns[1] + " " + columns[2]
            subsequent_course["Days"] = ' '.join(columns[3:-5])
            subsequent_course["Start"] = columns[-5]
            subsequent_course["End"] = columns[-4]
            subsequent_course["StartDate"] = columns[-3]
            subsequent_course["EndDate"] = columns[-2]
            subsequent_course["Status"] = columns[-1]
            subsequent_course["Instructor"] = current_course["Instructor"]
            subsequent_course["DeliveryMode"] = current_course["DeliveryMode"]
            
            # Append the subsequent course to the list of courses
            courses.append(subsequent_course)
            
            # Reset the subsequent course dictionary
            subsequent_course = {key: "" for key in course_dict}
            
            j += 1
            
        # Reset the current course dictionary
        current_course = {key: "" for key in course_dict}
        
        # Increment the index
        i = j
    
    # Debugging: Print the number of courses with unique course codes in the ["Course"] key
    print(f"Number of unique course codes: {len(set([course['Course'] for course in courses]))}")
    # Debugging: Print the number of matches found
    print(f"Number of weekly calendar entries: {len(courses)}")
    
    return courses