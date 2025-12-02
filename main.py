import os
import re
from PyPDF2 import PdfReader
import requests

def scan_pdf_with_ollama(file_path, log_file, ollama_url, ollama_prompt):
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

    # Send the extracted text to the Ollama model
    try:
        response = requests.post(
            ollama_url,
            json={"prompt": ollama_prompt, "content": pdf_text}
        )
        response.raise_for_status()
        result = response.json()
        is_applicable = result.get("is_applicable", False)
        matched_attributes = result.get("matched_attributes", [])
    except Exception as e:
        print(f"Error communicating with Ollama model: {e}")
        return

    # Determine the log entry
    if is_applicable and matched_attributes:
        log_entry = f"{file_path}: {', '.join(matched_attributes)}\n"
    else:
        log_entry = f"{file_path}: Not applicable\n"

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
    ollama_url = "http://localhost:8000/analyze"  # Replace with your Ollama model endpoint
    ollama_prompt = (
        "Determine if the following PDF content meets any of these requirements: \n"
        "- Female Only\n"
        "- STEM Major Only\n"
        "- Service Member Only\n"
        "Return 'is_applicable' as true or false and list matched attributes."
    )
    scan_pdf_with_ollama(pdf_path, log_path, ollama_url, ollama_prompt)