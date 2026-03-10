"""Documents routes (upload, query)"""

from api.utils.logging_config import logger
from pathlib import Path
from typing import List
from pydantic import BaseModel
from retrieval import Retriever
from generation import AnswerGenerator
from config import TOP_K, MAX_FILE_SIZE


class QueryRequest(BaseModel):
    question:str
    top_k:int  | None = None
    message_history:List[dict] | None = None # List of messages in the conversation
    session_id:int | None = None # ID of the chat session to use

class MessagePair(BaseModel):
    question:str
    answer:str


from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_current_user
from api.models import User
from ingestion import ingest_document
from chunking import chunk_document
from embeddings import EmbeddingGenerator
from vectorstore import ChromaVectorStore



router = APIRouter(prefix="/documents",tags=["documents"])


@router.get("/")
def get_documents(
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user),
):
    """List all documents uploaded by by the current user."""
    upload_dir = Path("data/uploads") / str(current_user.id)
    if not upload_dir.exists():
        return {"documents":[]}
    files = []
    for f in upload_dir.iterdir():
        if f.is_file():
            files.append({
                "filename":f.name,
                "uploaded_at":f.stat().st_mtime, # unix timestamp
            })

            # Sort by uplaoded_at descending (newest first)
    files.sort(key=lambda x : x["uploaded_at"], reverse=True)
    return {"documents":files}
@router.delete("/{filename}")
def delete_document(
    filename:str,
    db:Session = Depends(get_db),
    current_user: User=Depends(get_current_user),

):
    """Delete a document and its chunks from the vector store."""
    import urllib.parse

    # Decode filename in case it has special characters.
    filename = urllib.parse.unquote(filename)


    # Security: ensure path stays within user's folder
    uploads_dir = Path("data/uploads") / str(current_user.id)
    uploads_dir = uploads_dir.resolve()
    file_path = (uploads_dir / filename).resolve()

    if file_path.parent != uploads_dir:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid filename.",

        )
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found.",
        )
    # Delete from vectore store
    store = ChromaVectorStore()
    store.delete_by_source(filename, str(current_user.id))
    # Delete file from disk
    file_path.unlink()

    return {
        "message": "Document deleted successfully.",
        "filename": filename,
    }
@router.post("/upload")
async def upload(
    file:UploadFile = File(...),
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user),
):
    """Upload document and index it for the current user."""
    # Save uploaded file to disk
    uploads_dir = Path("data/uploads") / str(current_user.id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    dest_path = uploads_dir / file.filename
    
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE:
        logger.error(f"Document {file.filename} is too large. Maximum size is {MAX_FILE_SIZE} MB.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is too large. Maximum size is {MAX_FILE_SIZE} MB.",
        )
    logger.info(f"Document {file.filename} uploaded successfully. Size: {size_mb:.2f} MB.")
    with open(dest_path, "wb") as f:
        f.write(content)
    # Ingest, chunk, embed, and store

    try:
        parsed = ingest_document(dest_path)
        logger.info(f"Document {file.filename} parsed successfully.")
    except Exception as e:
        logger.error(f"Failed to parse document {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse document: {str(e)}",
        )

    if not parsed.content.strip():
        logger.error(f"Document {file.filename} is empty or contains no text.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is empty or contains no text.",
        )
    
    chunks = chunk_document(parsed)
    if not chunks:
        logger.error(f"No chunks produced from document {file.filename}.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No chunks produced from document.",
        )
    texts = [c.text for c in chunks]
    gen = EmbeddingGenerator()
    embeddings = gen.embed_batch(texts)

    store = ChromaVectorStore()
    # Delete old chunks for re-upload (same filename)
    store.delete_by_source(file.filename, str(current_user.id))
    metadatas = [
        {
            "source_file": c.source_file,
            "chunk_index": c.chunk_index,
            "user_id": str(current_user.id),
            **{k: str(v) for k,v in c.metadata.items()}
        }
        for c in chunks
    ]
    store.add_chunks(texts, embeddings, metadatas)

   

    return {
        "message": "Document uploaded and indexed successfully.",
        "file_name": file.filename,
        "chunk_indexed": len(chunks),
    }


@router.post("/query")
def query(
    body:QueryRequest,
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user),
):
    """Answer a question based only on the current user's documents."""
    question = body.question.strip()
    if not question:
        logger.error("Question cannot be empty.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )
    MAX_QUESTION_LEN = 2000
    if len(question) > MAX_QUESTION_LEN:
        logger.error(f"Question is too long. Maximum length is {MAX_QUESTION_LEN} characters.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question is too long. Maximum length is {MAX_QUESTION_LEN} characters.",
        )
    retriever = Retriever()
    result = retriever.retrieve_with_context(
        question,
        top_k=body.top_k or TOP_K,
        user_id=str(current_user.id),
    )

    if result["num_results"] == 0:
        return {
            "answer":"I cannot answer because no relevant documents were found for this user.",
            "sources": [],
        }

    gen = AnswerGenerator()
    source_files = list({r.source_file for r in result["chunks"]})
    response = gen.generate(
        query=result["query"],
        context_text=result["context_text"],
        source_files=source_files,
        message_history=body.message_history,
    )
    return {
        "answer":response.answer,
        "sources":source_files,
        "refused":response.refused
    }