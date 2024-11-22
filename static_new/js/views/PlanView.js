// Vue du plan d'entraînement global
const PlanView = {
    async init() {
        try {
            if (!StateManager.getState('program')) {
                await StateManager.loadProgram();
            }
            this.updateProgress();
            this.attachListeners();
        } catch (error) {
            console.error('Error initializing PlanView:', error);
        }
    },

    attachListeners() {
        const calendarButton = document.querySelector('.calendar-sync-button');
        if (calendarButton) {
            calendarButton.addEventListener('click', this.handleCalendarSync.bind(this));
        }
    },

    async handleCalendarSync() {
        try {
            const response = await API.getCalendarUrls();
            if (response.success) {
                this.showCalendarOptions(response.urls);
            }
        } catch (error) {
            console.error('Error getting calendar URLs:', error);
        }
    },

    showCalendarOptions(urls) {
        const modal = document.createElement('div');
        modal.className = 'calendar-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>Sync with your calendar</h3>
                <div class="calendar-options">
                    <a href="${urls.google_calendar}" target="_blank" class="calendar-option">
                        Google Calendar
                    </a>
                    <a href="${urls.ical}" class="calendar-option">
                        Apple Calendar
                    </a>
                    <div class="calendar-option">
                        <p>Direct URL:</p>
                        <input type="text" readonly value="${urls.ics_feed}" />
                    </div>
                </div>
                <button class="close-modal">Close</button>
            </div>
        `;

        document.body.appendChild(modal);
        modal.querySelector('.close-modal').addEventListener('click', () => {
            modal.remove();
        });
    },

    updateProgress() {
        const program = StateManager.getState('program');
        if (!program) return;

        const profile = StateManager.getState('profile');
        const totalWorkouts = program.length;
        const completedWorkouts = program.filter(workout => {
            return new Date(workout.date) < new Date();
        }).length;

        const progressPercent = Math.round((completedWorkouts / totalWorkouts) * 100);
        const progressCircle = document.querySelector('.progress-circle');
        if (progressCircle) {
            progressCircle.style.setProperty('--progress', `${progressPercent}`);
        }
    },

    // Mise à jour de la méthode render de PlanView
render() {
    const profile = StateManager.getState('profile');
    const program = StateManager.getState('program');

    if (!program || !profile) {
        return '<div class="loading"></div>';
    }

    const { totalDistance, remainingDays, remainingWorkouts } = this.calculateProgramStats();
    const progressPercent = Math.round(((program.length - remainingWorkouts) / program.length) * 100);

    return `
        <div class="plan-view">
            <div class="plan-header">
                <div class="card">
                    <span class="running-icon">🏃</span>
                    <h1>${profile.distance_cible}km Run</h1>
                    <p class="race-info">Race Date ${DateFormatter.formatWorkoutDate(new Date(profile.goal_date))}</p>
                    <p class="race-link">${profile.objectif_principal}</p>

                    <div class="stats-container">
                        <div class="stat-item">
                            <span class="stat-icon">📅</span>
                            <span class="stat-value">${program.length} weeks Plan</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-icon">🏃</span>
                            <span class="stat-value">${totalDistance}km total</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="progress-section card">
                <div class="progress-info">
                    <p class="progress-text">You are at your ${this.getCurrentWeek()}th week of training!</p>
                    <div class="progress-stats">
                        <p>${remainingDays} days left</p>
                        <p>${remainingWorkouts} workouts left</p>
                    </div>
                </div>
                <div class="progress-circle">
                    <svg viewBox="0 0 36 36">
                        <path d="M18 2.0845
                            a 15.9155 15.9155 0 0 1 0 31.831
                            a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="#eee"
                            stroke-width="3"
                        />
                        <path d="M18 2.0845
                            a 15.9155 15.9155 0 0 1 0 31.831
                            a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="#FF5733"
                            stroke-width="3"
                            stroke-dasharray="${progressPercent}, 100"
                        />
                    </svg>
                    <span class="progress-percentage">${progressPercent}%</span>
                </div>
            </div>

            <div class="estimated-time card">
                <h3>Estimated Time Finisher</h3>
                <p class="time-range">${profile.chrono_cible}</p>
            </div>

            <div class="current-week card">
                <h3>Current Week ${this.getCurrentWeek()}</h3>
                <p class="week-info">${DateFormatter.formatWeekRange(this.getWeekDates().start, this.getWeekDates().end)} • ${this.getCurrentWeekDistance()}km total</p>
                ${this.renderCurrentWeek()}
            </div>

            <button class="coach-button">
                Talk with your coach
            </button>
        </div>
    `;
},

    calculateProgramStats() {
        const program = StateManager.getState('program');
        const today = new Date();

        const totalDistance = program.reduce((sum, workout) => sum + workout.distance, 0);
        const remainingWorkouts = program.filter(w => new Date(w.date) > today).length;
        const lastWorkoutDate = new Date(program[program.length - 1].date);
        const remainingDays = Math.ceil((lastWorkoutDate - today) / (1000 * 60 * 60 * 24));

        return { totalDistance, remainingWorkouts, remainingDays };
    },

    renderCurrentWeek() {
        const program = StateManager.getState('program');
        const currentWeekWorkouts = program.filter(workout => {
            const workoutDate = new Date(workout.date);
            return workoutDate >= DateFormatter.getCurrentWeekDates().firstDay &&
                   workoutDate <= DateFormatter.getCurrentWeekDates().lastDay;
        });

        return currentWeekWorkouts.map(workout => new WorkoutCard(workout).render()).join('');
    }
};