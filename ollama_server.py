from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

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
        
        # Analyze the PDF
        requirements = ["Female Only", "STEM Major Only", "Service Member Only"]
        matched_attributes = [req for req in requirements if req.lower() in pdf_text.lower()]
        
        is_applicable = bool(matched_attributes)
        status = "Applicable" if is_applicable else "Not Applicable"
        
        # Clean up the uploaded file
        os.remove(filepath)
        
        return jsonify({
            "filename": filename,
            "status": status,
            "is_applicable": is_applicable,
            "matched_attributes": matched_attributes
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/analyze", methods=["POST"])
def analyze_pdf():
    try:
        # Extract the prompt and content from the request
        data = request.get_json()
        prompt = data.get("prompt", "")
        content = data.get("content", "")

        # Simulate a lightweight model analysis
        requirements = ["Female Only", "STEM Major Only", "Service Member Only"]
        matched_attributes = [req for req in requirements if req.lower() in content.lower()]

        # Determine if the PDF is applicable
        is_applicable = bool(matched_attributes)

        # Return the result
        return jsonify({
            "is_applicable": is_applicable,
            "matched_attributes": matched_attributes
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)