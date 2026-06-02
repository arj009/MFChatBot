document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = 'http://127.0.0.1:8000/api';
    
    const chatHistory = document.getElementById('chatHistory');
    const examplesContainer = document.getElementById('examplesContainer');
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');

    // 1. Fetch Examples on Load
    fetchExamples();

    async function fetchExamples() {
        try {
            const response = await fetch(`${API_BASE_URL}/examples`);
            if (!response.ok) throw new Error('Failed to fetch examples');
            const examples = await response.json();
            
            examplesContainer.innerHTML = '';
            examples.forEach(ex => {
                const btn = document.createElement('button');
                btn.className = 'example-chip';
                btn.textContent = ex.label;
                btn.title = ex.query;
                btn.onclick = () => handleSend(ex.query);
                examplesContainer.appendChild(btn);
            });
        } catch (error) {
            console.error('Error loading examples:', error);
            // Hide examples container if fetch fails
            examplesContainer.style.display = 'none';
        }
    }

    // 2. Handle Form Submit
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (text) handleSend(text);
    });

    async function handleSend(text) {
        // Clear input and remove examples if present
        userInput.value = '';
        if (examplesContainer) examplesContainer.remove();

        // Render User Message
        appendUserMessage(text);
        scrollToBottom();

        // Show Typing Indicator & disable input
        const typingId = appendTypingIndicator();
        scrollToBottom();
        sendBtn.disabled = true;
        userInput.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: text })
            });

            if (!response.ok) throw new Error('Server returned an error');
            const data = await response.json();
            
            // Remove typing indicator
            removeMessage(typingId);
            
            // Render Assistant Message
            appendAssistantMessage(data);

        } catch (error) {
            console.error('Chat error:', error);
            removeMessage(typingId);
            appendAssistantMessage({
                answer: "I'm sorry, I'm having trouble connecting to the server right now. Please try again later.",
                source_url: null,
                last_updated: null
            });
        } finally {
            sendBtn.disabled = false;
            userInput.disabled = false;
            userInput.focus();
            scrollToBottom();
        }
    }

    // 3. UI Rendering Helpers
    function appendUserMessage(text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message user';
        msgDiv.innerHTML = `<div class="bubble"><p>${escapeHTML(text)}</p></div>`;
        chatHistory.appendChild(msgDiv);
    }

    function appendAssistantMessage(data) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message assistant';
        
        let bubbleHtml = `<div class="bubble">`;
        
        // Formatted answer text (split by newlines for paragraphs)
        const paragraphs = data.answer.split('\n').filter(p => p.trim());
        paragraphs.forEach(p => {
            bubbleHtml += `<p>${escapeHTML(p)}</p>`;
        });

        // Source URL
        if (data.source_url) {
            bubbleHtml += `
                <a href="${data.source_url}" target="_blank" rel="noopener noreferrer" class="source-link">
                    Read more on Groww
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="7" y1="17" x2="17" y2="7"></line>
                        <polyline points="7 7 17 7 17 17"></polyline>
                    </svg>
                </a>
            `;
        }
        
        bubbleHtml += `</div>`;
        
        // Footer (Last updated)
        if (data.last_updated) {
            bubbleHtml += `<div class="msg-footer">Last updated: ${data.last_updated}</div>`;
        }

        msgDiv.innerHTML = bubbleHtml;
        chatHistory.appendChild(msgDiv);
    }

    function appendTypingIndicator() {
        const id = 'typing-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message assistant';
        msgDiv.id = id;
        msgDiv.innerHTML = `
            <div class="bubble typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        chatHistory.appendChild(msgDiv);
        return id;
    }

    function removeMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag])
        );
    }
});
