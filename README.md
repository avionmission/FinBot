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
- **LLM**: Google Gemini Pro
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Document Processing**: BeautifulSoup, requests

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone https://github.com/avionmission/FinBot
   cd finbot-chat
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python -m app.main
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Open your browser and configure**:
   - Navigate to `http://localhost:8000`
   - In the Settings panel, enter your Google Gemini API key
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Click "Save API Key" to start using the bot

   **Alternative**: You can also create a `.env` file with your API key:
   ```bash
   GOOGLE_API_KEY="your_api_key_here"
   FAISS_INDEX_PATH=./data/faiss_index
   DOCUMENTS_PATH=./data/documents
   ```

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
│   ├── main.py              # FastAPI application
│   └── services/
│       ├── rag_service.py   # RAG implementation
│       └── document_service.py  # Document processing
├── web/
│   ├── index.html          # Web UI
│   ├── style.css           # Styling
│   └── script.js           # Frontend logic
├── data/                   # Vector store data (auto-created)
├── requirements.txt
├── .env                    # Environment configuration
└── README.md
```

## Configuration

### Environment Variables
- `GOOGLE_API_KEY`: Your Google Gemini API key (get it from Google AI Studio)
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

# Check if the server is running
curl http://localhost:8000/api/health
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

## Troubleshooting

### Installation Issues
If you encounter dependency installation errors:
```bash
# Make sure you're in a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip first
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### API Key Issues
- Enter your API key in the Settings panel on the web interface, or
- Create a `.env` file with `GOOGLE_API_KEY="your_key_here"`
- Get your key from: https://makersuite.google.com/app/apikey
- Ensure the key has proper permissions for Gemini API

### Common Errors
- **"GOOGLE_API_KEY not set"**: Enter your API key in the Settings panel or create a `.env` file
- **"Module not found"**: Make sure virtual environment is activated
- **Port already in use**: Use a different port with `--port 8001` or kill existing process
- **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details