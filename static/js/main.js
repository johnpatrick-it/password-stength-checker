// DOM Elements
const passwordInput = document.getElementById('password');
const togglePasswordBtn = document.getElementById('togglePassword');
const resultsDiv = document.getElementById('results');
const emptyState = document.getElementById('emptyState');
const strengthBar = document.getElementById('strengthBar');
const strengthText = document.getElementById('strengthText');
const scoreText = document.getElementById('scoreText');
const lengthText = document.getElementById('lengthText');
const commonText = document.getElementById('commonText');
const patternsText = document.getElementById('patternsText');
const breachText = document.getElementById('breachText');
const breachAlert = document.getElementById('breachAlert');
const breachMessage = document.getElementById('breachMessage');
const feedbackList = document.getElementById('feedbackList');

// Debounce timer
let debounceTimer;

// Toggle password visibility
togglePasswordBtn.addEventListener('click', () => {
    const type = passwordInput.type === 'password' ? 'text' : 'password';
    passwordInput.type = type;
});

// Listen for password input
passwordInput.addEventListener('input', (e) => {
    const password = e.target.value;

    // Clear previous timer
    clearTimeout(debounceTimer);

    // If empty, show empty state
    if (password.length === 0) {
        showEmptyState();
        return;
    }

    // Debounce API call (wait 300ms after user stops typing)
    debounceTimer = setTimeout(() => {
        checkPassword(password);
    }, 300);
});

// Show empty state
function showEmptyState() {
    resultsDiv.classList.add('hidden');
    emptyState.classList.remove('hidden');
}

// Hide empty state
function hideEmptyState() {
    emptyState.classList.add('hidden');
    resultsDiv.classList.remove('hidden');
}

// Check password strength via API
async function checkPassword(password) {
    try {
        const response = await fetch('/check-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password: password })
        });

        if (!response.ok) {
            throw new Error('API request failed');
        }

        const data = await response.json();
        updateUI(data);

    } catch (error) {
        console.error('Error checking password:', error);
        // Show error state
        showError();
    }
}

// Update UI with results
function updateUI(data) {
    hideEmptyState();

    // Update score
    scoreText.textContent = data.score;

    // Update strength text and color
    strengthText.textContent = data.strength;
    strengthText.className = `text-lg font-bold ${getStrengthColor(data.strength)}`;

    // Update progress bar
    strengthBar.style.width = `${data.score}%`;
    strengthBar.className = `h-3 rounded-full transition-all duration-500 ease-out ${getStrengthBgColor(data.strength)}`;

    // Update stats
    lengthText.textContent = `${data.length} chars`;

    commonText.textContent = data.is_common ? '⚠️ Yes' : '✓ No';
    commonText.className = `text-xl font-semibold ${data.is_common ? 'text-red-600' : 'text-green-600'}`;

    patternsText.textContent = data.has_patterns ? '⚠️ Yes' : '✓ No';
    patternsText.className = `text-xl font-semibold ${data.has_patterns ? 'text-orange-600' : 'text-green-600'}`;

    breachText.textContent = data.is_breached ? '🚨 Yes' : '✓ No';
    breachText.className = `text-xl font-semibold ${data.is_breached ? 'text-red-600' : 'text-green-600'}`;

    // Show/hide breach alert
    if (data.is_breached) {
        breachAlert.classList.remove('hidden');
        breachMessage.innerHTML = `WARNING: This password was found in ${data.breach_count.toLocaleString()} data breaches!
            <a href="https://haveibeenpwned.com/Passwords" target="_blank" class="underline hover:text-red-900 font-bold">
                Learn more →
            </a>`;
    } else {
        breachAlert.classList.add('hidden');
    }

    // Update feedback list
    updateFeedback(data.feedback);
}

// Update feedback list
function updateFeedback(feedback) {
    feedbackList.innerHTML = '';

    if (feedback.length === 0) {
        const li = document.createElement('li');
        li.className = 'flex items-start text-green-700';
        li.innerHTML = `
            <svg class="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
            </svg>
            <span>All good! Strong password.</span>
        `;
        feedbackList.appendChild(li);
        return;
    }

    feedback.forEach(item => {
        const li = document.createElement('li');
        const isWarning = item.includes('WARNING') || item.includes('common') || item.includes('breach');
        const isPositive = item.includes('Excellent');

        li.className = `flex items-start ${isWarning ? 'text-red-700' : isPositive ? 'text-green-700' : 'text-gray-700'}`;

        const icon = isWarning
            ? `<svg class="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
               </svg>`
            : isPositive
            ? `<svg class="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
               </svg>`
            : `<svg class="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
               </svg>`;

        // Add helpful links based on feedback type
        let feedbackText = item;
        let resourceLink = '';

        if (item.includes('commonly used password')) {
            resourceLink = ' <a href="https://nordpass.com/most-common-passwords-list/" target="_blank" class="underline hover:opacity-80">View common passwords →</a>';
        } else if (item.includes('sequential') || item.includes('patterns') || item.includes('repeated')) {
            resourceLink = ' <a href="https://pages.nist.gov/800-63-3/sp800-63b.html" target="_blank" class="underline hover:opacity-80">NIST Guidelines →</a>';
        } else if (item.includes('8 characters')) {
            resourceLink = ' <a href="https://www.ncsc.gov.uk/collection/passwords" target="_blank" class="underline hover:opacity-80">Password best practices →</a>';
        }

        li.innerHTML = `${icon}<span>${feedbackText}${resourceLink}</span>`;
        feedbackList.appendChild(li);
    });
}

// Get text color based on strength
function getStrengthColor(strength) {
    const colors = {
        'Weak': 'text-red-600',
        'Medium': 'text-orange-500',
        'Strong': 'text-blue-600',
        'Very Strong': 'text-green-600'
    };
    return colors[strength] || 'text-gray-600';
}

// Get background color based on strength
function getStrengthBgColor(strength) {
    const colors = {
        'Weak': 'bg-red-500',
        'Medium': 'bg-orange-500',
        'Strong': 'bg-blue-500',
        'Very Strong': 'bg-green-500'
    };
    return colors[strength] || 'bg-gray-500';
}

// Show error state
function showError() {
    hideEmptyState();
    strengthText.textContent = 'Error';
    strengthText.className = 'text-lg font-bold text-red-600';
    feedbackList.innerHTML = '<li class="text-red-600">Failed to check password. Please try again.</li>';
}
