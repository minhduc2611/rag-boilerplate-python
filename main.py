from flask import Flask, request, jsonify, Response, g
from flask_cors import CORS
from functools import wraps
from services.upload_file import upload_file
import logging
from libs.weaviate_lib import initialize_schema, close_client
from contextlib import contextmanager
from services.handle_ask import  handle_ask_streaming, handle_ask_non_streaming, AskError
from services.handle_auth import sign_in, sign_up, verify_jwt_token, AuthError
from services.handle_youtube import get_video_metadata, YouTubeError
from data_classes.common_classes import AskRequest, Message, Section, AuthRequest, Language, Document, File
from services.handle_messages import handle_chat
from services.handle_sections import (
    create_section,
    get_sections,
    get_section_by_id,
    update_section,
    delete_section,
    search_sections
)
from services.upload_file import get_documents, create_document, update_document, delete_document, get_document_by_id, get_files, get_file_by_id, create_file, update_file, delete_file          
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "No authorization header"}), 401

        try:
            # Extract token from "Bearer <token>"
            token = auth_header.split(" ")[1]
            payload = verify_jwt_token(token)
            g.user_id = payload['user_id']
            return f(*args, **kwargs)
        except AuthError as e:
            return jsonify({"error": e.message}), e.status_code
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 401

    return decorated_function

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@contextmanager
def weaviate_connection():
    try:
        yield
    finally:
        close_client()
        
@app.route('/api/v1/upload-documents', methods=['POST'])
@login_required
def process_pdf_endpoint():
    """Endpoint to process a PDF file and return semantic chunks"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        # 1. prepare payload
        files = request.files.getlist('files')
        description = request.form.get('description')
        author = g.user_id
        # 2. handle request
        results, failed_objects = upload_file(files, description, author)

        # 3. return results
        return jsonify({
            "status": "success" if failed_objects == 0 else "failed",
            "description": description,
            "results": results,
            "failed_objects": failed_objects
        }), 200

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sign-in', methods=['POST'])
def sign_in_endpoint():
    """Sign in endpoint"""
    try:
        body = request.json
        auth_request = AuthRequest(**body)
        result = sign_in(auth_request)
        return jsonify(result), 200
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error signing in: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sign-up', methods=['POST'])
def sign_up_endpoint():
    """Sign up endpoint"""
    try:
        body = request.json
        auth_request = AuthRequest(**body)
        result = sign_up(auth_request)
        return jsonify(result), 201
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error signing up: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/chat/<session_id>/ask', methods=['POST'])
@login_required
def ask_endpoint(session_id):
    try:
        # 1. prepare payload
        body = request.json
        messages = [Message(**msg) for msg in body.get('messages', [])]
        ask_request = AskRequest(
            messages=messages,
            session_id=session_id,
            language=body.get('language', Language.VI),
            options=body.get('options'),
            model=body.get('model', 'gpt-4o')
        )

        # 2. handle request
        is_streaming = ask_request.options and ask_request.options.get("stream", False)
        try:
            if is_streaming:
                return handle_ask_streaming(ask_request)
            else:
                results = handle_ask_non_streaming(ask_request)
                return jsonify(results), 200
        except AskError as e:
            return Response(
                response=json.dumps({"error": e.message}),
                status=e.status_code,
                mimetype="application/json"
            )
    except Exception as e:
        logger.error(f"Error processing ask: {str(e)}")
        return Response(
            response=json.dumps({"error": str(e)}),
            status=500,
            mimetype="application/json"
        )

@app.route('/api/v1/sections/<section_id>/messages', methods=['GET'])
@login_required
def chat_endpoint(section_id):
    try:
        results = handle_chat(section_id)
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        return jsonify({"error": str(e)}), 500

# manage sections
@app.route('/api/v1/sections', methods=['POST'])
@login_required
def create_section_endpoint():
    """Create a new section"""
    try:
        body = request.json
        section = Section(**body)
        section.author = g.user_id
        section = create_section(section)
        return jsonify(section), 201
    except Exception as e:
        logger.error(f"Error creating section: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sections', methods=['GET'])
@login_required
def get_sections_endpoint():
    """Get all sections with pagination"""
    try:
        # get email from jwt token
        email = g.user_id
        print(email)
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        sections = get_sections(email, limit, offset)
        return jsonify(sections), 200
    except Exception as e:
        logger.error(f"Error getting sections: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sections/<section_id>', methods=['GET'])
@login_required
def get_section_endpoint(section_id):
    """Get a section by ID"""
    try:
        section = get_section_by_id(section_id)
        if not section:
            return jsonify({"error": "Section not found"}), 404
        return jsonify(section), 200
    except Exception as e:
        logger.error(f"Error getting section: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sections/<section_id>', methods=['PUT'])
@login_required
def update_section_endpoint(section_id):
    """Update a section"""
    try:
        body = request.json
        section = Section(**body)
        success = update_section(section_id, section)
        if not success:
            return jsonify({"error": "Section not found"}), 404
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error updating section: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sections/<section_id>', methods=['DELETE'])
@login_required
def delete_section_endpoint(section_id):
    """Delete a section"""
    try:
        success = delete_section(section_id)
        if not success:
            return jsonify({"error": "Section not found"}), 404
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error deleting section: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sections/search', methods=['GET'])
@login_required
def search_sections_endpoint():
    """Search sections by content"""
    try:
        query = request.args.get('query', '')
        limit = int(request.args.get('limit', 10))
        sections = search_sections(query, limit)
        return jsonify(sections), 200
    except Exception as e:
        logger.error(f"Error searching sections: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/youtube/metadata/<video_id>', methods=['GET'])
@login_required
def youtube_metadata_endpoint(video_id):
    """Get metadata for a YouTube video"""
    try:
        metadata = get_video_metadata(video_id)
        return jsonify(metadata), 200
    except YouTubeError as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Error fetching YouTube metadata: {str(e)}")
        return jsonify({"error": str(e)}), 500

# manage documents 

@app.route('/api/v1/documents', methods=['GET'])
@login_required
def get_documents_endpoint():
    """Get all documents"""
    try:
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        documents = get_documents(limit, offset)
        return jsonify(documents), 200
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/documents/<document_id>', methods=['GET'])
@login_required
def get_document_endpoint(document_id):
    """Get a document by ID"""
    try:
        document = get_document_by_id(document_id) 
        return jsonify(document), 200
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/documents', methods=['POST'])
@login_required
def create_document_endpoint():
    """Create a new document"""
    try:
        body = request.json
        document = Document(**body) 
        document.author = g.user_id
        document = create_document(document)
        return jsonify(document), 201
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/v1/documents/<document_id>', methods=['PUT'])
@login_required
def update_document_endpoint(document_id):
    """Update a document"""
    try:
        body = request.json
        document = Document(**body)
        document.author = g.user_id
        document = update_document(document_id, document)
        return jsonify(document), 200
    except Exception as e:
        logger.error(f"Error updating document: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/v1/documents/<document_id>', methods=['DELETE'])
@login_required
def delete_document_endpoint(document_id):
    """Delete a document"""
    try:
        success = delete_document(document_id)
        if not success:
            return jsonify({"error": "Document not found"}), 404
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        return jsonify({"error": str(e)}), 500

# manage files
@app.route('/api/v1/files', methods=['GET'])
@login_required
def get_files_endpoint():
    """Get all files"""
    try:
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        files = get_files(limit, offset)
        return jsonify(files), 200
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/v1/files/<file_id>', methods=['GET'])
@login_required
def get_file_endpoint(file_id):
    """Get a file by ID"""
    try:
        file = get_file_by_id(file_id)
        return jsonify(file), 200
    except Exception as e:
        logger.error(f"Error getting file: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/v1/files/<file_id>', methods=['PUT'])
@login_required
def update_file_endpoint(file_id):
    """Update a file"""
    try:
        body = request.json
        file = File(**body)
        file.author = g.user_id
        file = update_file(file_id, file)
        return jsonify(file), 200
    except Exception as e:
        logger.error(f"Error updating file: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/v1/files/<file_id>', methods=['DELETE'])
@login_required
def delete_file_endpoint(file_id):
    """Delete a file"""
    try:
        success = delete_file(file_id)
        if not success:
            return jsonify({"error": "File not found"}), 404
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return jsonify({"error": str(e)}), 500
    







if __name__ == '__main__':
    with weaviate_connection():
        initialize_schema()
        app.run(debug=False, port=3001) 
