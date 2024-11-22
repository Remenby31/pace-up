// Gestionnaire du chat avec le coach
const Chat = {
    isOpen: false,
    messageHistory: [],
    container: null,

    init() {
        // Initialiser le conteneur de chat depuis le template
        const template = document.getElementById('chat-template');
        this.container = template.content.cloneNode(true).querySelector('.chat-container');
        document.body.appendChild(this.container);
        
        this.attachListeners();
        this.loadHistory();
    },

    attachListeners() {
        // Fermeture du chat
        this.container.querySelector('.close-btn').addEventListener('click', () => this.close());

        // Gestion de l'envoi de messages
        const input = this.container.querySelector('.chat-input input');
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && input.value.trim()) {
                this.sendMessage(input.value.trim());
                input.value = '';
            }
        });

        // Gestion du bouton vocal
        this.container.querySelector('.voice-btn').addEventListener('click', () => {
            // Implémenter la reconnaissance vocale ici
            console.log('Voice input not implemented yet');
        });
    },

    async loadHistory() {
        this.messageHistory = StateManager.getState('chatHistory') || [];
        this.renderMessages();
    },

    async sendMessage(message) {
        try {
            // Ajouter le message utilisateur
            this.addMessage(message, true);

            // Obtenir la réponse du coach
            const response = await API.sendMessage(message, this.messageHistory);
            
            if (response.success) {
                // Afficher la réponse
                this.addMessage(response.response, false);
                
                // S'il y a des modifications du programme
                if (response.changes_made) {
                    await StateManager.loadProgram();
                    // Rafraîchir la vue actuelle
                    Router.handleRoute();
                }
                
                // Gérer les suggestions si présentes
                if (response.suggestions) {
                    this.showSuggestions(response.suggestions);
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('Sorry, I encountered an error. Please try again.', false);
        }
    },

    addMessage(content, fromUser = true) {
        const message = {
            content,
            fromUser,
            timestamp: new Date().toISOString()
        };
        
        this.messageHistory.push(message);
        StateManager.setState('chatHistory', this.messageHistory);
        this.renderMessage(message);
    },

    renderMessage(message) {
        const messagesContainer = this.container.querySelector('.chat-messages');
        const messageEl = document.createElement('div');
        messageEl.className = `chat-message ${message.fromUser ? 'user' : 'coach'}`;
        messageEl.innerHTML = `
            <div class="message-content">${message.content}</div>
            <div class="message-time">${DateFormatter.formatTime(new Date(message.timestamp))}</div>
        `;
        messagesContainer.appendChild(messageEl);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    },

    renderMessages() {
        const messagesContainer = this.container.querySelector('.chat-messages');
        messagesContainer.innerHTML = '';
        this.messageHistory.forEach(message => this.renderMessage(message));
    },

    showSuggestions(suggestions) {
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'chat-suggestions';
        
        suggestions.forEach(suggestion => {
            const btn = document.createElement('button');
            btn.className = 'suggestion-btn';
            btn.textContent = suggestion.content;
            btn.addEventListener('click', () => this.sendMessage(suggestion.content));
            suggestionsContainer.appendChild(btn);
        });

        const messagesContainer = this.container.querySelector('.chat-messages');
        messagesContainer.appendChild(suggestionsContainer);
    },

    open(initialMessage = null) {
        this.container.classList.add('open');
        this.isOpen = true;
        
        if (initialMessage) {
            const input = this.container.querySelector('.chat-input input');
            input.value = initialMessage;
            input.focus();
        }
    },

    close() {
        this.container.classList.remove('open');
        this.isOpen = false;
    }
};