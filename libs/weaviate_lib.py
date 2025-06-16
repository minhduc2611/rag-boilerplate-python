import os
from typing import List, Dict, Any, Optional, TypeVar
import weaviate
from weaviate.auth import Auth
import weaviate.classes as wvc
from weaviate.collections.classes.grpc import Sorting
from weaviate.collections.classes.filters import _Filters, Filter
from datetime import datetime
# Environment variables
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
headers = {
    "X-OpenAI-Api-Key": OPENAI_API_KEY,
}
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,                     # Weaviate URL: "REST Endpoint" in Weaviate Cloud console
    auth_credentials=Auth.api_key(WEAVIATE_API_KEY),  # Weaviate API key: "ADMIN" API key in Weaviate Cloud console
    headers=headers
)
def close_client():
    client.close()
COLLECTION_DOCUMENTS = "Documents"
COLLECTION_MESSAGES = "Messages"
COLLECTION_SECTIONS = "Sections"
COLLECTION_USERS = "Users"
COLLECTION_FILES = "Files"

def initialize_schema() -> None:
    """Initialize the Weaviate schema if it doesn't exist."""
    exists = client.collections.exists(COLLECTION_DOCUMENTS)
    if not exists:
        client.collections.create(
            name=COLLECTION_DOCUMENTS,
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(
                model=EMBEDDING_MODEL
            ),
            properties=[
                wvc.config.Property(name="title", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="description", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="file_id", data_type=wvc.config.DataType.UUID),
            ]
        )
        print("🙌🏼 Collection Documents created successfully")
    exists = client.collections.exists(COLLECTION_MESSAGES)
    if not exists:
        client.collections.create(
            name=COLLECTION_MESSAGES,
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(
                model=EMBEDDING_MODEL
            ),
            properties=[
                wvc.config.Property(name="session_id", data_type=wvc.config.DataType.UUID),
                wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="role", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
            ]
        )
        print("🙌🏼 Collection Messages created successfully")
    exists = client.collections.exists(COLLECTION_SECTIONS)
    if not exists:
        client.collections.create(
            name=COLLECTION_SECTIONS,
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(
                model=EMBEDDING_MODEL
            ),
            properties=[
                wvc.config.Property(name="title", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="order", data_type=wvc.config.DataType.INT),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="updated_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="author", data_type=wvc.config.DataType.TEXT),
            ]
        )
        print("🙌🏼 Collection Sections created successfully")
    exists = client.collections.exists(COLLECTION_USERS)
    if not exists:
        client.collections.create(
            name=COLLECTION_USERS,
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(
                model=EMBEDDING_MODEL
            ),
            properties=[
                wvc.config.Property(name="email", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="password", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="name", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="updated_at", data_type=wvc.config.DataType.DATE), 
            ]
        )
        print("🙌🏼 Collection Users created successfully")
    exists = client.collections.exists(COLLECTION_FILES)
    if not exists:
        client.collections.create(
            name=COLLECTION_FILES,
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(
                model=EMBEDDING_MODEL
            ),
            properties=[
                wvc.config.Property(name="name", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="path", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="updated_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="author", data_type=wvc.config.DataType.TEXT),
            ]
        )
        print("🙌🏼 Collection Files created successfully")
    print("🙌🏼 Schema initialized successfully")

def upload_documents(documents: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Upload documents to Weaviate.
    
    Args:
        documents: List of dictionaries containing 'title' and 'content' keys
    
    Returns:
        Response from Weaviate
    """
    data_objects = []
    
    for doc in documents:
        data_objects.append({
            "title": doc["title"],
            "content": doc["content"],
            "description": doc["description"],
            "author": doc["author"],
            "file_id": doc["file_id"],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        })
    
    # response = 
    collection = client.collections.get(COLLECTION_DOCUMENTS)

    with collection.batch.fixed_size(batch_size=200) as batch:
        for data_object in data_objects:
            batch.add_object(
                properties=data_object,
            )
            if batch.number_errors > 10:
                print("Batch import stopped due to excessive errors.")
                break
    failed_objects = collection.batch.failed_objects
    if failed_objects:
        print(f"Number of failed imports: {len(failed_objects)}")
        print(f"First failed object: {failed_objects[0]}")

    
    return failed_objects

def search_documents(query: str, limit: int = 3) -> list[dict]:
    """
    Search for relevant documents using vector similarity.

    Args:
        query: Search query string
        limit: Maximum number of results to return

    Returns:
        List of matching documents
    """
    collection = client.collections.get(COLLECTION_DOCUMENTS)
    response = collection.query.near_text(
        query=query,
        limit=limit,
        certainty=0.7,
        
    )
    # Each object in response.objects contains .properties with your fields
    return [obj.properties for obj in response.objects]

def search_non_vector_collection(
    collection_name: str,
    limit: int = 100,
    properties: List[str] = [],
    filters: Optional[_Filters] = None,
    offset: Optional[int] = None,
    sort: Optional[Sorting] = None,
) -> list[dict]:
    """
    For non vector search, use this function.
    Search for relevant collection.

    Args:
        collection_name: Name of the collection to search
        limit: Maximum number of results to return
        properties: List of properties to return
        filters: Filters to apply to the search
        offset: Offset to start from
        sort: Sorting to apply to the search

    Returns:
        List of matching collection
    """
    collection = client.collections.get(collection_name)
    response = collection.query.fetch_objects(
        limit=limit,
        return_properties=properties,
        filters=filters,
        offset=offset,
        sort=sort,
    )
    # Each object in response.objects contains .properties with your fields, and uuid
    return [{"uuid": obj.uuid, **obj.properties} for obj in response.objects]


def search_vector_collection(
    collection_name: str,
    query: str,
    limit: int = 3,
    properties: List[str] = [],
    filters: Optional[_Filters] = None,
    offset: Optional[int] = None,
    sort: Optional[Sorting] = None,
) -> list[dict]:
    """
    Search for relevant collection using vector similarity.

    Args:
        collection_name: Name of the collection to search
        query: Search query string
        limit: Maximum number of results to return
        properties: List of properties to return
        filters: Filters to apply to the search 
        offset: Offset to start from
        sort: Sorting to apply to the search

    Returns:
        List of matching collection
    """
    collection = client.collections.get(collection_name)
    response = collection.query.near_text(
        query=query,
        limit=limit,
        return_properties=properties,
        filters=filters,
        offset=offset,
        sort=sort,
    )
    # Each object in response.objects contains .properties with your fields
    return [obj.properties for obj in response.objects]

T = TypeVar('T', bound=Dict[str, Any])

def insert_to_collection(
    collection_name: str,
    properties: T,
    uuid: Optional[str] = None
) -> str:
    # Get the collection
    collection = client.collections.get(collection_name)

    # Insert a single object
    if uuid:
        uuid = collection.data.insert(properties=properties, uuid=uuid)
    else:
        uuid = collection.data.insert(properties=properties)

    return uuid

def insert_to_collection_in_batch(
    collection_name: str,
    properties: List[T]
) -> List[str]:
    # Get the collection
    collection = client.collections.get(collection_name)
    # Insert a single object
    uuids = collection.data.insert_many(properties)
    return uuids



def update_collection_object(
    collection_name: str,
    uuid: str,
    properties: T
) -> bool:
    # Get the collection
    collection = client.collections.get(collection_name)
    # Update a single object
    collection.data.update(properties=properties, uuid=uuid)
    return True

def delete_collection_object(
    collection_name: str,
    uuid: str
) -> str:
    # Get the collection
    collection = client.collections.get(collection_name)
    # Delete a single object
    collection.data.delete_by_id(uuid)
    return uuid

def delete_collection_objects_many(
    collection_name: str,
    filters: Optional[_Filters] = None
) -> bool:
    # Get the collection
    collection = client.collections.get(collection_name)
    # Delete a single object
    collection.data.delete_many(where=filters)
    return True
