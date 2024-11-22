const SettingsView = {
    init() {
        this.attachListeners();
    },

    attachListeners() {
        const form = document.querySelector('.profile-form');
        if (form) {
            form.addEventListener('submit', this.handleProfileUpdate.bind(this));
        }
    },

    async handleProfileUpdate(event) {
        event.preventDefault();
        const form = event.target;
        
        // Récupérer les jours sélectionnés
        const selectedDays = Array.from(form.querySelectorAll('input[name="available_days"]:checked'))
            .map(input => input.value);

        const profile = {
            age: parseInt(form.age.value),
            poids: parseFloat(form.poids.value),
            taille: parseInt(form.taille.value),
            frequence_hebdomadaire: parseInt(form.frequence_hebdomadaire.value),
            objectif_principal: form.objectif_principal.value,
            distance_cible: parseInt(form.distance_cible.value),
            chrono_cible: form.chrono_cible.value,
            temps_actuel_5km: form.temps_actuel_5km.value,
            temps_actuel_10km: form.temps_actuel_10km.value,
            jours_disponibles_par_semaine: selectedDays,
            jour_sortie_longue: form.jour_sortie_longue.value
        };

        try {
            await API.updateProfile(profile);
            await StateManager.loadProgram();
            this.showSuccessMessage();
        } catch (error) {
            this.showErrorMessage(error);
        }
    },

    showSuccessMessage() {
        const message = document.createElement('div');
        message.className = 'success-message';
        message.textContent = 'Profile updated successfully!';
        document.querySelector('.settings-view').appendChild(message);
        setTimeout(() => message.remove(), 3000);
    },

    showErrorMessage(error) {
        const message = document.createElement('div');
        message.className = 'error-message';
        message.textContent = `Error updating profile: ${error.message}`;
        document.querySelector('.settings-view').appendChild(message);
        setTimeout(() => message.remove(), 3000);
    },

    getAvailableDays(profile) {
        // Gérer les différents formats possibles
        if (!profile.jours_disponibles_par_semaine) return [];
        if (typeof profile.jours_disponibles_par_semaine === 'string') {
            try {
                return JSON.parse(profile.jours_disponibles_par_semaine);
            } catch {
                return profile.jours_disponibles_par_semaine.split(',');
            }
        }
        if (Array.isArray(profile.jours_disponibles_par_semaine)) {
            return profile.jours_disponibles_par_semaine;
        }
        return [];
    },

    render() {
        const profile = StateManager.getState('profile');
        
        if (!profile) {
            return '<div class="loading"></div>';
        }

        const availableDays = this.getAvailableDays(profile);

        return `
            <div class="settings-view">
                <h1>Settings</h1>
                
                <section class="profile-section">
                    <h2>Your Profile</h2>
                    <form class="profile-form">
                        <div class="form-group">
                            <label for="age">Age</label>
                            <input type="number" id="age" name="age" value="${profile.age || ''}" required>
                        </div>

                        <div class="form-group">
                            <label for="poids">Weight (kg)</label>
                            <input type="number" step="0.1" id="poids" name="poids" value="${profile.poids || ''}" required>
                        </div>

                        <div class="form-group">
                            <label for="taille">Height (cm)</label>
                            <input type="number" id="taille" name="taille" value="${profile.taille || ''}" required>
                        </div>

                        <div class="form-group">
                            <label for="frequence_hebdomadaire">Weekly Frequency</label>
                            <input type="number" id="frequence_hebdomadaire" name="frequence_hebdomadaire" 
                                value="${profile.frequence_hebdomadaire || ''}" required min="1" max="7">
                        </div>

                        <div class="form-group">
                            <label for="objectif_principal">Main Goal</label>
                            <input type="text" id="objectif_principal" name="objectif_principal" 
                                value="${profile.objectif_principal || ''}" required>
                        </div>

                        <div class="form-group">
                            <label for="chrono_cible">Target Time</label>
                            <input type="text" id="chrono_cible" name="chrono_cible" 
                                value="${profile.chrono_cible || ''}" required>
                        </div>

                        <div class="form-group">
                            <label for="temps_actuel_5km">Current 5K Time</label>
                            <input type="text" id="temps_actuel_5km" name="temps_actuel_5km" 
                                value="${profile.temps_actuel_5km || ''}" required>
                        </div>

                        <div class="form-group">
                            <label for="temps_actuel_10km">Current 10K Time</label>
                            <input type="text" id="temps_actuel_10km" name="temps_actuel_10km" 
                                value="${profile.temps_actuel_10km || ''}" required>
                        </div>

                        <div class="form-group">
                            <label for="jour_sortie_longue">Long Run Day</label>
                            <select id="jour_sortie_longue" name="jour_sortie_longue">
                                <option value="Sunday" ${profile.jour_sortie_longue === 'Sunday' ? 'selected' : ''}>Sunday</option>
                                <option value="Saturday" ${profile.jour_sortie_longue === 'Saturday' ? 'selected' : ''}>Saturday</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label>Available Training Days</label>
                            <div class="days-selector">
                                ${['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                                    .map(day => `
                                        <label class="day-checkbox">
                                            <input type="checkbox" name="available_days" value="${day}"
                                                ${availableDays.includes(day) ? 'checked' : ''}>
                                            <span>${day.slice(0, 3)}</span>
                                        </label>
                                    `).join('')}
                            </div>
                        </div>

                        <button type="submit" class="btn-primary">Update Profile</button>
                    </form>
                </section>

                <section class="app-settings">
                    <h2>App Settings</h2>
                    <div class="settings-group">
                        <label class="setting-item">
                            <span>Notifications</span>
                            <input type="checkbox" class="toggle-switch" checked>
                        </label>
                        
                        <label class="setting-item">
                            <span>Dark Mode</span>
                            <input type="checkbox" class="toggle-switch" id="darkModeToggle">
                        </label>
                    </div>
                </section>

                <section class="data-management">
                    <h2>Data Management</h2>
                    <button class="btn-secondary" onclick="SettingsView.exportData()">Export Your Data</button>
                    <button class="btn-danger" onclick="SettingsView.clearData()">Clear All Data</button>
                </section>
            </div>
        `;
    },

    exportData() {
        const data = {
            profile: StateManager.getState('profile'),
            program: StateManager.getState('program'),
            chatHistory: StateManager.getState('chatHistory')
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'running-program-data.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    clearData() {
        if (confirm('Are you sure you want to clear all your data? This cannot be undone.')) {
            localStorage.clear();
            StateManager.init();
            window.location.reload();
        }
    }
};