// Gestionnaire de routage simple
const Router = {
    routes: {
        today: {
            render: () => TodayView.render(),
            init: () => TodayView.init()
        },
        plan: {
            render: () => PlanView.render(),
            init: () => PlanView.init()
        },
        settings: {
            render: () => SettingsView.render(),
            init: () => SettingsView.init()
        }
    },

    init() {
        window.addEventListener('hashchange', () => this.handleRoute());
        window.addEventListener('load', () => this.handleRoute());
        
        // Gérer les clics sur la navigation
        document.querySelectorAll('#bottom-nav .nav-item').forEach(button => {
            button.addEventListener('click', (e) => {
                const view = e.currentTarget.dataset.view;
                this.navigateTo(view);
            });
        });
    },

    handleRoute() {
        const hash = window.location.hash.slice(1) || 'today';
        const viewContainer = document.getElementById('view-container');
        
        // Mettre à jour la navigation
        document.querySelectorAll('#bottom-nav .nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.view === hash);
        });

        // Mettre à jour l'état
        StateManager.setState('currentView', hash);

        // Rendre la vue
        if (this.routes[hash]) {
            viewContainer.innerHTML = this.routes[hash].render();
            this.routes[hash].init();
        }
    },

    navigateTo(route) {
        window.location.hash = route;
    }
};