from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

@dataclass
class Message:
    role: str
    content: str
    session_id: Optional[str] = None
    created_at: Optional[str] = None

# enum for language
class Language(Enum):
    VI = "vi"
    EN = "en"

@dataclass
class AskRequest:
    messages: List[Message]
    session_id: str
    model: str
    language: Language = Language.VI
    options: Optional[Dict[str, Any]] = None

@dataclass
class Pagination:
    limit: int = 3
    offset: Optional[int] = None
    page: Optional[int] = None

@dataclass
class Section:
    uuid: Optional[str] = None
    language: Language = Language.VI
    messages: Optional[List[Message]] = None
    title: Optional[str] = None
    order: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    author: Optional[str] = None

@dataclass
class SignInRequest:
    email: str
    password: str

@dataclass
class SignUpRequest:
    email: str
    password: str
    name: Optional[str] = None

@dataclass
class User:
    email: str
    password: str  # This will be hashed
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class AuthRequest:
    email: str
    password: str
    name: Optional[str] = None
    
@dataclass
class Document:
    uuid: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: Optional[str] = None
    
@dataclass
class File:
    uuid: Optional[str] = None
    name: Optional[str] = None
    path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: Optional[str] = None