// Gestionnaire d'état simple avec pattern Observer
const StateManager = {
    state: {
        currentView: 'today',
        program: null,
        profile: null,
        chatHistory: [],
        currentWeek: null
    },

    listeners: {},

    init() {
        // Charger l'état initial depuis le localStorage si disponible
        const savedState = localStorage.getItem('appState');
        if (savedState) {
            this.state = { ...this.state, ...JSON.parse(savedState) };
        }
    },

    subscribe(key, callback) {
        if (!this.listeners[key]) {
            this.listeners[key] = [];
        }
        this.listeners[key].push(callback);
    },

    setState(key, newValue) {
        this.state[key] = newValue;
        
        // Sauvegarder dans le localStorage
        localStorage.setItem('appState', JSON.stringify(this.state));
        
        // Notifier les listeners
        if (this.listeners[key]) {
            this.listeners[key].forEach(callback => callback(newValue));
        }
    },

    getState(key) {
        return this.state[key];
    },

    // Méthodes spécifiques pour la gestion du programme
    async loadProgram() {
        try {
            const response = await API.getProgram();
            if (response.success) {
                this.setState('program', response.program);
                this.setState('profile', response.profile);
                return response;
            }
            throw new Error('Failed to load program');
        } catch (error) {
            console.error('Error loading program:', error);
            throw error;
        }
    },

    // Gestion de l'historique du chat
    addChatMessage(message, fromUser = true) {
        const chatHistory = [...this.state.chatHistory, {
            role: fromUser ? 'user' : 'assistant',
            content: message,
            timestamp: new Date().toISOString()
        }];
        this.setState('chatHistory', chatHistory);
    }
};