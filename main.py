from flask import Flask, request, jsonify
from services.upload_file import upload_file
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/api/v1/upload-documents', methods=['POST'])
def process_pdf_endpoint():
    """Endpoint to process a PDF file and return semantic chunks"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        files = request.files.getlist('files')
        description = request.form.get('description')
        
        results = upload_file(files, description)

        return jsonify({
            "status": "success",
            "description": description,
            "results": results
        }), 200

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=3001) 