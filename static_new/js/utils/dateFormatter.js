// Utilitaire pour le formatage des dates
const DateFormatter = {
    formatWorkoutDate(date) {
        const options = { weekday: 'long', day: 'numeric', month: 'short' };
        return date.toLocaleDateString('fr-FR', options);
    },

    formatTime(date) {
        return date.toLocaleTimeString('fr-FR', { 
            hour: '2-digit', 
            minute: '2-digit'
        });
    },

    formatWeekRange(startDate, endDate) {
        const options = { day: 'numeric', month: 'short' };
        return `${startDate.toLocaleDateString('fr-FR', options)} - ${endDate.toLocaleDateString('fr-FR', options)}`;
    },

    getWeekNumber(date) {
        const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
        const pastDaysOfYear = (date - firstDayOfYear) / 86400000;
        return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
    },

    getCurrentWeekDates() {
        const now = new Date();
        const firstDay = new Date(now.setDate(now.getDate() - now.getDay() + 1));
        const lastDay = new Date(now.setDate(now.getDate() - now.getDay() + 7));
        return { firstDay, lastDay };
    },

    formatDuration(minutes) {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return hours > 0 ? `${hours}h${mins > 0 ? mins : ''}` : `${mins}min`;
    },

    formatRelativeDate(date) {
        const now = new Date();
        const diff = date - now;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        
        if (days === 0) return "Aujourd'hui";
        if (days === 1) return "Demain";
        if (days === -1) return "Hier";
        if (days > 1 && days < 7) return `Dans ${days} jours`;
        if (days < 0 && days > -7) return `Il y a ${-days} jours`;
        
        return this.formatWorkoutDate(date);
    }
};