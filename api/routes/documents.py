"""Documents routes (upload, query)"""

from pathlib import Path
from typing import List
from pydantic import BaseModel
from retrieval import Retriever
from generation import AnswerGenerator
from config import TOP_K


class QueryRequest(BaseModel):
    question:str
    top_k:int  | None = None


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
    with open(dest_path, "wb") as f:
        f.write(content)
    # Ingest, chunk, embed, and store

    try:
        parsed = ingest_document(dest_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse document: {str(e)}",
        )

    if not parsed.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is empty or contains no text.",
        )
    
    chunks = chunk_document(parsed)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No chunks produced from document.",
        )
    texts = [c.text for c in chunks]
    gen = EmbeddingGenerator()
    embeddings = gen.embed_batch(texts)

    store = ChromaVectorStore()
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
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
    )
    return {
        "answer":response.answer,
        "sources":source_files,
        "refused":response.refused
    }