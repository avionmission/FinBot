from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
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

# Initialize services
rag_service = RAGService()
document_service = DocumentService()

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
async def query_finbot(request: QueryRequest):
    try:
        if not request.api_key:
            raise HTTPException(status_code=400, detail="Gemini API key is required")
        
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
async def add_document_from_url(request: AddUrlRequest):
    try:
        # Validate URL format
        if not request.url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
        
        result = await document_service.add_from_url(request.url)
        return {"message": "Document added successfully", "chunks": result}
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
async def upload_document(file: UploadFile = File(...)):
    try:
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
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")
        
        # Process the file
        result = await document_service.add_from_file(file_content, file.filename, file.content_type)
        
        return {
            "message": f"File '{file.filename}' uploaded successfully",
            "chunks": result,
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "unsupported" in error_msg.lower() or "failed to extract" in error_msg.lower():
            raise HTTPException(status_code=400, detail=f"Failed to process file: {error_msg}")
        else:
            raise HTTPException(status_code=500, detail=f"Internal error: {error_msg}")

@app.get("/api/documents")
async def get_documents():
    try:
        documents = document_service.get_document_sources()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/chunks")
async def debug_chunks():
    """Debug endpoint to see what chunks are stored in the vector database"""
    try:
        chunks_info = []
        for i, doc in enumerate(rag_service.documents_metadata):
            chunks_info.append({
                "index": i,
                "source": doc["source"],
                "text_preview": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                "text_length": len(doc["text"])
            })
        
        return {
            "total_chunks": len(chunks_info),
            "chunks": chunks_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "FinBot Chat"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)