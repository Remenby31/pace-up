// Composant pour afficher une séance d'entraînement
class WorkoutCard {
    constructor(workout) {
        this.workout = workout;
    }

    static getTypeIcon(type) {
        const icons = {
            'Easy Run': '🏃‍♂️',
            'Long Run': '🏃‍♂️',
            'Intervals': '⚡',
            'Tempo': '🔥',
            'Recovery': '💪'
        };
        return icons[type] || '🏃‍♂️';
    }

    static getTypeColor(type) {
        const colors = {
            'Easy Run': '#4CAF50',
            'Long Run': '#2196F3',
            'Intervals': '#FF5722',
            'Tempo': '#FFC107',
            'Recovery': '#9C27B0'
        };
        return colors[type] || '#4CAF50';
    }

    render() {
        const date = new Date(this.workout.date);
        const formattedDate = DateFormatter.formatWorkoutDate(date);
        const timeString = DateFormatter.formatTime(date);

        return `
            <div class="workout-card" data-date="${this.workout.date}">
                <div class="workout-header">
                    <span class="workout-date">${formattedDate}</span>
                    <span class="workout-time">${timeString}</span>
                </div>
                <div class="workout-body">
                    <div class="workout-type" style="background-color: ${WorkoutCard.getTypeColor(this.workout.type_de_seance)}">
                        ${WorkoutCard.getTypeIcon(this.workout.type_de_seance)}
                        ${this.workout.type_de_seance}
                    </div>
                    <div class="workout-distance">${this.workout.distance}km</div>
                </div>
                <div class="workout-description">${this.workout.description}</div>
                <div class="workout-actions">
                    <button class="btn-action" data-action="modify">Modify</button>
                    <button class="btn-action" data-action="skip">Skip</button>
                </div>
            </div>
        `;
    }

    attachListeners(card) {
        const modifyBtn = card.querySelector('[data-action="modify"]');
        const skipBtn = card.querySelector('[data-action="skip"]');

        modifyBtn.addEventListener('click', () => this.handleModify());
        skipBtn.addEventListener('click', () => this.handleSkip());
    }

    handleModify() {
        Chat.open(`I want to modify my ${this.workout.type_de_seance} scheduled for ${DateFormatter.formatWorkoutDate(new Date(this.workout.date))}`);
    }

    handleSkip() {
        Chat.open(`I need to skip my ${this.workout.type_de_seance} scheduled for ${DateFormatter.formatWorkoutDate(new Date(this.workout.date))}`);
    }

    static renderWeekSummary(workouts) {
        const totalDistance = workouts.reduce((sum, w) => sum + w.distance, 0);
        const totalWorkouts = workouts.length;

        return `
            <div class="week-summary">
                <div class="summary-item">
                    <span class="summary-value">${totalWorkouts}</span>
                    <span class="summary-label">workouts</span>
                </div>
                <div class="summary-item">
                    <span class="summary-value">${totalDistance}km</span>
                    <span class="summary-label">total</span>
                </div>
            </div>
        `;
    }
}