class FinBotChat {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.urlInput = document.getElementById('urlInput');
        this.addUrlButton = document.getElementById('addUrlButton');
        this.urlStatus = document.getElementById('urlStatus');
        
        this.initializeEventListeners();
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
        
        // Sample question buttons
        document.querySelectorAll('.sample-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const question = e.target.getAttribute('data-question');
                this.messageInput.value = question;
                this.sendMessage();
            });
        });
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
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
                    max_results: 3
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Add bot response to chat
            this.addBotMessage(data.answer, data.sources, data.confidence);
            
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('Sorry, I encountered an error processing your request. Please try again.', 'bot');
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
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `url=${encodeURIComponent(url)}`
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
}

// Initialize the chat application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new FinBotChat();
});