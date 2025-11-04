class FinBotChat {
    constructor() {
        // Generate unique session ID for this browser session
        this.sessionId = this.generateSessionId();

        // Chat elements
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

        this.initializeEventListeners();
        this.loadApiKey();
        this.loadDocuments();

        // Show session info
        console.log('Session ID:', this.sessionId);
        this.addMessage(`Welcome! Your session ID is: ${this.sessionId.substring(0, 8)}...`, 'system');
    }

    generateSessionId() {
        return 'session-' + Math.random().toString(36).substring(2, 11) + '-' + Date.now().toString(36);
    }

    getHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-Session-ID': this.sessionId
        };
    }

    loadApiKey() {
        const savedApiKey = localStorage.getItem('gemini_api_key');
        if (savedApiKey && this.apiKeyInput) {
            this.apiKeyInput.value = savedApiKey;
            this.addMessage('✅ API key loaded from browser storage', 'system');
        }

        // Save API key when it changes (auto-save)
        if (this.apiKeyInput) {
            this.apiKeyInput.addEventListener('input', () => {
                localStorage.setItem('gemini_api_key', this.apiKeyInput.value);
            });
        }
    }

    saveApiKey() {
        const apiKey = this.apiKeyInput?.value?.trim();
        if (apiKey) {
            localStorage.setItem('gemini_api_key', apiKey);
            this.addMessage('✅ API key saved successfully!', 'system');
        } else {
            this.addMessage('⚠️ Please enter an API key before saving', 'system');
        }
    }

    initializeEventListeners() {
        // Send message on button click
        this.sendButton?.addEventListener('click', () => this.sendMessage());

        // Send message on Enter key
        this.messageInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // Add document from URL
        this.addUrlButton?.addEventListener('click', () => this.addDocumentFromUrl());

        // File upload events
        this.fileUploadArea?.addEventListener('click', () => this.fileInput.click());
        this.fileInput?.addEventListener('change', (e) => this.handleFileSelect(e));

        // Drag and drop events
        this.fileUploadArea?.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.fileUploadArea?.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.fileUploadArea?.addEventListener('drop', (e) => this.handleFileDrop(e));

        // Sample question buttons
        document.querySelectorAll('.sample-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const question = e.target.getAttribute('data-question');
                this.messageInput.value = question;
                this.sendMessage();
            });
        });

        // Save API key button
        const saveApiKeyButton = document.getElementById('saveApiKeyButton');
        saveApiKeyButton?.addEventListener('click', () => this.saveApiKey());

        // Debug button
        const debugButton = document.getElementById('debugButton');
        if (debugButton) {
            debugButton.addEventListener('click', () => this.debugSession());
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        const apiKey = this.apiKeyInput.value.trim();
        if (!apiKey) {
            alert('Please enter your Gemini API key first.');
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
                headers: this.getHeaders(),
                body: JSON.stringify({
                    question: message,
                    max_results: 3,
                    api_key: apiKey
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
                headers: this.getHeaders(),
                body: JSON.stringify({ url: url })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.showUrlStatus(`✅ Added ${data.chunks} document chunks successfully!`, 'success');
            this.urlInput.value = '';
            this.loadDocuments(); // Refresh document list

        } catch (error) {
            console.error('Error:', error);
            this.showUrlStatus('❌ Failed to add document. Please check the URL and try again.', 'error');
        } finally {
            this.setUrlLoading(false);
        }
    }

    // Simple markdown renderer for basic formatting
    renderMarkdown(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // **bold**
            .replace(/\*(.*?)\*/g, '<em>$1</em>')              // *italic*
            .replace(/`(.*?)`/g, '<code>$1</code>')            // `code`
            .replace(/\n/g, '<br>');                           // line breaks
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        let senderName = 'FinBot';
        if (sender === 'user') senderName = 'You';
        if (sender === 'system') senderName = 'System';

        // Render markdown for bot messages, plain text for others
        const renderedContent = sender === 'bot' ? this.renderMarkdown(content) : content;
        contentDiv.innerHTML = `<strong>${senderName}:</strong> ${renderedContent}`;

        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addBotMessage(answer, sources, confidence) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Render markdown in bot responses
        const renderedAnswer = this.renderMarkdown(answer);
        contentDiv.innerHTML = `<strong>FinBot:</strong> ${renderedAnswer}`;

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
        formData.append('session_id', this.sessionId); // Add session ID as form field

        console.log('Uploading file for session:', this.sessionId);
        const response = await fetch('/api/documents/upload', {
            method: 'POST',
            headers: {
                'X-Session-ID': this.sessionId
                // Note: Don't set Content-Type with FormData, browser sets it automatically
            },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Upload result:', result);

        // Update our session ID if server returned one
        if (result.session_id && result.session_id !== this.sessionId) {
            console.log('Server returned different session ID:', result.session_id);
            this.sessionId = result.session_id;
        }

        return result;
    }

    async loadDocuments() {
        try {
            console.log('Loading documents for session:', this.sessionId);
            const response = await fetch('/api/documents', {
                headers: {
                    'X-Session-ID': this.sessionId
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Documents loaded:', data.documents);
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

    async debugSession() {
        try {
            const debugInfo = document.getElementById('debugInfo');
            debugInfo.innerHTML = 'Checking session...';

            // Check session chunks
            const chunksResponse = await fetch('/api/debug/chunks', {
                headers: {
                    'X-Session-ID': this.sessionId
                }
            });

            if (chunksResponse.ok) {
                const chunksData = await chunksResponse.json();
                debugInfo.innerHTML = `
                    <strong>Session:</strong> ${this.sessionId.substring(0, 12)}...<br>
                    <strong>Chunks:</strong> ${chunksData.total_chunks}<br>
                    <strong>Session Exists:</strong> ${chunksData.session_exists}<br>
                    <strong>All Sessions:</strong> ${chunksData.all_sessions.length}<br>
                    <strong>Sources:</strong> ${chunksData.chunks.map(c => c.source).join(', ')}
                `;
            } else {
                debugInfo.innerHTML = 'Debug failed';
            }
        } catch (error) {
            console.error('Debug error:', error);
            document.getElementById('debugInfo').innerHTML = 'Debug error: ' + error.message;
        }
    }
}

// Initialize the chat application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new FinBotChat();
});