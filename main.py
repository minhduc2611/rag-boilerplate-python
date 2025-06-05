from flask import Flask, request, jsonify
from services.upload_file import upload_file
import logging
from libs.weaviate_lib import initialize_schema, close_client
from contextlib import contextmanager
from services.handle_ask import handle_ask
from data_classes.common_classes import AskRequest, Message
from services.handle_messages import handle_chat
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def weaviate_connection():
    try:
        yield
    finally:
        close_client()

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
        
        results, failed_objects = upload_file(files, description)

        return jsonify({
            "status": "success" if failed_objects == 0 else "failed",
            "description": description,
            "results": results,
            "failed_objects": failed_objects
        }), 200

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/chat/<session_id>/ask', methods=['POST'])
def ask_endpoint(session_id):
    try:
        body = request.json
        # Convert the JSON body into an AskRequest object
        messages = [Message(**msg) for msg in body.get('messages', [])]
        ask_request = AskRequest(
            messages=messages,
            session_id=session_id,
            options=body.get('options')
        )
        results = handle_ask(ask_request)
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error processing ask: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/chat/<session_id>', methods=['GET'])
def chat_endpoint(session_id):
    try:
        results = handle_chat(session_id)
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    with weaviate_connection():
        initialize_schema()
        app.run(debug=False, port=3001) 
    
