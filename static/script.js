const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.querySelector('.container');
const messageArea = document.getElementById('message-area');

// New: Get the mobile toggle buttons
const signInMobileToggle = document.getElementById('signInMobileToggle');
const signUpMobileToggle = document.getElementById('signUpMobileToggle');

// New: Get the dark mode toggle button
const darkModeToggle = document.querySelector('.dark-mode-toggle');


// Desktop 'Sign Up' button click
if (signUpButton) {
    signUpButton.addEventListener('click', () => {
        container.classList.add("right-panel-active");
    });
}

// Desktop 'Sign In' button click
if (signInButton) {
    signInButton.addEventListener('click', () => {
        container.classList.remove("right-panel-active");
    });
}

// Mobile 'Sign Up' toggle button click (from Login form)
if (signInMobileToggle) {
    signInMobileToggle.addEventListener('click', () => {
        container.classList.add("right-panel-active"); // Activates the sign-up view
    });
}

// Mobile 'Sign In' toggle button click (from Register form)
if (signUpMobileToggle) {
    signUpMobileToggle.addEventListener('click', () => {
        container.classList.remove("right-panel-active"); // Activates the sign-in view
    });
}


// Function to display server messages (e.g., from Flask Flash messages)
function displayMessage(message, type) {
    if (messageArea) {
        messageArea.innerHTML = `<div class="message ${type}">${message}</div>`;
        setTimeout(() => {
            messageArea.innerHTML = ''; // Clear message after 5 seconds
        }, 5000);
    }
}

// Check for messages in the URL (e.g., ?message=success&type=success)
const urlParams = new URLSearchParams(window.location.search);
const msg = urlParams.get('message');
const type = urlParams.get('type');

if (msg && type) {
    displayMessage(decodeURIComponent(msg), type);
    // Clear URL parameters so the message doesn't reappear on refresh
    history.replaceState({}, document.title, window.location.pathname);
}

// Add a listener for form submissions (optional, for feedback before redirection)
// Or use AJAX for asynchronous submission
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', (event) => {
        // Example: Disable button to prevent multiple clicks
        const submitButton = event.submitter;
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Processando...';
        }
    });
});


// Dark Mode Toggle Logic
if (darkModeToggle) {
    darkModeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        // Save user preference to localStorage
        if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('darkMode', 'enabled');
        } else {
            localStorage.setItem('darkMode', 'disabled');
        }
    });

    // Check for saved dark mode preference on page load
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
    }
}