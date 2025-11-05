from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import uuid
from typing import Optional
from .services.rag_service import RAGService
from .services.document_service import DocumentService

app = FastAPI(title="FinBot Chat", description="Finance Domain Assistant with RAG")

# Configure CORS for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static web files
app.mount("/static", StaticFiles(directory="web"), name="static")



def get_session_id(x_session_id: Optional[str] = Header(None)) -> str:
    """Get or create session ID"""
    if x_session_id:
        return x_session_id
    return str(uuid.uuid4())

class QueryRequest(BaseModel):
    question: str
    api_key: str
    max_results: int = 3

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float

class AddUrlRequest(BaseModel):
    url: str

@app.get("/")
async def serve_ui():
    return FileResponse("web/index.html")

@app.post("/api/query", response_model=QueryResponse)
async def query_finbot(request: QueryRequest, session_id: Optional[str] = Header(None, alias="x-session-id")):
    try:
        if not request.api_key:
            raise HTTPException(status_code=400, detail="Gemini API key is required")
        
        # Use session-specific RAG service or create new session
        if not session_id:
            session_id = str(uuid.uuid4())
        rag_service = RAGService(session_id)
        result = await rag_service.query(request.question, request.api_key, request.max_results)
        return QueryResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg:
            raise HTTPException(status_code=400, detail="Invalid API key. Please check your Gemini API key.")
        else:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/add-url")
async def add_document_from_url(request: AddUrlRequest, session_id: Optional[str] = Header(None, alias="x-session-id")):
    try:
        # Validate URL format
        if not request.url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
        
        # Use session-specific document service or create new session
        if not session_id:
            session_id = str(uuid.uuid4())
        document_service = DocumentService(session_id)
        result = await document_service.add_from_url(request.url)
        return {"message": "Document added successfully", "chunks": result, "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "460" in error_msg:
            raise HTTPException(status_code=400, detail="Website blocked the request. Try a different URL or check if the site allows automated access.")
        elif "404" in error_msg:
            raise HTTPException(status_code=400, detail="URL not found. Please check the URL and try again.")
        elif "timeout" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Request timed out. The website may be slow or unavailable.")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to process document: {error_msg}")

@app.post("/api/documents/upload")
async def upload_document(request: Request, file: UploadFile = File(...), session_id: Optional[str] = Header(None, alias="x-session-id")):
    try:
        # Debug: Print all headers
        print(f"[UPLOAD] All headers: {dict(request.headers)}")
        print(f"[UPLOAD] Received file: {file.filename}, Session ID: {session_id}")
        
        # Validate file type
        allowed_types = [
            "application/pdf",
            "application/vnd.ms-excel", 
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/plain"
        ]
        
        if file.content_type not in allowed_types and not any(file.filename.lower().endswith(ext) for ext in ['.pdf', '.xlsx', '.xls', '.txt']):
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF, Excel, or TXT files.")
        
        # Read file content
        file_content = await file.read()
        print(f"[UPLOAD] File size: {len(file_content)} bytes")
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")
        
        # Use session-specific document service or create new session
        if not session_id:
            session_id = str(uuid.uuid4())
            print(f"[UPLOAD] Generated new session ID: {session_id}")
        
        document_service = DocumentService(session_id)
        result = await document_service.add_from_file(file_content, file.filename, file.content_type)
        print(f"[UPLOAD] Added {result} chunks to session {session_id}")
        
        # Verify the chunks were added
        from .services.rag_service import SESSION_STORES
        if session_id in SESSION_STORES:
            doc_count = len(SESSION_STORES[session_id]['documents_metadata'])
            print(f"[UPLOAD] Session {session_id} now has {doc_count} total documents")
        
        return {
            "message": f"File '{file.filename}' uploaded successfully",
            "chunks": result,
            "filename": file.filename,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[UPLOAD ERROR] {str(e)}")
        error_msg = str(e)
        if "unsupported" in error_msg.lower() or "failed to extract" in error_msg.lower():
            raise HTTPException(status_code=400, detail=f"Failed to process file: {error_msg}")
        else:
            raise HTTPException(status_code=500, detail=f"Internal error: {error_msg}")

@app.get("/api/documents")
async def get_documents(session_id: Optional[str] = Header(None, alias="x-session-id")):
    try:
        print(f"[DOCUMENTS] Loading documents for session: {session_id}")
        
        # Use session-specific document service or create new session
        if not session_id:
            session_id = str(uuid.uuid4())
            print(f"[DOCUMENTS] Generated new session ID: {session_id}")
        
        document_service = DocumentService(session_id)
        documents = document_service.get_document_sources()
        print(f"[DOCUMENTS] Found {len(documents)} documents for session {session_id}")
        
        return {"documents": documents}
    except Exception as e:
        print(f"[DOCUMENTS ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/chunks")
async def debug_chunks(session_id: Optional[str] = Header(None, alias="x-session-id")):
    """Debug endpoint to see what chunks are stored in the session vector database"""
    try:
        # Use session-specific RAG service or create new session
        if not session_id:
            session_id = str(uuid.uuid4())
        rag_service = RAGService(session_id)
        chunks_info = []
        for i, doc in enumerate(rag_service.documents_metadata):
            chunks_info.append({
                "index": i,
                "source": doc["source"],
                "text_preview": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                "text_length": len(doc["text"])
            })
        
        # Import SESSION_STORES to check all sessions
        from .services.rag_service import SESSION_STORES
        
        return {
            "total_chunks": len(chunks_info),
            "chunks": chunks_info,
            "session_id": session_id,
            "all_sessions": list(SESSION_STORES.keys()),
            "session_exists": session_id in SESSION_STORES
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/session/{session_id}")
async def debug_session_info(session_id: str):
    """Debug endpoint to check specific session info"""
    try:
        from .services.rag_service import SESSION_STORES
        
        if session_id not in SESSION_STORES:
            return {
                "session_exists": False,
                "session_id": session_id,
                "all_sessions": list(SESSION_STORES.keys())
            }
        
        session_data = SESSION_STORES[session_id]
        return {
            "session_exists": True,
            "session_id": session_id,
            "initialized": session_data.get('initialized', False),
            "documents_count": len(session_data.get('documents_metadata', [])),
            "has_index": session_data.get('index') is not None,
            "documents": [doc["source"] for doc in session_data.get('documents_metadata', [])]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
async def get_active_sessions():
    """Debug endpoint to see active sessions"""
    return {
        "active_sessions": RAGService.get_active_sessions(),
        "total_sessions": len(RAGService.get_active_sessions())
    }

@app.delete("/api/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear a specific session"""
    RAGService.clear_session(session_id)
    return {"message": f"Session {session_id} cleared"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "FinBot Chat"}

@app.on_event("startup")
async def startup_event():
    """Print startup information"""
    port = os.environ.get("PORT", "8000")
    print(f"🚀 FinBot Chat starting up...")
    print(f"🌐 Server will bind to 0.0.0.0:{port}")
    print(f"📚 Session-based knowledge isolation enabled")
    print(f"✅ Application ready to receive requests")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)