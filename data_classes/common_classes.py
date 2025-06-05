from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class Message:
    role: str
    content: str
    session_id: Optional[str] = None
    created_at: Optional[str] = None

@dataclass
class AskRequest:
    messages: List[Message]
    session_id: str
    options: Optional[Dict[str, Any]] = None

@dataclass
class Pagination:
    limit: int = 3
    offset: Optional[int] = None
    page: Optional[int] = None