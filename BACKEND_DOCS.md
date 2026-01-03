# Password Strength Checker - Backend Documentation

## Overview
A Flask-based REST API that analyzes password strength using multiple security criteria.

---

## Tech Stack
- **Python 3.14.0**
- **Flask 3.1.2** - Web framework
- **requests 2.32.5** - HTTP library for API calls
- **re (regex)** - Pattern matching
- **hashlib** - SHA-1 hashing for breach checking

---

## Project Structure
```
password-strength-checker/
├── venv/                      # Virtual environment (not committed)
├── app.py                     # Main Flask application
├── common_passwords.txt       # 10,000 most common passwords
├── requirements.txt           # Python dependencies
├── .gitignore                # Git ignore rules
└── readme.md                 # Project overview
```

---

## Features

### 1. Password Length Scoring (0-30 points)
- **< 8 characters:** 2 points per character
- **8-11 characters:** 20 points
- **12-15 characters:** 25 points
- **16+ characters:** 30 points

### 2. Character Variety (0-40 points)
- **Lowercase letters:** +10 points
- **Uppercase letters:** +10 points
- **Numbers:** +10 points
- **Special characters:** +10 points (!@#$%^&*(),.?":{}|<>)

### 3. Common Password Detection (-20 points)
- Checks against 10,000 most common passwords
- Loaded into memory on app startup for fast lookup
- Case-insensitive matching
- **Source:** SecLists Common-Credentials

### 4. Pattern Detection (-10 points each)
- **Sequential numbers:** 012, 123, 234, etc.
- **Sequential letters:** abc, bcd, xyz, etc.
- **Repeated characters:** aaa, 111, etc. (3+ repeats)
- **Keyboard patterns:** qwerty, asdfgh, zxcvbn

### 5. Data Breach Checking (-30 points)
- Uses **HaveIBeenPwned API**
- Checks 600+ million breached passwords
- **k-Anonymity:** Only sends first 5 chars of SHA-1 hash
- Returns breach count (how many times password was leaked)
- Network-safe: Returns false on API failure (doesn't block users)

---

## Scoring System

**Total Score: 0-100 points**

| Score Range | Strength Level |
|-------------|----------------|
| 0-29        | Weak          |
| 30-59       | Medium        |
| 60-79       | Strong        |
| 80-100      | Very Strong   |

---

## API Endpoints

### 1. Homepage
```
GET /
```
Returns: Simple text message

### 2. Check Password (API)
```
POST /check-password
Content-Type: application/json

Request Body:
{
  "password": "yourpassword"
}

Response:
{
  "score": 85,
  "strength": "Very Strong",
  "feedback": ["Excellent password!"],
  "is_common": false,
  "has_patterns": false,
  "is_breached": false,
  "breach_count": 0,
  "length": 18
}
```

### 3. Test Route (Browser-friendly)
```
GET /test/<password>
```
Example: `http://localhost:5000/test/password123`

Returns: HTML page with formatted results

---

## Core Functions

### `load_common_passwords()`
- Loads `common_passwords.txt` into a Python `set` on app startup
- Set provides O(1) lookup time
- Case-insensitive storage (all lowercase)

### `check_password_breach(password)`
**HaveIBeenPwned k-Anonymity Implementation**

1. Hash password with SHA-1
2. Split hash: prefix (first 5 chars) + suffix (remaining)
3. Send only prefix to API: `https://api.pwnedpasswords.com/range/{prefix}`
4. API returns all hashes starting with that prefix
5. Check locally if full hash matches
6. Returns: `(is_breached: bool, breach_count: int)`

**Privacy:** Password never leaves your server!

### `check_password_strength(password)`
Main analysis function:
1. Validates password (not empty)
2. Calculates length score
3. Checks character variety
4. Detects common passwords
5. Identifies patterns using regex
6. Checks breach database
7. Calculates final score and strength level
8. Generates feedback messages

Returns comprehensive dictionary with all results.

---

## Security Features

### 1. k-Anonymity for Breach Checking
- Password hashed locally with SHA-1
- Only first 5 characters of hash sent to API
- Full password never transmitted
- API cannot reverse-engineer password from prefix

### 2. Timeout Protection
```python
response = requests.get(url, timeout=3)
```
- 3-second timeout prevents hanging
- Graceful failure on network issues

### 3. Error Handling
- File not found: Warns but continues (common_passwords.txt)
- Network errors: Returns false, doesn't block user
- Invalid input: Returns weak score with feedback

---

## Regex Patterns Used

```python
r'[a-z]'                    # Lowercase letters
r'[A-Z]'                    # Uppercase letters
r'\d'                       # Digits
r'[!@#$%^&*(),.?":{}|<>]'  # Special characters
r'(012|123|234|...)'        # Sequential numbers
r'(abc|bcd|cde|...)'        # Sequential letters
r'(.)\1{2,}'                # Repeated characters (3+)
```

---

## Running the Application

### Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Run
```bash
python app.py
```

Server starts on: `http://127.0.0.1:5000`

Debug mode: ON (auto-reloads on code changes)

---

## Example Test Cases

| Password | Expected Result |
|----------|----------------|
| `password` | Weak - Common + Breached |
| `qwerty123` | Weak - Keyboard pattern + Breached |
| `abc123` | Weak - Sequential letters/numbers |
| `aaaa1111` | Weak - Repeated characters |
| `MyS3cure!Pass@2024` | Very Strong - All criteria met |
| `P@ssw0rd!` | Medium - Common + Breached despite variety |

---

## Future Enhancements (Frontend - Next Phase)

1. HTML/CSS/JavaScript frontend
2. Real-time password checking as user types
3. Visual strength indicator (progress bar)
4. Animated feedback messages
5. Copy-to-clipboard for generated passwords
6. Password generator

---

## Dependencies

```
Flask==3.1.2
requests==2.32.5
```

Plus automatic dependencies:
- Jinja2 (templating)
- Werkzeug (WSGI server)
- click (CLI)
- itsdangerous (security)
- MarkupSafe (safe rendering)

---

## Notes

- Virtual environment (`venv/`) should never be committed to Git
- API calls to HaveIBeenPwned are rate-limited (reasonable use only)
- Common passwords list can be upgraded to 100k for more coverage
- SHA-1 used only for breach checking (not for password storage!)
- Debug mode should be disabled in production

---

**Backend Status:** ✅ Complete

**Created:** 2026-01-03

**Author:** Patrick Haguimit (with Claude Code)
