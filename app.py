from flask import Flask, render_template, request, jsonify
import re
import hashlib
import requests
import random
import string

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


def enhance_password(password):
    """
    Enhance a weak password by making it stronger

    Returns: enhanced_password (string)
    """
    if not password:
        # Generate a completely random password if empty
        return generate_strong_password()

    enhanced = password

    # 1. Ensure minimum length of 16 characters
    if len(enhanced) < 16:
        # Add random characters to reach 16 chars
        chars_needed = 16 - len(enhanced)
        random_chars = ''.join(random.choices(
            string.ascii_letters + string.digits + string.punctuation,
            k=chars_needed
        ))
        enhanced += random_chars

    # 2. Ensure it has all character types
    has_lower = bool(re.search(r'[a-z]', enhanced))
    has_upper = bool(re.search(r'[A-Z]', enhanced))
    has_digit = bool(re.search(r'\d', enhanced))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', enhanced))

    additions = []
    if not has_lower:
        additions.append(random.choice(string.ascii_lowercase))
    if not has_upper:
        additions.append(random.choice(string.ascii_uppercase))
    if not has_digit:
        additions.append(random.choice(string.digits))
    if not has_special:
        additions.append(random.choice('!@#$%^&*'))

    if additions:
        # Insert missing characters at random positions
        enhanced_list = list(enhanced)
        for char in additions:
            pos = random.randint(0, len(enhanced_list))
            enhanced_list.insert(pos, char)
        enhanced = ''.join(enhanced_list)

    # 3. Replace sequential patterns with random chars
    # Replace sequential numbers
    enhanced = re.sub(r'(012|123|234|345|456|567|678|789)',
                     lambda m: ''.join(random.choices(string.digits, k=len(m.group()))),
                     enhanced)

    # Replace sequential letters (case-insensitive)
    sequential_letters = ['abc', 'bcd', 'cde', 'def', 'efg', 'fgh', 'ghi', 'hij',
                         'ijk', 'jkl', 'klm', 'lmn', 'mno', 'nop', 'opq', 'pqr',
                         'qrs', 'rst', 'stu', 'tuv', 'uvw', 'vwx', 'wxy', 'xyz']
    for seq in sequential_letters:
        if seq in enhanced.lower():
            # Find and replace while preserving case
            pattern = re.compile(re.escape(seq), re.IGNORECASE)
            enhanced = pattern.sub(''.join(random.choices(string.ascii_letters, k=3)), enhanced)

    # 4. Replace keyboard patterns
    keyboard_patterns = ['qwerty', 'asdfgh', 'zxcvbn', 'qwertyuiop', 'asdfghjkl']
    for pattern in keyboard_patterns:
        if pattern in enhanced.lower():
            replacement = ''.join(random.choices(string.ascii_letters, k=len(pattern)))
            enhanced = re.sub(re.escape(pattern), replacement, enhanced, flags=re.IGNORECASE)

    # 5. Replace repeated characters (3 or more)
    enhanced = re.sub(r'(.)\1{2,}', lambda m: m.group(1) + ''.join(random.choices(
        string.ascii_letters + string.digits, k=len(m.group()) - 1
    )), enhanced)

    # 6. If it's still a common password, add random suffix
    if enhanced.lower() in COMMON_PASSWORDS:
        enhanced += '-' + ''.join(random.choices(
            string.ascii_letters + string.digits, k=6
        ))

    return enhanced


def generate_strong_password(length=16):
    """Generate a completely random strong password"""
    # Ensure at least one of each type
    password_chars = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice('!@#$%^&*')
    ]

    # Fill the rest randomly
    remaining = length - len(password_chars)
    password_chars.extend(random.choices(
        string.ascii_letters + string.digits + '!@#$%^&*',
        k=remaining
    ))

    # Shuffle to avoid predictable pattern
    random.shuffle(password_chars)

    return ''.join(password_chars)


# Route for homepage
@app.route('/')
def index():
    return render_template('index.html')


# Route for checking password strength (POST - for API/JavaScript)
@app.route('/check-password', methods=['POST'])
def check_password():
    """API endpoint to check password strength"""
    password = request.json.get('password', '')

    # Analyze password
    result = check_password_strength(password)

    return jsonify(result)


# Route for enhancing weak passwords
@app.route('/enhance-password', methods=['POST'])
def enhance_password_endpoint():
    """API endpoint to enhance a weak password"""
    password = request.json.get('password', '')

    # Enhance the password
    enhanced = enhance_password(password)

    # Also return the strength check of the enhanced password
    result = check_password_strength(enhanced)
    result['enhanced_password'] = enhanced

    return jsonify(result)


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
