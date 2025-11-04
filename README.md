# FinBot Chat 🤖

AI-powered finance assistant with RAG (Retrieval-Augmented Generation). Upload documents, ask questions, get intelligent answers.

## Tech Stack

- **Backend**: FastAPI, LangChain, FAISS
- **LLM**: Google Gemini Pro
- **Frontend**: Vanilla HTML/CSS/JS
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **Document Processing**: PyPDF2, BeautifulSoup

## Features

- **Session-based isolation** - Each browser session has its own knowledge base
- **Document upload** - PDF, Excel, text files + URL ingestion  
- **Privacy-first** - API keys stored locally in browser only
- **Real-time chat** - Clean, responsive web interface
- **Semantic search** - FAISS vector database with sentence transformers

## Quick Start

```bash
# Setup
git clone <your-repo>
cd finbot-chat
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python -m app.main
```

Open `http://localhost:8000`, enter your [Gemini API key](https://makersuite.google.com/app/apikey), and start chatting!

## API Endpoints

- `GET /` - Serve web UI
- `POST /api/query` - Query the FinBot with session isolation
- `POST /api/documents/upload` - Upload PDF/Excel/text files
- `POST /api/documents/add-url` - Add document from URL
- `GET /api/documents` - List uploaded documents for session
- `GET /api/health` - Health check

## Project Structure

```
finbot-chat/
├── app/
│   ├── main.py              # FastAPI application
│   └── services/
│       ├── rag_service.py   # RAG implementation with session isolation
│       └── document_service.py  # Document processing
├── web/
│   ├── index.html          # Web UI
│   ├── style.css           # Styling
│   ├── script.js           # Frontend logic
│   └── favicon.ico         # Site icon
├── requirements.txt
├── Procfile               # For deployment
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request