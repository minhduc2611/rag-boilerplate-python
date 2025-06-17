from flask import Flask, request, jsonify, Response, g
from flask_cors import CORS
from functools import wraps
from services.upload_file import upload_file
import logging
from libs.weaviate_lib import initialize_schema, close_client
from contextlib import contextmanager
from services.handle_ask import  handle_ask_streaming, handle_ask_non_streaming, AskError
from services.handle_auth import sign_in, sign_up, verify_jwt_token, AuthError, blacklist_token
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
from agents.meta_agent import (
    generate_meta_agent_response,
    create_agent,
    list_agents,
    get_agent,
    update_agent,
    delete_agent,
    search_agents,
    generate_agent_code,
    test_agent
)
import json

app = Flask(__name__)
CORS(app, expose_headers=["X-Total-Count", "X-Page-Size", "X-Page-Number", "X-Total-Pages"])

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
        sections, total_count = get_sections(email, limit, offset)
        
        # Calculate pagination info
        page_number = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
        
        response = jsonify(sections)
        response.headers['X-Total-Count'] = str(total_count)
        response.headers['X-Page-Size'] = str(limit)
        response.headers['X-Page-Number'] = str(page_number)
        response.headers['X-Total-Pages'] = str(total_pages)
        return response, 200
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

# manage documents 

@app.route('/api/v1/documents', methods=['GET'])
@login_required
def get_documents_endpoint():
    """Get all documents"""
    try:
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        documents, total_count = get_documents(limit, offset)
        
        # Calculate pagination info
        page_number = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
        
        response = jsonify(documents)
        response.headers['X-Total-Count'] = str(total_count)
        response.headers['X-Page-Size'] = str(limit)
        response.headers['X-Page-Number'] = str(page_number)
        response.headers['X-Total-Pages'] = str(total_pages)
        return response, 200
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
        files, total_count = get_files(limit, offset)
        
        # Calculate pagination info
        page_number = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
        
        response = jsonify(files)
        response.headers['X-Total-Count'] = str(total_count)
        response.headers['X-Page-Size'] = str(limit)
        response.headers['X-Page-Number'] = str(page_number)
        response.headers['X-Total-Pages'] = str(total_pages)
        return response, 200
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
    

# Meta Agent endpoints ================================
@app.route('/api/v1/meta-agent/chat', methods=['POST'])
@login_required
def meta_agent_chat_endpoint():
    """Chat with the meta agent"""
    try:
        body = request.json
        messages = [Message(**msg) for msg in body.get('messages', [])]
        language = body.get('language', Language.EN)
        options = body.get('options', {})
        
        response = generate_meta_agent_response(
            messages=messages,
            language=language,
            options=options
        )
        
        return jsonify({"response": response}), 200
    except Exception as e:
        logger.error(f"Error in meta agent chat: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents', methods=['POST'])
@login_required
def create_agent_endpoint():
    """Create a new agent"""
    try:
        body = request.json
        name = body.get('name')
        description = body.get('description')
        system_prompt = body.get('system_prompt')
        tools = body.get('tools', [])
        model = body.get('model', 'gpt-4o-mini')
        temperature = body.get('temperature', 0)
        
        result = create_agent(
            name=name,
            description=description,
            system_prompt=system_prompt,
            tools=tools,
            model=model,
            temperature=temperature,
            author=g.user_id
        )
        
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents', methods=['GET'])
@login_required
def list_agents_endpoint():
    """List all agents for the current user"""
    try:
        limit = int(request.args.get('limit', 10))
        agents = list_agents(author=g.user_id, limit=limit)
        return jsonify(agents), 200
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/<agent_id>', methods=['GET'])
@login_required
def get_agent_endpoint(agent_id):
    """Get a specific agent"""
    try:
        agent = get_agent(agent_id)
        if "error" in agent:
            return jsonify(agent), 404
        return jsonify(agent), 200
    except Exception as e:
        logger.error(f"Error getting agent: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/<agent_id>', methods=['PUT'])
@login_required
def update_agent_endpoint(agent_id):
    """Update an agent"""
    try:
        body = request.json
        result = update_agent(agent_id, **body)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error updating agent: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/<agent_id>', methods=['DELETE'])
@login_required
def delete_agent_endpoint(agent_id):
    """Delete an agent"""
    try:
        result = delete_agent(agent_id)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error deleting agent: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/search', methods=['GET'])
@login_required
def search_agents_endpoint():
    """Search for agents"""
    try:
        query = request.args.get('query', '')
        limit = int(request.args.get('limit', 5))
        agents = search_agents(query=query, limit=limit)
        return jsonify(agents), 200
    except Exception as e:
        logger.error(f"Error searching agents: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/<agent_id>/code', methods=['GET'])
@login_required
def generate_agent_code_endpoint(agent_id):
    """Generate Python code for an agent"""
    try:
        agent_config = get_agent(agent_id)
        if "error" in agent_config:
            return jsonify(agent_config), 404
        
        code = generate_agent_code(agent_config)
        return jsonify({"code": code}), 200
    except Exception as e:
        logger.error(f"Error generating agent code: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/<agent_id>/test', methods=['POST'])
@login_required
def test_agent_endpoint(agent_id):
    """Test an agent with sample input"""
    try:
        body = request.json
        test_input = body.get('test_input', 'Hello, how can you help me?')
        
        result = test_agent(agent_id=agent_id, test_input=test_input)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error testing agent: {str(e)}")
        return jsonify({"error": str(e)}), 500
# ================================
@app.route('/api/v1/logout', methods=['POST'])
@login_required
def logout_endpoint():
    """Logout"""
    try:
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(" ")[1]
        
        # Blacklist the token
        success = blacklist_token(token, g.user_id)
        
        if not success:
            return jsonify({"error": "Failed to logout"}), 500
            
        return jsonify({"status": "success", "message": "Successfully logged out"}), 200
        
    except Exception as e:
        logger.error(f"Error logging out: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    with weaviate_connection():
        initialize_schema()
        app.run(debug=False, port=3001) 
