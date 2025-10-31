# FinBot Chat 🏦

A domain-specific AI assistant for finance that answers customer queries using RAG (Retrieval-Augmented Generation). Built with Python, LangChain, FastAPI, and FAISS for semantic search.

## Features

- **RAG-powered responses**: Combines retrieval and generation for accurate, context-aware answers
- **Semantic search**: Uses FAISS vector database for efficient document retrieval
- **Web-based UI**: Clean, responsive interface for easy interaction
- **Document ingestion**: Add financial documents from URLs to expand knowledge base
- **Real-time chat**: FastAPI backend with WebSocket-like experience
- **Pre-loaded FAQs**: Comes with common banking and financial questions

## Tech Stack

- **Backend**: Python, FastAPI, LangChain
- **Vector Database**: FAISS
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **LLM**: OpenAI GPT (configurable)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Document Processing**: BeautifulSoup, requests

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd finbot-chat
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run the application**:
   ```bash
   python -m app.main
   ```

4. **Open your browser**:
   Navigate to `http://localhost:8000`

## API Endpoints

- `GET /` - Serve web UI
- `POST /api/query` - Query the FinBot
- `POST /api/documents/add-url` - Add document from URL
- `GET /api/health` - Health check

## Usage Examples

### Chat Interface
Ask questions like:
- "What is a savings account?"
- "How do I apply for a credit card?"
- "What are the fees for wire transfers?"

### Adding Documents
Use the sidebar to add financial documents from URLs:
- Bank policy pages
- Financial education articles
- FAQ pages
- Investment guides

## Project Structure

```
finbot-chat/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   └── services/
│       ├── __init__.py
│       ├── rag_service.py   # RAG implementation
│       └── document_service.py  # Document processing
├── web/
│   ├── index.html          # Web UI
│   ├── style.css           # Styling
│   └── script.js           # Frontend logic
├── data/                   # Vector store data (auto-created)
├── requirements.txt
├── .env.example
└── README.md
```

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `FAISS_INDEX_PATH`: Path to FAISS index files (default: ./data/faiss_index)
- `DOCUMENTS_PATH`: Path to document storage (default: ./data/documents)

### Customization
- Modify `rag_service.py` to use different embedding models
- Update `_create_sample_index()` to include your specific financial FAQs
- Adjust chunk size and overlap in `document_service.py`

## Development

### Adding New Features
1. **Custom document types**: Extend `DocumentService` for PDF, Word docs
2. **Authentication**: Add user management and session handling
3. **Analytics**: Track query patterns and user interactions
4. **Multi-language**: Support for different languages

### Testing
```bash
# Test the API directly
curl -X POST "http://localhost:8000/api/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is compound interest?"}'
```

## Deployment

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "app.main"]
```

### Production Considerations
- Use a production ASGI server like Gunicorn
- Set up proper logging and monitoring
- Configure CORS for your domain
- Use environment-specific configurations
- Consider using a more robust vector database for scale

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details