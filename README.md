```
agentic_rag_backend/
│
├── app/                            # Main FastAPI app
│   ├── main.py                     # FastAPI entrypoint
│   └── api/
│       └── v1/
│           └── routes.py          # `/hackrx/run` route
│
├── core/                           # Core config & startup
│   ├── config.py                  # Env + App settings
│   └── logger.py                  # Logging setup
│
├── services/                       # Modular logic layer
│   ├── document_loader.py         # Load & split PDF/DOCX/email
│   ├── vector_store.py            # Pinecone index wrapper
│   ├── agent_executor.py          # LangChain agent logic
│   ├── clause_matcher.py          # Semantic similarity + clause logic
│   └── response_builder.py        # JSON structuring & reasoning
│
├── chains/                         # LangChain chains & prompts
│   ├── qa_chain.py                # Gemini prompt + chain
│   └── prompts/
│       ├── rag_prompt.txt
│       └── rationale_prompt.txt
│
├── tools/                          # Custom LangChain tools (optional)
│   └── semantic_search_tool.py    # Agent tool wrapper for retrieval
│
├── models/                         # Pydantic models
│   └── request_response.py        # Request/response schemas
│
├── utils/                          # Utility scripts/helpers
│   ├── file_downloader.py
│   ├── text_cleaner.py
│   └── chunking.py
│
├── .env                            # Environment variables
├── requirements.txt                # Python dependencies
└── README.md

```

```
🏗️ Complete Modular Backend Architecture
Key Components Implemented:

🚀 FastAPI Application Layer

Main FastAPI app with CORS support
Bearer token authentication
Health check endpoints
Structured error handling


⚙️ Core Infrastructure

Configuration management with environment variables
Advanced logging setup with Loguru (console + file rotation)
Settings validation with Pydantic


🔧 Service Layer (Modular Design)

DocumentLoader: Downloads and processes PDF/DOCX/email files
VectorStoreManager: Handles Pinecone operations with async support
AgentExecutor: LangChain agent orchestration with custom tools
ClauseMatcher: Semantic similarity matching with TF-IDF
ResponseBuilder: Structures JSON responses


🧠 LangChain Integration

QA Chain with custom prompts for policy analysis
Custom tools for semantic search and clause matching
Gemini Pro integration with proper error handling


🛠️ Advanced Utilities

Async file downloader with content-type detection
Text cleaner with policy-specific preprocessing
Smart chunking with token counting and section identification



🎯 Key Features:

Async Processing: Full async/await support for better performance
Error Resilience: Comprehensive error handling with graceful degradation
Smart Chunking: Policy-aware document splitting for optimal retrieval
Vector Search: Pinecone integration with similarity thresholds
Modular Design: Clean separation of concerns for easy maintenance
Production Ready: Logging, monitoring, and cleanup operations

📋 API Endpoint:
POST /api/v1/hackrx/run
Authorization: Bearer 8b19aa4e64ea7d5aa15448e401460637d5d9ba07e3a839ae961d745fb0910de3
The system processes your exact workflow:

Downloads document from blob URL
Creates embeddings and stores in Pinecone
Uses LangChain agents with Gemini for question answering
Returns structured JSON responses
Performs background cleanup

🚦 Next Steps:

Setup Environment: Add your API keys to .env
Install Dependencies: pip install -r requirements.txt
Run Application: python app/main.py
Test API: Use the provided sample requests

The backend is designed to handle your insurance policy document analysis with 10 questions and return precise answers as shown in your sample response format. Everything is modular, scalable, and production-ready!


```

# README.md
# Agentic RAG Backend

A modular backend system for Retrieval-Augmented Generation (RAG) using LangChain, Pinecone, and Google Gemini API.

## Features

- 🔍 **Document Processing**: Supports PDF, DOCX, and email formats
- 🧠 **Vector Search**: Pinecone integration for semantic similarity search
- 🤖 **LLM Integration**: Google Gemini Pro for intelligent question answering
- 🔧 **Modular Architecture**: Clean separation of concerns with service layers
- 🚀 **FastAPI**: High-performance async API with automatic documentation
- 📊 **Advanced Chunking**: Smart document splitting for optimal retrieval
- 🛠️ **Agent Framework**: LangChain agents with custom tools

## Quick Start

### Prerequisites

- Python 3.10+
- Google API Key (for Gemini)
- Pinecone API Key and Environment

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agentic_rag_backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the application:
```bash
python app/main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

### Authentication

All API endpoints require Bearer token authentication:

```
Authorization: Bearer 8b19aa4e64ea7d5aa15448e401460637d5d9ba07e3a839ae961d745fb0910de3
```

### Endpoints

#### POST `/api/v1/hackrx/run`

Process documents and answer questions using RAG pipeline.

**Request Body:**
```json
{
    "documents": "https://example.com/document.pdf",
    "questions": [
        "What is the waiting period?",
        "What are the coverage limits?"
    ]
}
```

**Response:**
```json
{
    "answers": [
        "The waiting period is 36 months for pre-existing conditions.",
        "Coverage is limited to $100,000 per year with 20% co-pay."
    ]
}
```

## Architecture

### Service Layer

- **DocumentLoader**: Handles document download and parsing
- **VectorStoreManager**: Manages Pinecone operations and embeddings
- **AgentExecutor**: Orchestrates LangChain agents and tools
- **ClauseMatcher**: Provides semantic similarity matching
- **ResponseBuilder**: Formats structured responses

### Chains

- **QAChain**: Question-answering chain with custom prompts
- **Custom Tools**: Semantic search and clause matching tools

### Utilities

- **FileDownloader**: Async file downloading
- **TextCleaner**: Text preprocessing and cleaning
- **AdvancedChunker**: Smart document chunking strategies

## Configuration

Key configuration options in `core/config.py`:

- `CHUNK_SIZE`: Document chunk size (default: 1000)
- `TOP_K_RESULTS`: Number of search results (default: 5)
- `SIMILARITY_THRESHOLD`: Minimum similarity score (default: 0.7)
- `VECTOR_DIMENSION`: Embedding dimensions (default: 768)

## Logging

The application uses structured logging with Loguru:

- Console output with colored formatting
- File rotation (10MB files, 10 days retention)
- Configurable log levels

## Error Handling

Comprehensive error handling with:

- Graceful degradation for failed operations
- Detailed error messages and logging
- Background cleanup for vector store operations

## Development

### Project Structure

```
agentic_rag_backend/
├── app/                 # FastAPI application
├── core/               # Configuration and logging
├── services/           # Business logic layer
├── chains/             # LangChain chains and prompts
├── models/             # Pydantic schemas
├── utils/              # Utility functions
└── requirements.txt    # Dependencies
```

### Testing

Run the application locally and test with curl:

```bash
curl -X POST "http://localhost:8000/api/v1/hackrx/run" \
  -H "Authorization: Bearer 8b19aa4e64ea7d5aa15448e401460637d5d9ba07e3a839ae961d745fb0910de3" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": "https://example.com/policy.pdf",
    "questions": ["What is covered under this policy?"]
  }'
```

## Production Deployment

For production deployment:

1. Set appropriate environment variables
2. Use a production WSGI server like Gunicorn
3. Configure proper logging and monitoring
4. Set up health checks and load balancing
5. Use environment-specific Pinecone indexes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.