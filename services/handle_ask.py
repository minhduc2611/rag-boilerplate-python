from typing import List, Dict, Any
from flask import Response
import json
from libs.weaviate_lib import search_documents, insert_to_collection_in_batch
from data_classes.common_classes import AskRequest
from agents.buddha_agent import generate_answer
from datetime import datetime, timedelta

def validate_ask(body: AskRequest) -> List[str]:
    errors: List[str] = []
    if not body.messages or not isinstance(body.messages, list):
        errors.append("messages is required")
    if not body.session_id:
        errors.append("session_id is required")
    return errors

def handle_ask(body: AskRequest) -> Dict[str, Any]:
    errors = validate_ask(body)
    if errors:
        return Response(
            content=json.dumps({"error": errors}),
            status_code=400,
            media_type="application/json"
        )
    # Get the last user message as the query
    user_messages = [msg for msg in body.messages if msg.role == "user"]
    last_user_message = user_messages[-1] if user_messages else None

    if not last_user_message:
        return Response(
            content=json.dumps({"error": "No user message found"}),
            status_code=400,
            media_type="application/json"
        )

    # Search for relevant documents
    relevant_docs = search_documents(last_user_message.content)

    contexts = [
        {
            "title": doc["title"],
            "content": doc["content"]
        }
        for doc in relevant_docs
    ]
    # Generate answer using OpenAI
    answer = generate_answer(body.messages, contexts, body.options)
    sources_set = set(doc["title"] for doc in contexts)

    user_time = datetime.now()

    # Insert messages to the database
    insert_to_collection_in_batch(
        collection_name="Messages",
        properties=[{
            "session_id": body.session_id,
            "content": last_user_message.content,
            "role": last_user_message.role,
            "created_at": user_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        {
            "session_id": body.session_id,
            "content": answer,
            "role": "assistant",
            "created_at": (user_time + timedelta(milliseconds=100)).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        ]
    )
    return {
        "answer": answer,
        "sources": list(sources_set),
        "contexts": contexts
    }
