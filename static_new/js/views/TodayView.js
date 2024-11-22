// Vue principale affichant l'entraînement du jour
const TodayView = {
    async init() {
        try {
            // Initialiser le programme si pas déjà fait
            if (!StateManager.getState('program')) {
                await StateManager.loadProgram();
            }
            this.attachListeners();
            this.updateWeekSelector();
        } catch (error) {
            console.error('Error initializing TodayView:', error);
        }
    },

    attachListeners() {
        // Gestion du sélecteur de semaine
        const weekSelector = document.querySelector('.week-selector');
        if (weekSelector) {
            weekSelector.addEventListener('change', (e) => {
                this.loadWeek(e.target.value);
            });
        }

        // Bouton "Talk with your coach"
        const coachButton = document.querySelector('.coach-button');
        if (coachButton) {
            coachButton.addEventListener('click', () => Chat.open());
        }
    },

    updateWeekSelector() {
        const program = StateManager.getState('program');
        if (!program) return;

        const weekGroups = this.groupWorkoutsByWeek(program);
        const weeks = Object.entries(weekGroups).sort(([weekA], [weekB]) => weekA - weekB);
        
        const weekSelector = document.querySelector('.week-selector');
        if (weekSelector) {
            weekSelector.innerHTML = weeks.map(([weekNum, weekData], index) => `
                <option value="${weekNum}" ${weekData.isCurrent ? 'selected' : ''}>
                    Week ${index + 1} / ${weeks.length}
                </option>
            `).join('');
        }
    },

    groupWorkoutsByWeek(workouts) {
        if (!Array.isArray(workouts)) return {};
        
        return workouts.reduce((weeks, workout) => {
            const date = new Date(workout.date);
            const weekNumber = DateFormatter.getWeekNumber(date);
            
            if (!weeks[weekNumber]) {
                weeks[weekNumber] = {
                    workouts: [],
                    isCurrent: this.isCurrentWeek(date)
                };
            }
            
            weeks[weekNumber].workouts.push(workout);
            return weeks;
        }, {});
    },

    isCurrentWeek(date) {
        const today = new Date();
        const weekStart = new Date(date);
        weekStart.setDate(weekStart.getDate() - weekStart.getDay());
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);
        return today >= weekStart && today <= weekEnd;
    },

    getTodayWorkout() {
        const program = StateManager.getState('program');
        if (!program || !Array.isArray(program)) return null;

        const today = new Date();
        return program.find(workout => {
            const workoutDate = new Date(workout.date);
            return workoutDate.toDateString() === today.toDateString();
        });
    },

    render() {
        const program = StateManager.getState('program');
        
        if (!program) {
            return '<div class="loading"></div>';
        }
    
        const todayWorkout = this.getTodayWorkout();
        const currentWeekWorkouts = this.getCurrentWeekWorkouts(program);
        
        return `
            <div class="today-view">
                <select class="week-selector"></select>
                
                <div class="card">
                    ${todayWorkout ? `
                        <div class="today-workout">
                            <h2>Today's workout</h2>
                            ${new WorkoutCard(todayWorkout).render()}
                        </div>
                    ` : `
                        <div class="no-workout">
                            <p>No workout scheduled for today</p>
                            <button class="btn-primary" onclick="Chat.open('I want to add a workout for today')">
                                Add a workout
                            </button>
                        </div>
                    `}
                </div>
    
                <div class="week-overview">
                    <h2>Your week program</h2>
                    ${currentWeekWorkouts.length > 0 ? `
                        <div class="card">
                            ${this.renderWeekOverview(currentWeekWorkouts)}
                        </div>
                    ` : `
                        <div class="card">
                            <p>No workouts scheduled this week</p>
                        </div>
                    `}
                </div>
    
                <button class="coach-button">
                    Talk with your coach
                </button>
            </div>
        `;
    },
    

    renderWeekOverview(workouts) {
        if (!Array.isArray(workouts) || workouts.length === 0) {
            return '<p>No workouts scheduled this week</p>';
        }

        return workouts
            .sort((a, b) => new Date(a.date) - new Date(b.date))
            .map(workout => new WorkoutCard(workout).render())
            .join('');
    },

    getCurrentWeekWorkouts(program) {
        if (!Array.isArray(program)) return [];

        const today = new Date();
        const weekStart = new Date(today);
        weekStart.setDate(weekStart.getDate() - weekStart.getDay());
        weekStart.setHours(0, 0, 0, 0);

        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);
        weekEnd.setHours(23, 59, 59, 999);

        return program.filter(workout => {
            const workoutDate = new Date(workout.date);
            return workoutDate >= weekStart && workoutDate <= weekEnd;
        });
    },

    loadWeek(weekNumber) {
        const program = StateManager.getState('program');
        if (!program) return;

        const weekGroups = this.groupWorkoutsByWeek(program);
        const selectedWeek = weekGroups[weekNumber];

        if (selectedWeek) {
            const weekOverviewContainer = document.querySelector('.week-overview');
            if (weekOverviewContainer) {
                weekOverviewContainer.innerHTML = `
                    <h2>Your week program</h2>
                    ${this.renderWeekOverview(selectedWeek.workouts)}
                `;
            }
        }
    }
};