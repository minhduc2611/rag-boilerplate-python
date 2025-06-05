from libs.pdf_lib import process_pdf, read_pdf_from_buffer, allowed_file
from flask import jsonify
from werkzeug.datastructures import FileStorage
from typing import List

def upload_file(files: List[FileStorage], description: str) -> List[dict]:
    if not files:
        raise Exception("No files uploaded")

    results = []
    for file in files:
        if not allowed_file(file.filename):
            raise Exception(f"File type not allowed for {file.filename}. Only PDF files are accepted.")

        # Read PDF content from buffer
        pdf_content = read_pdf_from_buffer(file)
        
        # Process the PDF content
        chunks = process_pdf(
            text=pdf_content,
        )
        
        # Convert chunks to a serializable format
        serialized_chunks = [
            {
                "content": chunk.page_content,
                "metadata": chunk.metadata
            }
            for chunk in chunks
        ]
        
        results.append({
            "filename": file.filename,
            "num_chunks": len(chunks),
            "chunks": serialized_chunks
        })
    return results