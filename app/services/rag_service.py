import os
import faiss
import numpy as np
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from sentence_transformers import SentenceTransformer
import pickle
from dotenv import load_dotenv

load_dotenv()

class RAGService:
    def __init__(self):
        self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')
        self.llm = OpenAI(temperature=0.7, openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_store = None
        self.documents_metadata = []
        self.load_or_create_index()
    
    def load_or_create_index(self):
        """Load existing FAISS index or create new one"""
        index_path = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
        
        if os.path.exists(f"{index_path}.faiss") and os.path.exists(f"{index_path}_metadata.pkl"):
            # Load existing index
            index = faiss.read_index(f"{index_path}.faiss")
            with open(f"{index_path}_metadata.pkl", 'rb') as f:
                self.documents_metadata = pickle.load(f)
            
            # Create FAISS vector store wrapper
            self.vector_store = FAISS(
                embedding_function=self.embeddings.encode,
                index=index,
                docstore={},
                index_to_docstore_id={}
            )
        else:
            # Create new index with sample financial documents
            self._create_sample_index()
    
    def _create_sample_index(self):
        """Create initial index with sample financial FAQs"""
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
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings.astype('float32'))
        
        # Store metadata
        self.documents_metadata = [{"text": doc, "source": "FAQ"} for doc in sample_docs]
        
        # Save index
        os.makedirs(os.path.dirname(os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")), exist_ok=True)
        index_path = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
        faiss.write_index(index, f"{index_path}.faiss")
        
        with open(f"{index_path}_metadata.pkl", 'wb') as f:
            pickle.dump(self.documents_metadata, f)
        
        # Create vector store wrapper
        self.vector_store = FAISS(
            embedding_function=self.embeddings.encode,
            index=index,
            docstore={},
            index_to_docstore_id={}
        )
    
    async def query(self, question: str, max_results: int = 3):
        """Process query using RAG"""
        # Get query embedding
        query_embedding = self.embeddings.encode([question])
        
        # Search similar documents
        index_path = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
        index = faiss.read_index(f"{index_path}.faiss")
        
        scores, indices = index.search(query_embedding.astype('float32'), max_results)
        
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
            response = self.llm(prompt)
            confidence = float(np.mean(scores[0])) if len(scores[0]) > 0 else 0.0
            
            return {
                "answer": response.strip(),
                "sources": sources,
                "confidence": confidence
            }
        except Exception as e:
            return {
                "answer": f"I apologize, but I encountered an error processing your question: {str(e)}",
                "sources": [],
                "confidence": 0.0
            }
    
    def add_documents(self, documents: list[str], sources: list[str]):
        """Add new documents to the index"""
        # Create embeddings for new documents
        new_embeddings = self.embeddings.encode(documents)
        
        # Load existing index
        index_path = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
        index = faiss.read_index(f"{index_path}.faiss")
        
        # Add new embeddings
        index.add(new_embeddings.astype('float32'))
        
        # Update metadata
        for doc, source in zip(documents, sources):
            self.documents_metadata.append({"text": doc, "source": source})
        
        # Save updated index
        faiss.write_index(index, f"{index_path}.faiss")
        with open(f"{index_path}_metadata.pkl", 'wb') as f:
            pickle.dump(self.documents_metadata, f)
        
        return len(documents)