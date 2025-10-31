import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .rag_service import RAGService

class DocumentService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
    
    async def add_from_url(self, url: str):
        """Retrieve document from URL and add to vector store"""
        try:
            # Fetch content from URL
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Split text into chunks
            documents = self.text_splitter.split_text(text)
            
            # Filter out very short chunks
            documents = [doc for doc in documents if len(doc.strip()) > 50]
            
            if not documents:
                raise ValueError("No meaningful content extracted from URL")
            
            # Add to RAG service
            rag_service = RAGService()
            sources = [url] * len(documents)
            chunks_added = rag_service.add_documents(documents, sources)
            
            return chunks_added
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to process document: {str(e)}")
    
    def add_from_text(self, text: str, source: str = "Manual Input"):
        """Add text document to vector store"""
        try:
            # Split text into chunks
            documents = self.text_splitter.split_text(text)
            
            # Filter out very short chunks
            documents = [doc for doc in documents if len(doc.strip()) > 50]
            
            if not documents:
                raise ValueError("No meaningful content in provided text")
            
            # Add to RAG service
            rag_service = RAGService()
            sources = [source] * len(documents)
            chunks_added = rag_service.add_documents(documents, sources)
            
            return chunks_added
            
        except Exception as e:
            raise Exception(f"Failed to process text: {str(e)}")