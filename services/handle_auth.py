from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from data_classes.common_classes import User, AuthRequest
from libs.weaviate_lib import search_non_vector_collection, insert_to_collection
from weaviate.collections.classes.filters import Filter
import os

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')  # In production, use a secure secret
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = timedelta(days=1)  # Token expires in 1 day

class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def create_jwt_token(user_id: str) -> str:
    """Create a JWT token for a user"""
    print('user_id:')
    print(user_id)
    payload = {
        'user_id': user_id,
        'exp': datetime.now(UTC) + JWT_EXPIRATION,
        'iat': datetime.now(UTC)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify a JWT token and return the payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired", 401)
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token", 401)

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a user by email"""
    filters = Filter.by_property("email").equal(email)
    users = search_non_vector_collection(
        collection_name="Users",
        filters=filters,
        limit=1,
        properties=["email", "password", "name", "created_at", "updated_at"]
    )

    return users[0] if users else None

def sign_up(auth_request: AuthRequest) -> Dict[str, Any]:
    """Register a new user"""
    # Check if user already exists
    existing_user = get_user_by_email(auth_request.email)
    if existing_user:
        raise AuthError("Email already registered", 400)

    # Create new user
    user = User(
        email=auth_request.email,
        password=generate_password_hash(auth_request.password),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        name=auth_request.name
    )

    # Insert user into database
    user_data = {
        "email": user.email,
        "password": user.password,
        "name": user.name,
        "created_at": user.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": user.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    # Insert and get the UUID
    user_id = insert_to_collection(
        collection_name="Users",
        properties=user_data
    )
    
    if not user_id:
        raise AuthError("Failed to create user", 500)
        

    # Generate token
    token = create_jwt_token(user_id)
    return {
        "token": token,
        "user": {
            "email": user.email,
            "name": user.name
        }
    }

def sign_in(auth_request: AuthRequest) -> Dict[str, Any]:
    """Authenticate a user and return a token"""
    # Get user from database
    user = get_user_by_email(auth_request.email)
    if not user:
        raise AuthError("Invalid email or password", 401)

    # Verify password
    if not check_password_hash(user["password"], auth_request.password):
        raise AuthError("Invalid email or password", 401)

    # Generate token
    token = create_jwt_token(user["email"])
    return {
        "token": token,
        "user": {
            "email": user["email"],
            "name": user["name"]
        }
    } 