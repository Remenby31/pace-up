// Script d'initialisation principal
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Initialiser le gestionnaire d'état
        StateManager.init();
        
        // Initialiser le chat
        Chat.init();
        
        // Initialiser le routeur après avoir chargé les données initiales
        await StateManager.loadProgram();
        Router.init();
        
        // Vérifier si nous avons une vue spécifique dans l'URL
        const hash = window.location.hash.slice(1);
        if (hash) {
            Router.handleRoute();
        } else {
            // Rediriger vers la vue par défaut si aucune n'est spécifiée
            window.location.hash = 'today';
        }
        
        console.log('Application initialized successfully');
        
    } catch (error) {
        console.error('Error initializing application:', error);
    }
});