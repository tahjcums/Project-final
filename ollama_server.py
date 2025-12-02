from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
import os
import requests
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ollama configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3.1:latest"

# System prompt for analyzing PDFs
SYSTEM_PROMPT = """You are an expert document analyzer. Your task is to analyze PDF content and determine if it relates to female-only or female-targeted scholarships, programs, or opportunities.

Look for indicators such as:
- "Female Only"
- "Women Only"
- "For Women"
- "Female Scholarship"
- "Women's Scholarship"
- "Female-Targeted"
- "Women-Targeted"
- "For Female Students"
- "Women Scholarship"
- "Female Applicants"
- Any other variations that indicate the opportunity is specifically for females/women

When analyzing, respond with ONLY a JSON object in this exact format:
{
  "is_female_targeted": true or false,
  "confidence": 0.0 to 1.0,
  "matched_phrases": ["phrase1", "phrase2"],
  "reasoning": "brief explanation"
}

Do not include any other text or markdown. Only the JSON object."""

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

def call_ollama_model(pdf_text):
    """Call Ollama model to analyze PDF content"""
    try:
        prompt = f"{SYSTEM_PROMPT}\n\nAnalyze this PDF content:\n\n{pdf_text}"
        
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract the response text
        response_text = result.get("response", "").strip()
        
        # Try to parse JSON from the response
        try:
            # Find JSON in the response (sometimes Ollama adds extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                analysis = json.loads(json_str)
            else:
                # Fallback if no JSON found
                analysis = {
                    "is_female_targeted": False,
                    "confidence": 0,
                    "matched_phrases": [],
                    "reasoning": "Could not parse response"
                }
        except json.JSONDecodeError:
            analysis = {
                "is_female_targeted": False,
                "confidence": 0,
                "matched_phrases": [],
                "reasoning": "Could not parse model response"
            }
        
        return analysis
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Error communicating with Ollama: {str(e)}",
            "is_female_targeted": False,
            "confidence": 0,
            "matched_phrases": [],
            "reasoning": "Connection error"
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "is_female_targeted": False,
            "confidence": 0,
            "matched_phrases": [],
            "reasoning": "Unexpected error"
        }

@app.route("/upload", methods=["POST"])
def upload_pdf():
    try:
        # Check if file is in request
        if 'pdf_file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['pdf_file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.pdf'):
            return jsonify({"error": "Only PDF files are allowed"}), 400
        
        # Save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from PDF
        pdf_text = ""
        try:
            reader = PdfReader(filepath)
            for page in reader.pages:
                pdf_text += page.extract_text()
        except Exception as e:
            return jsonify({"error": f"Error reading PDF: {str(e)}"}), 500
        
        # Analyze the PDF using Ollama model
        analysis = call_ollama_model(pdf_text)
        
        # Check for error
        if "error" in analysis:
            return jsonify({"error": analysis["error"]}), 500
        
        is_female_targeted = analysis.get("is_female_targeted", False)
        status = "Applicable" if is_female_targeted else "Not Applicable"
        
        # Clean up the uploaded file
        os.remove(filepath)
        
        return jsonify({
            "filename": filename,
            "status": status,
            "is_applicable": is_female_targeted,
            "confidence": analysis.get("confidence", 0),
            "matched_phrases": analysis.get("matched_phrases", []),
            "reasoning": analysis.get("reasoning", "")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/analyze", methods=["POST"])
def analyze_pdf():
    try:
        # Extract the prompt and content from the request
        data = request.get_json()
        prompt = data.get("prompt", SYSTEM_PROMPT)  # Use provided prompt or default
        content = data.get("content", "")

        # Call Ollama model with custom prompt
        full_prompt = f"{prompt}\n\nAnalyze this PDF content:\n\n{content}"
        
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False
            },
            timeout=120
        )
        
        response.raise_for_status()
        result = response.json()
        response_text = result.get("response", "").strip()
        
        # Try to parse JSON from response
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                analysis = json.loads(json_str)
            else:
                analysis = {
                    "is_female_targeted": False,
                    "confidence": 0,
                    "matched_phrases": [],
                    "reasoning": "Could not parse response"
                }
        except json.JSONDecodeError:
            analysis = {
                "is_female_targeted": False,
                "confidence": 0,
                "matched_phrases": [],
                "reasoning": "Could not parse model response"
            }

        return jsonify(analysis)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)