from flask import Flask, render_template, request, jsonify
import re
import hashlib
import requests

# Create Flask app instance
app = Flask(__name__)

# Load common passwords when app starts
COMMON_PASSWORDS = set()

def load_common_passwords():
    """Load common passwords from file into memory"""
    try:
        with open('common_passwords.txt', 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                COMMON_PASSWORDS.add(line.strip().lower())
        print(f"Loaded {len(COMMON_PASSWORDS)} common passwords")
    except FileNotFoundError:
        print("Warning: common_passwords.txt not found!")

# Load passwords when app starts
load_common_passwords()


def check_password_breach(password):
    """
    Check if password has been exposed in data breaches using HaveIBeenPwned API

    Uses k-anonymity: Only sends first 5 chars of SHA-1 hash
    Returns: (is_breached: bool, breach_count: int)
    """
    # Hash the password with SHA-1
    sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()

    # Split into prefix (first 5 chars) and suffix (rest)
    hash_prefix = sha1_hash[:5]
    hash_suffix = sha1_hash[5:]

    # API endpoint
    url = f'https://api.pwnedpasswords.com/range/{hash_prefix}'

    try:
        # Make request to HIBP API
        response = requests.get(url, timeout=3)

        if response.status_code != 200:
            # If API fails, return False (don't block user)
            return False, 0

        # Parse response - format is "SUFFIX:COUNT\r\n"
        hashes = response.text.splitlines()

        for line in hashes:
            # Each line: "SUFFIX:COUNT"
            parts = line.split(':')
            if len(parts) == 2:
                suffix, count = parts
                if suffix == hash_suffix:
                    # Password found in breach!
                    return True, int(count)

        # Password not found in breaches
        return False, 0

    except requests.RequestException:
        # Network error - don't penalize user
        return False, 0


def check_password_strength(password):
    """
    Analyze password strength and return detailed results

    Returns a dictionary with:
    - score: 0-100
    - strength: Weak/Medium/Strong/Very Strong
    - feedback: List of suggestions
    - is_common: Boolean
    - has_patterns: Boolean
    """

    if not password:
        return {
            'score': 0,
            'strength': 'Weak',
            'feedback': ['Password cannot be empty'],
            'is_common': False,
            'has_patterns': False
        }

    score = 0
    feedback = []

    # 1. Check length (0-30 points)
    length = len(password)
    if length < 8:
        feedback.append('Password should be at least 8 characters')
        score += length * 2
    elif length < 12:
        score += 20
    elif length < 16:
        score += 25
    else:
        score += 30

    # 2. Check character variety (0-40 points)
    has_lower = bool(re.search(r'[a-z]', password))
    has_upper = bool(re.search(r'[A-Z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))

    variety_score = 0
    if has_lower:
        variety_score += 10
    else:
        feedback.append('Add lowercase letters')

    if has_upper:
        variety_score += 10
    else:
        feedback.append('Add uppercase letters')

    if has_digit:
        variety_score += 10
    else:
        feedback.append('Add numbers')

    if has_special:
        variety_score += 10
    else:
        feedback.append('Add special characters (!@#$%^&*)')

    score += variety_score

    # 3. Check for common passwords (0-20 points penalty)
    is_common = password.lower() in COMMON_PASSWORDS
    if is_common:
        score -= 20
        feedback.append('This is a commonly used password!')

    # 4. Check for patterns (0-10 points penalty each)
    has_patterns = False

    # Sequential numbers: 123, 234, etc.
    if re.search(r'(012|123|234|345|456|567|678|789)', password):
        score -= 10
        feedback.append('Avoid sequential numbers (123, 456, etc.)')
        has_patterns = True

    # Sequential letters: abc, bcd, etc.
    if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
        score -= 10
        feedback.append('Avoid sequential letters (abc, xyz, etc.)')
        has_patterns = True

    # Repeated characters: aaa, 111, etc.
    if re.search(r'(.)\1{2,}', password):
        score -= 10
        feedback.append('Avoid repeated characters (aaa, 111, etc.)')
        has_patterns = True

    # Keyboard patterns: qwerty, asdf, etc.
    keyboard_patterns = ['qwerty', 'asdfgh', 'zxcvbn', 'qwertyuiop', 'asdfghjkl']
    for pattern in keyboard_patterns:
        if pattern in password.lower():
            score -= 10
            feedback.append('Avoid keyboard patterns (qwerty, asdf, etc.)')
            has_patterns = True
            break

    # Ensure score is between 0-100
    score = max(0, min(100, score))

    # Determine strength level
    if score < 30:
        strength = 'Weak'
    elif score < 60:
        strength = 'Medium'
    elif score < 80:
        strength = 'Strong'
    else:
        strength = 'Very Strong'

    # 5. Check if password was in data breaches
    is_breached, breach_count = check_password_breach(password)
    if is_breached:
        score -= 30  # Heavy penalty for breached passwords
        feedback.append(f'WARNING: This password has been exposed in {breach_count:,} data breaches!')

    # Recalculate strength after breach check
    score = max(0, min(100, score))
    if score < 30:
        strength = 'Weak'
    elif score < 60:
        strength = 'Medium'
    elif score < 80:
        strength = 'Strong'
    else:
        strength = 'Very Strong'

    # Add positive feedback if strong
    if score >= 80 and not feedback:
        feedback.append('Excellent password!')

    return {
        'score': score,
        'strength': strength,
        'feedback': feedback,
        'is_common': is_common,
        'has_patterns': has_patterns,
        'is_breached': is_breached,
        'breach_count': breach_count,
        'length': length
    }


# Route for homepage
@app.route('/')
def index():
    return "Hello, Flask! Password Checker Coming Soon..."


# Route for checking password strength (POST - for API/JavaScript)
@app.route('/check-password', methods=['POST'])
def check_password():
    """API endpoint to check password strength"""
    password = request.json.get('password', '')

    # Analyze password
    result = check_password_strength(password)

    return jsonify(result)


# Test route (GET - for browser testing)
@app.route('/test/<password>')
def test_password(password):
    """Test route - visit http://localhost:5000/test/yourpassword"""
    result = check_password_strength(password)

    # Format as readable HTML
    html = f"""
    <h1>Password Strength Checker - Test</h1>
    <p><strong>Password:</strong> {password}</p>
    <p><strong>Score:</strong> {result['score']}/100</p>
    <p><strong>Strength:</strong> <span style="color: {'red' if result['strength'] == 'Weak' else 'orange' if result['strength'] == 'Medium' else 'green'};">{result['strength']}</span></p>
    <p><strong>Length:</strong> {result['length']} characters</p>
    <p><strong>Common Password:</strong> {'Yes ⚠️' if result['is_common'] else 'No ✓'}</p>
    <p><strong>Has Patterns:</strong> {'Yes ⚠️' if result['has_patterns'] else 'No ✓'}</p>
    <p><strong>Data Breach:</strong> {'Yes - Found in ' + f"{result['breach_count']:,}" + ' breaches! 🚨' if result['is_breached'] else 'No ✓'}</p>
    <h3>Feedback:</h3>
    <ul>
    """

    for item in result['feedback']:
        html += f"<li>{item}</li>"

    html += """
    </ul>
    <p><a href="/">Back to Home</a></p>
    """

    return html


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
