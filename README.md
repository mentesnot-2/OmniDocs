# OmniDocs

**Universal, Scalable Retrieval-Augmented Generation for Multi-Format Documents**

OmniDocs is a production-grade Retrieval-Augmented Generation (RAG) system designed to ingest, understand, and retrieve knowledge from any document type, including PDF, DOCX, PPTX, XLSX, CSV, HTML, Markdown, and plain text.

Built with enterprise architecture principles, OmniDocs provides a modular, extensible pipeline for document ingestion, semantic indexing, and grounded question-answering using modern Large Language Models (LLMs). The system is designed to scale from local prototypes to enterprise deployments while maintaining accuracy, traceability, and security.

---

## ✨ Key Capabilities

- **Universal Document Ingestion** — Seamlessly processes PDFs, Word documents, PowerPoint presentations, Excel spreadsheets, and more.
- **Robust Text Extraction & Normalization** — Uses trusted, industry-proven parsing libraries to reliably extract and standardize content.
- **Semantic Chunking & Embeddings** — Optimized chunking strategies combined with state-of-the-art embedding models for high-quality retrieval.
- **Vector-Based Retrieval** — Fast and accurate similarity search using modern vector databases with full metadata support.
- **Grounded, Explainable AI Responses** — Answers are strictly generated from retrieved context, minimizing hallucinations and enabling source traceability.
- **Production-Ready Architecture** — Modular design, clean code, error handling, logging, and testability built in from day one.
- **Extensible & Model-Agnostic** — Easily swap embedding models, vector stores, or LLM providers without re-architecting the system.

---

## 🎯 Use Cases

- Enterprise document search and Q&A
- Internal knowledge bases
- Financial, legal, and technical document analysis
- AI copilots for large document repositories
- Multi-format research assistants

---

## 🏗️ Design Philosophy

OmniDocs is built with the assumption that it will be used in real production environments, not as a demo or proof-of-concept. The project emphasizes:

- Separation of concerns
- Maintainability and scalability
- Security and reliability
- Clear documentation and traceability


---

## 🚀 Setup

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)

### Backend

# Clone and enter project
cd OmniDocs

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env in project root (see Environment below)
# Start API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

