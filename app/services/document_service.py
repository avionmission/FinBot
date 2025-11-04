import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .rag_service import RAGService
import PyPDF2
import pandas as pd
import io
import os
from typing import List, Dict

# Optional pdfplumber import for better PDF text extraction
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

class DocumentService:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
    
    async def add_from_url(self, url: str):
        """Retrieve document from URL and add to vector store"""
        try:
            # Fetch content from URL with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML and extract text content
            soup = BeautifulSoup(response.content, 'html.parser')
            
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
            
            # Add to RAG service with session ID
            rag_service = RAGService(self.session_id)
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
            
            # Add to RAG service with session ID
            rag_service = RAGService(self.session_id)
            sources = [source] * len(documents)
            chunks_added = rag_service.add_documents(documents, sources)
            
            return chunks_added
            
        except Exception as e:
            raise Exception(f"Failed to process text: {str(e)}")
    
    async def add_from_file(self, file_content: bytes, filename: str, content_type: str):
        """Add document from uploaded file"""
        try:
            print(f"[DOC_SERVICE] Processing file: {filename}, type: {content_type}, session: {self.session_id}")
            text = ""
            
            if content_type == "application/pdf" or filename.lower().endswith('.pdf'):
                text = self._extract_pdf_text(file_content)
            elif content_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"] or filename.lower().endswith(('.xlsx', '.xls')):
                text = self._extract_excel_text(file_content, filename)
            elif content_type == "text/plain" or filename.lower().endswith('.txt'):
                text = file_content.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file type: {content_type}")
            
            print(f"[DOC_SERVICE] Extracted text length: {len(text)} characters")
            
            if not text.strip():
                raise ValueError("No text content found in the file")
            
            # Split text into chunks
            documents = self.text_splitter.split_text(text)
            print(f"[DOC_SERVICE] Split into {len(documents)} initial chunks")
            
            # Filter out very short chunks
            documents = [doc for doc in documents if len(doc.strip()) > 50]
            print(f"[DOC_SERVICE] After filtering: {len(documents)} chunks")
            
            if not documents:
                raise ValueError("No meaningful content extracted from file")
            
            # Add to RAG service with session ID
            rag_service = RAGService(self.session_id)
            sources = [filename] * len(documents)
            chunks_added = rag_service.add_documents(documents, sources)
            print(f"[DOC_SERVICE] Added {chunks_added} chunks to RAG service")
            
            return chunks_added
            
        except Exception as e:
            print(f"[DOC_SERVICE ERROR] {str(e)}")
            raise Exception(f"Failed to process file: {str(e)}")
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF file using multiple methods"""
        text = ""
        
        # Try pdfplumber first for better layout handling
        if PDFPLUMBER_AVAILABLE:
            try:
                text = self._extract_pdf_with_pdfplumber(file_content)
                if text and len(text.strip()) > 50:
                    return text
            except Exception:
                pass
        
        # Fallback to PyPDF2
        try:
            text = self._extract_pdf_with_pypdf2(file_content)
            if text and len(text.strip()) > 50:
                return text
        except Exception:
            pass
        
        raise Exception("Failed to extract readable text from PDF using any available method")
    
    def _extract_pdf_with_pdfplumber(self, file_content: bytes) -> str:
        """Extract text using pdfplumber for better layout handling"""
        pdf_file = io.BytesIO(file_content)
        text = ""
        
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        
        return self._clean_extracted_text(text)
    
    def _extract_pdf_with_pypdf2(self, file_content: bytes) -> str:
        """Extract text using PyPDF2 as fallback method"""
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        
        return self._clean_extracted_text(text)
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted PDF text"""
        if not text:
            return ""
        
        # Clean and filter text lines
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('http') and len(line.split()) == 1:
                continue
            if len(line) <= 2:
                continue
            if line.isdigit() and len(line) <= 3:
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_excel_text(self, file_content: bytes, filename: str) -> str:
        """Extract text from Excel file"""
        try:
            excel_file = io.BytesIO(file_content)
            
            # Try to read as Excel file
            if filename.lower().endswith('.xlsx'):
                df = pd.read_excel(excel_file, engine='openpyxl')
            else:
                df = pd.read_excel(excel_file, engine='xlrd')
            
            # Convert DataFrame to text
            text = ""
            
            # Add column headers
            text += "Columns: " + ", ".join(df.columns.astype(str)) + "\n\n"
            
            # Add data rows
            for index, row in df.iterrows():
                row_text = " | ".join([f"{col}: {val}" for col, val in zip(df.columns, row.values) if pd.notna(val)])
                text += row_text + "\n"
            
            return text
        except Exception as e:
            raise Exception(f"Failed to extract Excel text: {str(e)}")
    
    def get_document_sources(self) -> List[Dict]:
        """Get list of all document sources in the session knowledge base"""
        try:
            rag_service = RAGService(self.session_id)
            
            # Get unique sources from metadata
            sources = {}
            for doc in rag_service.documents_metadata:
                source = doc["source"]
                if source in sources:
                    sources[source]["chunks"] += 1
                else:
                    sources[source] = {
                        "name": source,
                        "chunks": 1,
                        "type": self._get_source_type(source)
                    }
            
            return list(sources.values())
        except Exception as e:
            raise Exception(f"Failed to get document sources: {str(e)}")
    
    def _get_source_type(self, source: str) -> str:
        """Determine the type of document source"""
        if source == "FAQ":
            return "Built-in FAQ"
        elif source.startswith("http"):
            return "Web Document"
        elif source.lower().endswith('.pdf'):
            return "PDF Document"
        elif source.lower().endswith(('.xlsx', '.xls')):
            return "Excel Spreadsheet"
        elif source.lower().endswith('.txt'):
            return "Text Document"
        else:
            return "Unknown"