// API Service pour communiquer avec le backend
const API = {
    baseUrl: 'http://localhost:18091', // À adapter selon l'environnement

    async initProgram() {
        try {
            const response = await fetch(`${this.baseUrl}/init-program`, {
                method: 'POST'
            });
            return await response.json();
        } catch (error) {
            console.error('Error initializing program:', error);
            throw error;
        }
    },

    async getProgram() {
        try {
            const response = await fetch(`${this.baseUrl}/get-program`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching program:', error);
            throw error;
        }
    },

    async sendMessage(message, history = []) {
        try {
            const response = await fetch(`${this.baseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message,
                    history
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error sending message:', error);
            throw error;
        }
    },

    async getChatSuggestions(message, history = []) {
        try {
            const response = await fetch(`${this.baseUrl}/chat-suggestions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message,
                    history
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error getting suggestions:', error);
            throw error;
        }
    },

    async getCalendarUrls() {
        try {
            const response = await fetch(`${this.baseUrl}/calendar-url`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching calendar URLs:', error);
            throw error;
        }
    }
};