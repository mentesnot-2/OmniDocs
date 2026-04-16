"""
OmniDocs RAG - Main entry point
Run: python main.py index <file_or_dir>
or python main.py query <question>
"""
import sys
from pathlib import Path

# Ensure project root is in path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import ensure_dirs,TOP_K
from ingestion import ingest_document,get_supported_extensions
from chunking import chunk_document
from embeddings import EmbeddingGenerator
from vectorstore import ChromaVectorStore
from retrieval import Retriever
from generation import AnswerGenerator

CLI_USER_ID = "cli"

def index_documents(
    file_path: Path,
    store: ChromaVectorStore,
    gen: EmbeddingGenerator,
    user_id: str = CLI_USER_ID,
):
    """Ingest, chunk, embed, and store a single document."""
    print(f"\nIndexing: {file_path.name}")

    # Ingest
    parsed = ingest_document(file_path)
    if not parsed.content.strip():
        print(f" Skipped (empty content): {file_path.name}")
        return
    
    # Chunk 
    chunks = chunk_document(parsed)
    print(f" Chunks: {len(chunks)}")

    if not chunks:
        return

    # Prepare for storage
    texts = [c.text for c in chunks]
    embeddings = gen.embed_batch(texts)
    metadata = [
        {
            "source_file": c.source_file,
            "chunk_index":c.chunk_index,
            "user_id": user_id,
            **{k:str(v) for k,v in c.metadata.items()}
        }
        for c in chunks
    ]
    store.add_chunks(texts,embeddings,metadata)
    print(f" Done: {file_path.name}")

def index_mode(path_arg:str):
    """Index document(s)"""

    ensure_dirs()
    
    path = Path(path_arg)
    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        return 1
    store = ChromaVectorStore()
    gen = EmbeddingGenerator()

    extensions = get_supported_extensions()
    if path.is_file():
        if path.suffix.lower() in extensions:
            index_documents(path,store,gen)
        else:
            print(f" Unsupported format: {path.suffix}")
            return 1
    else:
        for ext in extensions:
            for fp in path.rglob(f"*{ext}"):
                index_documents(fp,store,gen)
    print("\nIndexing completed")
    print(f"Vectore store stats: {store.get_stats()}")
    return 0

def query_mode(question:str):
    """Answer a question based on indexed documents"""

    retriever = Retriever()
    result = retriever.retrieve_with_context(question,top_k=TOP_K)

    if result["num_results"] == 0:
        print("No relevant documents found. documents first.")
        print(" Python main.py index <file_or_dir>")
        return 1
    
    # Generate answer
    try:
        gen = AnswerGenerator()
        source_files = list(set(r.source_file for r in result["chunks"]))
        response = gen.generate(
            query=result["query"],
            context_text=result["context_text"],
            source_files=source_files,
        )
        print("\n--- answer ---")
        print(response.answer)
        print("\n--- sources ---")
        for f in response.source_used:
            print(f"- {f}")
    except Exception as e:
        print(f"Error generating answer: {e}")
        print("Ensure OPENAI_API_KEY is set in .env file")
        return 1
    return 0

def main():

    if len(sys.argv) < 2:
        print("Usage:")
        print(" python main.py index <file_or_dir>")
        print(" python main.py query \"Your question\"")
        print("\nSupported formats: ", ", ".join(get_supported_extensions()))
        return 1
    command = sys.argv[1]
    if command == "index":
        if len(sys.argv) < 3:
            print("Usage: python main.py index <file_or_dir>")
            return 1
        return index_mode(sys.argv[2])
    elif command == "query":
        if len(sys.argv) < 3:
            print("Usage: python main.py query \"Your question\"")
            return 1
        question = " ".join(sys.argv[2:])
        return query_mode(question)

    else:
        print(f"Unknown command: {command}")
        print("Usage:")
        print(" python main.py index <file_or_dir>")
        print(" python main.py query \"Your question\"")
        print("\nSupported formats: ", ", ".join(get_supported_extensions()))
        return 1
    
if __name__ == "__main__":
    sys.exit(main())