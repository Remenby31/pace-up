// Gestionnaire de la navigation du bas
const BottomNav = {
    init() {
        this.navItems = document.querySelectorAll('#bottom-nav .nav-item');
        this.attachListeners();
        this.updateActiveState();
    },

    attachListeners() {
        this.navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const view = item.dataset.view;
                this.navigate(view);
            });
        });

        // Écouter les changements d'état pour mettre à jour la navigation
        StateManager.subscribe('currentView', (view) => {
            this.updateActiveState(view);
        });
    },

    navigate(view) {
        // Mettre à jour l'état
        StateManager.setState('currentView', view);
        
        // Mettre à jour l'URL sans recharger la page
        window.history.pushState({}, '', `#${view}`);
        
        // Déclencher le changement de vue
        Router.handleRoute();
    },

    updateActiveState(currentView = null) {
        // Si aucune vue n'est spécifiée, utiliser celle de l'URL ou 'today' par défaut
        if (!currentView) {
            currentView = window.location.hash.slice(1) || 'today';
        }

        // Mettre à jour les classes actives
        this.navItems.forEach(item => {
            item.classList.toggle('active', item.dataset.view === currentView);
        });
    }
};

// Initialiser la navigation au chargement
document.addEventListener('DOMContentLoaded', () => {
    BottomNav.init();
});