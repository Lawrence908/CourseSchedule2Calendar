import os
from pdf_parser import extract_text_from_pdf, parse_schedule
from google_calendar import authenticate_google_calendar, create_event

def main(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return

    text = extract_text_from_pdf(pdf_path)
    courses = parse_schedule(text)

    if not courses:
        print("No courses found in the PDF.")
        return

    service = authenticate_google_calendar()

    for course in courses:
        create_event(service, course)

    print("All events have been created successfully.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Import course schedule PDF to Google Calendar.')
    parser.add_argument('pdf', help='Path to the course schedule PDF file.')
    args = parser.parse_args()

    main(args.pdf)
