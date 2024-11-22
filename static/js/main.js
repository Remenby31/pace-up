// Global state
let currentlySelectedSession = null;
let messageHistory = [];


// Initialize the app
window.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/init-program', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            updateProfile(data.profile);
            updateProgram(data.program);
            
            if (data.isNew) {
                addMessage('coach', "Bienvenue ! J'ai créé un nouveau programme d'entraînement personnalisé pour vous.");
                if (data.explanation) {
                    addMessage('coach', data.explanation);
                }
            } else {
                addMessage('coach', "Bienvenue ! J'ai chargé votre programme d'entraînement existant.");
                addMessage('coach', "Comment puis-je vous aider aujourd'hui ?");
            }
        } else {
            addMessage('error', data.error);
        }

        await initializeCalendarSync();

    } catch (error) {
        addMessage('error', "Erreur lors de l'initialisation du programme");
    }
});

// Chat form submission
document.getElementById('chat-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    if (!message) return;
    
    input.value = '';
    clearSelectedSession();
    
    addMessage('user', message);
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message,
                history: messageHistory.slice(-10) // Send last 10 messages for context
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            addMessage('coach', data.response);
            if (data.changes_made) {
                const programResponse = await fetch('/get-program');
                const programData = await programResponse.json();
                if (programData.success) {
                    updateProgram(programData.program);
                }
            }
        } else {
            addMessage('error', data.error);
        }
    } catch (error) {
        addMessage('error', "Erreur lors de l'envoi du message");
    }
});


function addMessage(type, content) {
    const message = { role: type, content };
    messageHistory.push(message);
    
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message mb-4 ${type === 'user' ? 'text-right' : ''}`;
    
    const messageBubble = document.createElement('div');
    messageBubble.className = `inline-block rounded-lg px-4 py-2 max-w-[80%] ${
        type === 'user' 
            ? 'bg-[#FF6B35] text-white' 
            : type === 'error' 
                ? 'bg-red-500 text-white'
                : 'bg-[#f1f1f1]'
    }`;
    messageBubble.textContent = content;
    
    messageDiv.appendChild(messageBubble);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


function updateProfile(profile) {
    const profileSection = document.getElementById('profile-section');
    profileSection.innerHTML = `
        <div class="bg-[#f1f1f1] rounded-lg p-4 mb-4">
            <h2 class="text-xl font-bold mb-3 text-[#FF6B35]">Profil</h2>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <p class="font-bold">Objectif:</p>
                    <p>${profile.objectif_principal}</p>
                </div>
                <div>
                    <p class="font-bold">Chrono cible:</p>
                    <p>${profile.chrono_cible}</p>
                </div>
                <div>
                    <p class="font-bold">Performance 5km:</p>
                    <p>${profile.temps_actuel_5km}</p>
                </div>
                <div>
                    <p class="font-bold">Performance 10km:</p>
                    <p>${profile.temps_actuel_10km}</p>
                </div>
            </div>
            <div class="calendar-sync-container">
                <button class="calendar-sync-button" onclick="showCalendarMenu(event)">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"/>
                    </svg>
                    Synchroniser le calendrier
                </button>
            </div>
        </div>
    `;
}


function updateProgram(sessions) {
    const programSection = document.getElementById('program-section');
    programSection.innerHTML = `
        <h2 class="text-xl font-bold mb-4 text-[#FF6B35]">Programme d'entraînement</h2>
        <div class="space-y-4">
            ${sessions.map(session => `
                <div class="program-card bg-[#f1f1f1] rounded-lg p-4" 
                     data-date="${session.date}" 
                     onclick="handleSessionClick(this, '${session.date}')">
                    <div class="session-date">
                        ${formatDate(session.date)}
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="session-tag">
                            ${session.type_de_seance}
                        </span>
                        <span class="session-distance">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M6.293 2.293a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L8 5.414V13a1 1 0 11-2 0V5.414L4.707 6.707a1 1 0 01-1.414-1.414l3-3zM14 7a1 1 0 01-1 1h-2a1 1 0 110-2h2a1 1 0 011 1z" clip-rule="evenodd"/>
                            </svg>
                            ${session.distance} km
                        </span>
                    </div>
                    <div class="session-description">
                        ${session.description}
                    </div>
                    <div class="tooltip">
                        Cliquez pour modifier cette séance
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('fr-FR', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

function handleSessionClick(element, date) {
    clearSelectedSession();
    element.classList.add('selected');
    
    // Mettre le focus sur l'input avec un message suggéré
    const input = document.getElementById('message-input');
    input.value = `Concernant la séance du ${formatDate(date)}, `;
    input.focus();
}

function clearSelectedSession() {
    const selected = document.querySelector('.program-card.selected');
    if (selected) {
        selected.classList.remove('selected');
    }
    currentlySelectedSession = null;
}

// Calendar fonctions
async function initializeCalendarSync() {
    try {
        const response = await fetch('/calendar-url');
        const data = await response.json();
        
        if (data.success) {
            window.calendarUrls = data.urls;
        } else {
            console.error('Failed to fetch calendar URLs');
        }
    } catch (error) {
        console.error('Error initializing calendar sync:', error);
    }
}

function showCalendarMenu(event) {
    event.preventDefault();
    
    const existingMenu = document.querySelector('.calendar-sync-menu');
    if (existingMenu) {
        existingMenu.remove();
        return;
    }
    
    const button = event.currentTarget;
    const menu = document.createElement('div');
    menu.className = 'calendar-sync-menu';
    menu.innerHTML = `
        <div class="calendar-sync-menu-item" onclick="copyCalendarUrl('ics_feed')">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"/>
                <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"/>
            </svg>
            Copier l'URL du calendrier
        </div>
        <div class="calendar-sync-menu-item" onclick="openCalendarUrl('google_calendar')">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M15 5v2a2 2 0 01-2 2H7a2 2 0 01-2-2V5a2 2 0 012-2h6a2 2 0 012 2zm-2 4v8a2 2 0 01-2 2H7a2 2 0 01-2-2V9h8z"/>
            </svg>
            Ajouter à Google Calendar
        </div>
        <div class="calendar-sync-menu-item" onclick="openCalendarUrl('ical')">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"/>
            </svg>
            Ajouter à Apple/Outlook
        </div>
    `;
    
    // Position the menu
    const buttonRect = button.getBoundingClientRect();
    menu.style.top = `${buttonRect.bottom + window.scrollY + 5}px`;
    menu.style.left = `${buttonRect.left + window.scrollX}px`;
    
    document.body.appendChild(menu);
    setTimeout(() => menu.classList.add('active'), 0);
    
    // Close menu when clicking outside
    document.addEventListener('click', function closeMenu(e) {
        if (!menu.contains(e.target) && e.target !== button) {
            menu.remove();
            document.removeEventListener('click', closeMenu);
        }
    });
}

async function copyCalendarUrl(type) {
    if (!window.calendarUrls || !window.calendarUrls[type]) {
        console.error('Calendar URL not available');
        return;
    }
    
    try {
        await navigator.clipboard.writeText(window.calendarUrls[type]);
        showCopySuccess();
    } catch (err) {
        console.error('Failed to copy URL:', err);
    }
}

function openCalendarUrl(type) {
    if (!window.calendarUrls || !window.calendarUrls[type]) {
        console.error('Calendar URL not available');
        return;
    }
    
    window.open(window.calendarUrls[type], '_blank');
}

function showCopySuccess() {
    const notification = document.createElement('div');
    notification.className = 'copy-success';
    notification.textContent = 'URL copiée avec succès !';
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}