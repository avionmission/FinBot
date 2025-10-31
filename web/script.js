class FinBotChat {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.urlInput = document.getElementById('urlInput');
        this.addUrlButton = document.getElementById('addUrlButton');
        this.urlStatus = document.getElementById('urlStatus');
        this.fileInput = document.getElementById('fileInput');
        this.fileUploadArea = document.getElementById('fileUploadArea');
        this.fileStatus = document.getElementById('fileStatus');
        this.documentsList = document.getElementById('documentsList');
        this.apiKeyInput = document.getElementById('apiKeyInput');
        this.saveApiKeyButton = document.getElementById('saveApiKeyButton');
        this.apiKeyStatus = document.getElementById('apiKeyStatus');
        
        this.initializeEventListeners();
        this.loadApiKey();
        this.loadDocuments();
    }
    
    initializeEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter key
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // Add document from URL
        this.addUrlButton.addEventListener('click', () => this.addDocumentFromUrl());
        
        // File upload events
        this.fileUploadArea.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Drag and drop events
        this.fileUploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.fileUploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.fileUploadArea.addEventListener('drop', (e) => this.handleFileDrop(e));
        
        // Sample question buttons
        document.querySelectorAll('.sample-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const question = e.target.getAttribute('data-question');
                this.messageInput.value = question;
                this.sendMessage();
            });
        });
        
        // API key management
        this.saveApiKeyButton.addEventListener('click', () => this.saveApiKey());
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Check if API key is set
        const apiKey = this.getApiKey();
        if (!apiKey) {
            this.addMessage('Please set your Gemini API key in the Settings panel first.', 'bot');
            return;
        }
        
        // Add user message to chat
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        
        // Disable input while processing
        this.setLoading(true);
        
        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: message,
                    api_key: apiKey,
                    max_results: 3
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Add bot response to chat
            this.addBotMessage(data.answer, data.sources, data.confidence);
            
        } catch (error) {
            console.error('Error:', error);
            let errorMessage = 'Sorry, I encountered an error processing your request.';
            
            if (error.message.includes('API key')) {
                errorMessage = 'Invalid API key. Please check your Gemini API key in Settings.';
            } else if (error.message.includes('quota')) {
                errorMessage = 'API quota exceeded. Please check your Gemini API usage.';
            }
            
            this.addMessage(errorMessage, 'bot');
        } finally {
            this.setLoading(false);
        }
    }
    
    async addDocumentFromUrl() {
        const url = this.urlInput.value.trim();
        if (!url) return;
        
        this.setUrlLoading(true);
        this.showUrlStatus('Adding document...', 'info');
        
        try {
            const response = await fetch('/api/documents/add-url', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.showUrlStatus(`✅ Added ${data.chunks} document chunks successfully!`, 'success');
            this.urlInput.value = '';
            
        } catch (error) {
            console.error('Error:', error);
            this.showUrlStatus('❌ Failed to add document. Please check the URL and try again.', 'error');
        } finally {
            this.setUrlLoading(false);
        }
    }
    
    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `<strong>${sender === 'user' ? 'You' : 'FinBot'}:</strong> ${content}`;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addBotMessage(answer, sources, confidence) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `<strong>FinBot:</strong> ${answer}`;
        
        messageDiv.appendChild(contentDiv);
        
        // Add sources if available
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources';
            sourcesDiv.innerHTML = `<strong>Sources:</strong> ${sources.join(', ')}`;
            messageDiv.appendChild(sourcesDiv);
        }
        
        // Add confidence score
        if (confidence > 0) {
            const confidenceDiv = document.createElement('div');
            confidenceDiv.className = 'confidence';
            confidenceDiv.innerHTML = `Confidence: ${(confidence * 100).toFixed(1)}%`;
            messageDiv.appendChild(confidenceDiv);
        }
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    setLoading(loading) {
        this.sendButton.disabled = loading;
        this.messageInput.disabled = loading;
        this.sendButton.textContent = loading ? 'Thinking...' : 'Send';
    }
    
    setUrlLoading(loading) {
        this.addUrlButton.disabled = loading;
        this.urlInput.disabled = loading;
        this.addUrlButton.textContent = loading ? 'Adding...' : 'Add Document';
    }
    
    showUrlStatus(message, type) {
        this.urlStatus.textContent = message;
        this.urlStatus.className = `status-message ${type}`;
        
        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                this.urlStatus.textContent = '';
                this.urlStatus.className = 'status-message';
            }, 5000);
        }
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    // File upload methods
    handleFileSelect(event) {
        const files = event.target.files;
        this.uploadFiles(files);
    }
    
    handleDragOver(event) {
        event.preventDefault();
        this.fileUploadArea.classList.add('dragover');
    }
    
    handleDragLeave(event) {
        event.preventDefault();
        this.fileUploadArea.classList.remove('dragover');
    }
    
    handleFileDrop(event) {
        event.preventDefault();
        this.fileUploadArea.classList.remove('dragover');
        const files = event.dataTransfer.files;
        this.uploadFiles(files);
    }
    
    async uploadFiles(files) {
        if (!files || files.length === 0) return;
        
        this.showFileStatus('Uploading files...', 'info');
        
        for (let file of files) {
            try {
                await this.uploadSingleFile(file);
            } catch (error) {
                console.error(`Error uploading ${file.name}:`, error);
                this.showFileStatus(`❌ Failed to upload ${file.name}`, 'error');
                return;
            }
        }
        
        this.showFileStatus(`✅ Successfully uploaded ${files.length} file(s)!`, 'success');
        this.loadDocuments(); // Refresh document list
        this.fileInput.value = ''; // Clear file input
    }
    
    async uploadSingleFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/documents/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async loadDocuments() {
        try {
            const response = await fetch('/api/documents');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.displayDocuments(data.documents);
            
        } catch (error) {
            console.error('Error loading documents:', error);
            this.documentsList.innerHTML = '<div class="no-documents">Failed to load documents</div>';
        }
    }
    
    displayDocuments(documents) {
        if (!documents || documents.length === 0) {
            this.documentsList.innerHTML = '<div class="no-documents">No documents added yet</div>';
            return;
        }
        
        const documentsHtml = documents.map(doc => `
            <div class="document-item">
                <div class="document-name">${doc.name}</div>
                <div class="document-info">
                    <span class="document-type">${doc.type}</span>
                    <span>${doc.chunks} chunks</span>
                </div>
            </div>
        `).join('');
        
        this.documentsList.innerHTML = documentsHtml;
    }
    
    showFileStatus(message, type) {
        this.fileStatus.textContent = message;
        this.fileStatus.className = `status-message ${type}`;
        
        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                this.fileStatus.textContent = '';
                this.fileStatus.className = 'status-message';
            }, 5000);
        }
    }
    
    // API Key Management
    saveApiKey() {
        const apiKey = this.apiKeyInput.value.trim();
        if (!apiKey) {
            this.showApiKeyStatus('Please enter an API key', 'error');
            return;
        }
        
        // Store API key in localStorage
        localStorage.setItem('gemini_api_key', apiKey);
        this.showApiKeyStatus('API key saved successfully!', 'success');
        
        // Clear the input for security
        this.apiKeyInput.value = '';
    }
    
    loadApiKey() {
        const savedApiKey = localStorage.getItem('gemini_api_key');
        if (savedApiKey) {
            this.showApiKeyStatus('API key loaded', 'success');
        } else {
            this.showApiKeyStatus('Please enter your Gemini API key', 'info');
        }
    }
    
    getApiKey() {
        return localStorage.getItem('gemini_api_key');
    }
    
    showApiKeyStatus(message, type) {
        this.apiKeyStatus.textContent = message;
        this.apiKeyStatus.className = `status-message ${type}`;
        
        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                this.apiKeyStatus.textContent = '';
                this.apiKeyStatus.className = 'status-message';
            }, 3000);
        }
    }
}

// Initialize the chat application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new FinBotChat();
});