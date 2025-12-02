import os
import re
from PyPDF2 import PdfReader

def scan_pdf(file_path, log_file):
    # Define the strings to search for (case-insensitive)
    search_strings = ["Female Only", "STEM Major Only", "Service Member Only", "International only"]

    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    # Extract text from the PDF
    try:
        reader = PdfReader(file_path)
        pdf_text = ""
        for page in reader.pages:
            pdf_text += page.extract_text()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return

    # Search for strings in the PDF text
    matched_attributes = []
    for string in search_strings:
        if re.search(string, pdf_text, re.IGNORECASE):
            matched_attributes.append(string)

    # Determine the log entry
    if matched_attributes:
        log_entry = f"{file_path}: {', '.join(matched_attributes)}\n"
    else:
        log_entry = f"{file_path}: Applicable\n"

    # Write the log entry to the log file
    try:
        with open(log_file, "a") as log:
            log.write(log_entry)
        print(f"Log updated: {log_entry.strip()}")
    except Exception as e:
        print(f"Error writing to log file: {e}")

if __name__ == "__main__":
    # Example usage
    pdf_path = input("Enter the path to the PDF file: ").strip()
    log_path = "scan_log.txt"  # Log file name
    scan_pdf(pdf_path, log_path)