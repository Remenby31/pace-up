// static/auth.js
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const errorMessage = document.getElementById('error-message');
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // Configuration par défaut pour fetch
    function fetchWithCSRF(url, options = {}) {
        return fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                username: loginForm.username.value,
                password: loginForm.password.value
            };

            try {
                const response = await fetchWithCSRF('/login', {
                    method: 'POST',
                    body: JSON.stringify(formData)
                });

                const result = await response.json();
                
                if (result.success) {
                    window.location.href = result.redirect;
                } else {
                    errorMessage.textContent = result.message;
                    errorMessage.classList.add('visible');
                }
            } catch (error) {
                errorMessage.textContent = "Une erreur est survenue lors de la connexion";
                errorMessage.classList.add('visible');
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (registerForm.password.value !== registerForm.password_confirm.value) {
                errorMessage.textContent = "Les mots de passe ne correspondent pas";
                errorMessage.classList.add('visible');
                return;
            }

            const formData = {
                username: registerForm.username.value,
                password: registerForm.password.value
            };

            try {
                const response = await fetchWithCSRF('/register', {
                    method: 'POST',
                    body: JSON.stringify(formData)
                });

                const result = await response.json();
                
                if (result.success) {
                    window.location.href = '/login?registered=true';
                } else {
                    errorMessage.textContent = result.message;
                    errorMessage.classList.add('visible');
                }
            } catch (error) {
                errorMessage.textContent = "Une erreur est survenue lors de l'inscription";
                errorMessage.classList.add('visible');
            }
        });
    }

    // Gérer le message de succès après l'inscription
    if (window.location.search.includes('registered=true')) {
        const successMessage = document.createElement('div');
        successMessage.className = 'success-message';
        successMessage.textContent = "Inscription réussie ! Vous pouvez maintenant vous connecter.";
        document.body.appendChild(successMessage);
        
        setTimeout(() => {
            successMessage.remove();
        }, 3000);
    }
});