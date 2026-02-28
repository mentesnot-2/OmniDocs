"""
Text chunking with token-based splitting and overlap.
"""

from typing import List
from dataclasses import dataclass
import tiktoken
from config import CHUNK_OVERLAP, CHUNK_SIZE

@dataclass
class Chunk:
    """A chunk of text with metadata."""
    text: str
    chunk_index:int
    source_file:str
    metadata:dict

def chunk_text(
    text:str,
    source_file:str,
    metadata:dict = None,
    chunk_size:int = CHUNK_SIZE,
    chunk_overlap:int = CHUNK_OVERLAP,
) -> List[Chunk]:
    """ 
    Split text into overlapping chunks based on token count.
    Args:
        text: The text to chunk.
        source_file: The source file of the text.
        metadata: Additional metadata to include in the chunks.
        chunk_size: The maximum number of tokens per chunk.
        chunk_overlap: The number of tokens to overlap between chunks.
    Returns:
        A list of Chunk objects.
    """
    if not text or not text.strip():
        return []
    metadata = metadata or {}
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)

    chunks = []
    start = 0
    chunk_index = 0
    with start < len(tokens):

        # Get chunk tokens
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)

        # Create chunk with metadata
        chunk = Chunk(
            text=chunk_text,
            chunk_index=chunk_index,
            source_file=source_file,
            metadata={
                **metadata,
                "start_token": start,
                "end_token":min(end,len(tokens)),
                "total_tokens":len(chunk_tokens),
            },
        )

        chunks.append(chunk)

        # Move to next chunk with overlap
        start+=chunk_size - chunk_overlap
        chunk_index+=1
    return chunks
def chunk_document(parsed_doc) -> List[Chunk]:
    """
    Chunk a parsed document into overlapping chunks.
    Args:
        parsed_doc: A ParsedDocument object.
    Returns:
        A list of Chunk objects.
    """
    return chunk_text(
        text=parsed_doc.content,
        source_file=parsed_doc.source_file,
        metadata=parsed_doc.metadata,
    )