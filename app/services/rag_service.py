import os
import faiss
import numpy as np
from langchain_google_genai import ChatGoogleGenerativeAI
# Direct FAISS usage for vector operations
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import pickle
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Global storage for session-based knowledge bases
SESSION_STORES = {}

class RAGService:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Model preference order for Gemini
        self.models_to_try = [
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-001", 
            "models/gemini-2.5-flash",
            "models/gemini-flash-latest",
            "models/gemini-2.0-flash-lite",
            "models/gemini-2.0-flash-lite-001",
            "models/gemini-flash-lite-latest",
            "models/gemini-2.5-pro",
            "models/gemini-pro-latest"
        ]
        
        # Initialize session-specific storage
        self.init_session_store()
    
    def _get_llm_with_api_key(self, api_key: str):
        """Create LLM instance with provided API key"""
        if not api_key:
            raise ValueError("API key is required")
        
        for model_name in self.models_to_try:
            try:
                return ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=0.7,
                    google_api_key=api_key
                )
            except Exception:
                continue
        
        raise ValueError("Could not initialize any Gemini model. Please check your API key.")
    
    def init_session_store(self):
        """Initialize session-specific storage"""
        if self.session_id not in SESSION_STORES:
            SESSION_STORES[self.session_id] = {
                'index': None,
                'documents_metadata': [],
                'initialized': False
            }
        
        # Create sample index for new sessions
        if not SESSION_STORES[self.session_id]['initialized']:
            self._create_sample_index()
            SESSION_STORES[self.session_id]['initialized'] = True
    
    @property
    def documents_metadata(self):
        """Get documents metadata for current session"""
        return SESSION_STORES[self.session_id]['documents_metadata']
    
    @documents_metadata.setter
    def documents_metadata(self, value):
        """Set documents metadata for current session"""
        SESSION_STORES[self.session_id]['documents_metadata'] = value
    
    @property
    def index(self):
        """Get FAISS index for current session"""
        return SESSION_STORES[self.session_id]['index']
    
    @index.setter
    def index(self, value):
        """Set FAISS index for current session"""
        SESSION_STORES[self.session_id]['index'] = value
    
    def _create_sample_index(self):
        """Create initial in-memory index with sample financial FAQs"""
        sample_docs = [
            "What is a savings account? A savings account is a deposit account that earns interest and provides easy access to your money.",
            "How do I apply for a credit card? You can apply for a credit card online, by phone, or at a branch location.",
            "What is compound interest? Compound interest is interest calculated on the initial principal and accumulated interest.",
            "How do I check my account balance? You can check your balance online, through mobile app, ATM, or by calling customer service.",
            "What are the fees for wire transfers? Domestic wire transfers typically cost $15-30, international transfers cost $35-50.",
            "How do I set up direct deposit? Contact your employer's HR department and provide your bank routing and account numbers.",
            "What is the difference between checking and savings? Checking accounts are for daily transactions, savings accounts earn interest.",
            "How do I report a lost or stolen card? Call the customer service number immediately or use the mobile app to report it.",
            "What is APR? Annual Percentage Rate includes interest rate plus other fees expressed as a yearly rate.",
            "How do I dispute a transaction? Contact customer service within 60 days or use online banking to file a dispute."
        ]
        
        # Create embeddings
        embeddings = self.embeddings.encode(sample_docs)
        
        # Create in-memory FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings.astype('float32'))
        
        # Store in session
        self.index = index
        self.documents_metadata = [{"text": doc, "source": "FAQ"} for doc in sample_docs]
    
    async def query(self, question: str, api_key: str, max_results: int = 3):
        """Process query using RAG with provided API key"""
        # Get query embedding
        query_embedding = self.embeddings.encode([question])
        
        # Search similar documents in session index
        if self.index is None:
            return {
                "answer": "No documents have been added to your knowledge base yet. Please add some documents first.",
                "sources": [],
                "confidence": 0.0
            }
        
        scores, indices = self.index.search(query_embedding.astype('float32'), max_results)
        
        # Get relevant documents
        relevant_docs = []
        sources = []
        
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents_metadata):
                doc = self.documents_metadata[idx]
                relevant_docs.append(doc["text"])
                sources.append(doc["source"])
        
        # Generate context-aware response
        context = "\n".join(relevant_docs)
        
        prompt = f"""
        Based on the following financial information, answer the user's question accurately and helpfully.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer: Provide a clear, accurate response based on the context. If the context doesn't contain enough information, say so.
        """
        
        try:
            # Create LLM instance with provided API key
            llm = self._get_llm_with_api_key(api_key)
            
            # Generate response using Gemini
            response = llm.invoke(prompt)
            
            # Extract content from response
            if hasattr(response, 'content'):
                answer = response.content
            else:
                answer = str(response)
            
            confidence = float(np.mean(scores[0])) if len(scores[0]) > 0 else 0.0
            
            return {
                "answer": answer.strip(),
                "sources": sources,
                "confidence": confidence
            }
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                return {
                    "answer": "I'm currently experiencing high demand and have reached my API quota limit. Please try again in a few minutes. In the meantime, here's what I found in the knowledge base: " + context[:200] + "...",
                    "sources": sources,
                    "confidence": confidence if 'confidence' in locals() else 0.0
                }
            else:
                return {
                    "answer": f"I apologize, but I encountered an error processing your question: {error_msg}",
                    "sources": [],
                    "confidence": 0.0
                }
    
    def add_documents(self, documents: list[str], sources: list[str]):
        """Add new documents to the session index"""
        print(f"[RAG_SERVICE] Adding {len(documents)} documents to session {self.session_id}")
        
        # Create embeddings for new documents
        new_embeddings = self.embeddings.encode(documents)
        print(f"[RAG_SERVICE] Created embeddings shape: {new_embeddings.shape}")
        
        # Add new embeddings to session index
        if self.index is None:
            # Create new index if none exists
            dimension = new_embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            print(f"[RAG_SERVICE] Created new FAISS index with dimension {dimension}")
        
        self.index.add(new_embeddings.astype('float32'))
        print(f"[RAG_SERVICE] Added embeddings to index. Total vectors: {self.index.ntotal}")
        
        # Update session metadata
        current_metadata = self.documents_metadata
        for doc, source in zip(documents, sources):
            current_metadata.append({"text": doc, "source": source})
        self.documents_metadata = current_metadata
        print(f"[RAG_SERVICE] Updated metadata. Total documents: {len(self.documents_metadata)}")
        
        return len(documents)
    
    @classmethod
    def clear_session(cls, session_id: str):
        """Clear all data for a specific session"""
        if session_id in SESSION_STORES:
            del SESSION_STORES[session_id]
    
    @classmethod
    def get_active_sessions(cls):
        """Get list of active session IDs"""
        return list(SESSION_STORES.keys())