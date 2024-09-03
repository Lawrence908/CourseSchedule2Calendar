import tkinter as tk
from tkinter import filedialog, messagebox
from pdf_parser import extract_text_from_pdf, parse_schedule
from google_calendar import authenticate_google_calendar, create_event

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Course Schedule to Google Calendar")
        self.geometry("400x200")
        self.create_widgets()

    def create_widgets(self):
        self.label = tk.Label(self, text="Select your course schedule PDF:")
        self.label.pack(pady=10)

        self.upload_button = tk.Button(self, text="Upload PDF", command=self.upload_pdf)
        self.upload_button.pack(pady=5)

        self.process_button = tk.Button(self, text="Process and Create Events", command=self.process_pdf, state=tk.DISABLED)
        self.process_button.pack(pady=5)

    def upload_pdf(self):
        self.pdf_path = filedialog.askopenfilename(
            title="Select PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        if self.pdf_path:
            self.process_button.config(state=tk.NORMAL)
            messagebox.showinfo("Selected", f"Selected file: {self.pdf_path}")

    def process_pdf(self):
        try:
            text = extract_text_from_pdf(self.pdf_path)
            courses = parse_schedule(text)
            if not courses:
                messagebox.showwarning("No Courses Found", "No course details were found in the PDF.")
                return
            
            # Display course details for confirmation
            course_details = "\n".join([f"{course['Course']} - {course['Days']} {course['Start']} - {course['End']}" for course in courses])
            confirm = messagebox.askyesno("Confirm Events", f"Do you want to create the following events in Google Calendar?\n\n{course_details}")
            
            if confirm:
                service = authenticate_google_calendar()
                for course in courses:
                    create_event(service, course)
                messagebox.showinfo("Success", "All events have been created in your Google Calendar.")
            else:
                messagebox.showinfo("Cancelled", "Event creation has been cancelled.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    app = Application()
    app.mainloop()