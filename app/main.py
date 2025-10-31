from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from .services.rag_service import RAGService
from .services.document_service import DocumentService

app = FastAPI(title="FinBot Chat", description="Finance Domain Assistant with RAG")

# CORS middleware for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web UI
app.mount("/static", StaticFiles(directory="web"), name="static")

# Initialize services
rag_service = RAGService()
document_service = DocumentService()

class QueryRequest(BaseModel):
    question: str
    max_results: int = 3

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float

@app.get("/")
async def serve_ui():
    return FileResponse("web/index.html")

@app.post("/api/query", response_model=QueryResponse)
async def query_finbot(request: QueryRequest):
    try:
        result = await rag_service.query(request.question, request.max_results)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/add-url")
async def add_document_from_url(url: str):
    try:
        result = await document_service.add_from_url(url)
        return {"message": "Document added successfully", "chunks": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "FinBot Chat"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)