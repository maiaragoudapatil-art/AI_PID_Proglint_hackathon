import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from werkzeug.utils import secure_filename
import time

# Import the core processing pipeline
from main import process_document

app = Flask(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = None  # No size limit

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        return redirect(request.url)
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Start processing
        start_time = time.time()
        
        try:
            # Process the document
            result_json_path = process_document(filepath, app.config['OUTPUT_FOLDER'])
            processing_time = round(time.time() - start_time, 2)
            
            # Redirect to result page, passing the filename of the output
            return redirect(url_for('result', filename=os.path.basename(result_json_path), p_time=processing_time))
            
        except Exception as e:
            return f"An error occurred during processing: {str(e)}", 500
            
    return redirect(request.url)

@app.route('/result')
def result():
    filename = request.args.get('filename')
    p_time = request.args.get('p_time')
    
    if not filename:
        return redirect(url_for('index'))
        
    import json
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return render_template('result.html', data=data, processing_time=p_time)
    except FileNotFoundError:
        return "Result file not found.", 404

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return "File not found.", 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
