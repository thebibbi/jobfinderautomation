# Authentication & Authorization Guide

Complete guide to setting up authentication and authorization for the Job Automation System.

---

## Table of Contents

1. [Overview](#overview)
2. [Google OAuth 2.0 Setup](#google-oauth-20-setup)
3. [API Key Authentication](#api-key-authentication)
4. [Environment Configuration](#environment-configuration)
5. [Security Best Practices](#security-best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The Job Automation System uses multiple authentication methods depending on the feature:

| Feature | Authentication Method | Purpose |
|---------|----------------------|---------|
| Google Calendar | OAuth 2.0 | Access user's Google Calendar |
| Google Drive | OAuth 2.0 | Upload documents to Drive |
| Gmail API | OAuth 2.0 | Send email notifications |
| API Endpoints | API Key (Production) | Secure API access |
| WebSocket | Token (Production) | Secure real-time connection |

**Current Status**:
- ✅ OAuth 2.0 for Google services implemented
- 🔄 API Key authentication ready for production
- 🔄 WebSocket authentication ready for production

---

## Google OAuth 2.0 Setup

### Prerequisites

- Google account
- Access to Google Cloud Console

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project details:
   - **Project Name**: "Job Automation System"
   - **Location**: Your organization or "No organization"
4. Click "Create"

### Step 2: Enable Required APIs

Enable these APIs for your project:

1. Navigate to "APIs & Services" → "Library"

2. **Google Calendar API**:
   - Search for "Google Calendar API"
   - Click "Enable"
   - Used for: Interview scheduling, deadline reminders

3. **Google Drive API**:
   - Search for "Google Drive API"
   - Click "Enable"
   - Used for: Document upload (resumes, cover letters)

4. **Gmail API** (Optional):
   - Search for "Gmail API"
   - Click "Enable"
   - Used for: Email notifications

### Step 3: Create OAuth 2.0 Credentials

1. Navigate to "APIs & Services" → "Credentials"

2. Click "Create Credentials" → "OAuth client ID"

3. Configure OAuth consent screen (first time):
   - User Type: **External** (for personal use) or **Internal** (for organization)
   - Click "Create"

4. Fill in OAuth consent screen:
   ```
   App name: Job Automation System
   User support email: your-email@example.com
   Developer contact: your-email@example.com
   ```
   - Click "Save and Continue"

5. Add Scopes:
   ```
   ../auth/calendar - Google Calendar
   ../auth/drive.file - Google Drive (file access)
   ../auth/gmail.send - Gmail (send emails)
   ```
   - Click "Save and Continue"

6. Add Test Users (if External):
   - Add your email address
   - Click "Save and Continue"

7. Create OAuth Client ID:
   - Application type: **Desktop app**
   - Name: "Job Automation Desktop Client"
   - Click "Create"

8. Download credentials:
   - Click "Download JSON"
   - Save as `credentials/google_oauth_credentials.json`

### Step 4: Configure Credentials Path

**Option 1: Environment Variable** (Recommended):

```bash
# In .env
GOOGLE_OAUTH_CREDENTIALS_PATH=/absolute/path/to/credentials/google_oauth_credentials.json
```

**Option 2: Default Path**:

Place credentials at:
```
backend/credentials/google_oauth_credentials.json
```

### Step 5: First-time Authorization

1. Start the backend server:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. Trigger an API call that requires Calendar access:
   ```bash
   curl -X POST http://localhost:8000/api/v1/calendar/interview \
     -H "Content-Type: application/json" \
     -d '{
       "job_id": 1,
       "interview_type": "phone",
       "start_time": "2025-11-20T14:00:00Z"
     }'
   ```

3. Authorization flow:
   - Browser window will open automatically
   - Sign in with your Google account
   - Review permissions
   - Click "Allow"

4. Token saved:
   - Credentials cached in `credentials/calendar_token.pickle`
   - Automatically refreshed when expired

### Step 6: Verify Setup

Check if authentication works:

```bash
# Test Calendar API
curl http://localhost:8000/api/v1/calendar/upcoming

# Expected response:
{
  "events": [...]
}
```

---

## Google OAuth Scopes Explained

### Calendar Scope

**Scope**: `https://www.googleapis.com/auth/calendar`

**Permissions**:
- ✅ Create events
- ✅ Update events
- ✅ Delete events
- ✅ Read all calendars

**Used For**:
- Interview scheduling
- Follow-up reminders
- Application deadlines

**Alternative Scopes**:
- `calendar.events` - Read-only access
- `calendar.readonly` - View calendars only

### Drive Scope

**Scope**: `https://www.googleapis.com/auth/drive.file`

**Permissions**:
- ✅ Create files
- ✅ Upload files
- ✅ Read files created by app
- ❌ Cannot access other Drive files

**Used For**:
- Upload generated resumes
- Upload generated cover letters
- Create job-specific folders

**Alternative Scopes**:
- `drive` - Full Drive access (not recommended)
- `drive.appdata` - App-specific hidden folder only

### Gmail Scope

**Scope**: `https://www.googleapis.com/auth/gmail.send`

**Permissions**:
- ✅ Send emails
- ❌ Cannot read emails

**Used For**:
- Email notifications
- Follow-up emails (if automated)

---

## OAuth Token Management

### Token Storage

Tokens stored in `credentials/calendar_token.pickle`:

```python
{
  "token": "ya29.a0AfH6SMB...",
  "refresh_token": "1//0gXXXXXXXXXXXXX",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "123456789.apps.googleusercontent.com",
  "client_secret": "XXXXXXXXXXXXX",
  "scopes": ["https://www.googleapis.com/auth/calendar"]
}
```

### Token Refresh

Tokens automatically refresh:

```python
# In calendar_service.py
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())  # Automatic refresh
    with open(token_path, 'wb') as token:
        pickle.dump(creds, token)  # Save refreshed token
```

### Token Expiration

- **Access Token**: Valid for 1 hour
- **Refresh Token**: Valid indefinitely (until revoked)
- **Auto-refresh**: Happens automatically before API calls

### Revoking Access

**Option 1: Via Google Account**:
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click "Third-party apps with account access"
3. Find "Job Automation System"
4. Click "Remove Access"

**Option 2: Delete Token File**:
```bash
rm credentials/calendar_token.pickle
# Next API call will trigger re-authorization
```

---

## API Key Authentication

### Production API Key Setup

For production deployment, implement API key authentication:

#### Step 1: Generate API Keys

```python
# utils/generate_api_key.py
import secrets
import hashlib

def generate_api_key():
    """Generate secure API key"""
    key = secrets.token_urlsafe(32)
    return f"jobautomation_{key}"

def hash_api_key(api_key):
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

# Usage
api_key = generate_api_key()
print(f"API Key: {api_key}")
print(f"Hash: {hash_api_key(api_key)}")
```

#### Step 2: Store API Keys

```python
# models/api_key.py
from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key_hash = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    rate_limit = Column(Integer, default=1000)  # requests per hour
```

#### Step 3: Implement Authentication Middleware

```python
# middleware/auth.py
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
import hashlib

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """Verify API key from header"""

    # Hash provided key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Lookup in database
    db_key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True
    ).first()

    if not db_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key"
        )

    # Update last used
    db_key.last_used = datetime.utcnow()
    db.commit()

    return db_key
```

#### Step 4: Protect Endpoints

```python
# api/jobs.py
from ..middleware.auth import verify_api_key

@router.post("/", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key)  # Require API key
):
    """Create job (requires authentication)"""
    # ... implementation ...
```

#### Step 5: Client Usage

```bash
# cURL
curl -X POST http://api.example.com/api/v1/jobs \
  -H "X-API-Key: jobautomation_XXXXXXXXXXXXXXXXXXXXX" \
  -H "Content-Type: application/json" \
  -d '{"company": "Google", ...}'

# JavaScript
fetch('http://api.example.com/api/v1/jobs', {
  method: 'POST',
  headers: {
    'X-API-Key': 'jobautomation_XXXXXXXXXXXXXXXXXXXXX',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({company: 'Google', ...})
});

# Python
import requests

headers = {
    'X-API-Key': 'jobautomation_XXXXXXXXXXXXXXXXXXXXX',
    'Content-Type': 'application/json'
}
response = requests.post(
    'http://api.example.com/api/v1/jobs',
    headers=headers,
    json={'company': 'Google', ...}
)
```

---

## WebSocket Authentication

### Token-based WebSocket Auth

For production, implement token authentication:

```python
# api/websocket.py
from fastapi import WebSocket, Query, HTTPException
from jose import jwt, JWTError

async def verify_ws_token(token: str):
    """Verify WebSocket connection token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401)
        return user_id
    except JWTError:
        raise HTTPException(status_code=401)

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)  # Require token
):
    """WebSocket with authentication"""
    # Verify token
    try:
        user_id = await verify_ws_token(token)
    except HTTPException:
        await websocket.close(code=1008)  # Policy violation
        return

    # Connect authenticated user
    await manager.connect(websocket, user_id)
```

### Client Connection with Token

```javascript
// Get token from backend
const token = await fetch('/api/v1/auth/token', {
  method: 'POST',
  headers: {'X-API-Key': apiKey}
}).then(r => r.json()).then(d => d.token);

// Connect with token
const ws = new WebSocket(`ws://api.example.com/api/v1/ws?token=${token}`);
```

---

## Environment Configuration

### Development Environment

Create `.env` file in `backend/`:

```bash
# API Configuration
ENVIRONMENT=development
API_HOST=localhost
API_PORT=8000

# Google OAuth
GOOGLE_OAUTH_CREDENTIALS_PATH=./credentials/google_oauth_credentials.json

# Security (generate random secret)
SECRET_KEY=your-secret-key-here-at-least-32-characters

# Database
DATABASE_URL=sqlite:///./job_automation.db

# Redis Cache (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Email Configuration (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Logging
LOG_LEVEL=INFO
```

### Production Environment

```bash
# API Configuration
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000

# Google OAuth
GOOGLE_OAUTH_CREDENTIALS_PATH=/app/credentials/google_oauth_credentials.json

# Security
SECRET_KEY=CHANGE-THIS-TO-STRONG-RANDOM-SECRET

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@db:5432/jobautomation

# Redis Cache
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=CHANGE-THIS
REDIS_DB=0

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=WARNING
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

### Generating Secret Key

```python
# Generate secure secret key
import secrets
print(secrets.token_urlsafe(32))

# Output: Use this as SECRET_KEY in .env
```

---

## Security Best Practices

### 1. Credential Storage

✅ **DO**:
- Store credentials in `.env` file (gitignored)
- Use environment variables in production
- Encrypt sensitive files at rest
- Use secret management services (AWS Secrets Manager, Google Secret Manager)

❌ **DON'T**:
- Commit credentials to Git
- Hardcode credentials in code
- Share credentials in plain text
- Store credentials in client-side code

### 2. OAuth Token Security

✅ **DO**:
- Store tokens in secure location (`credentials/` folder, gitignored)
- Use minimal required scopes
- Implement token refresh
- Revoke tokens when no longer needed

❌ **DON'T**:
- Commit token files to Git
- Request excessive permissions
- Share tokens between users
- Store tokens in browser localStorage

### 3. API Key Security

✅ **DO**:
- Generate strong random keys (32+ bytes)
- Hash keys before storing
- Implement rate limiting
- Rotate keys periodically
- Use HTTPS in production

❌ **DON'T**:
- Use predictable patterns
- Store plain-text keys in database
- Share keys between applications
- Expose keys in URLs

### 4. WebSocket Security

✅ **DO**:
- Use WSS (secure WebSocket) in production
- Implement token-based auth
- Validate all client messages
- Implement rate limiting

❌ **DON'T**:
- Allow unauthenticated connections
- Trust client-provided data
- Allow connection hijacking

### 5. CORS Configuration

Development (permissive):
```python
allow_origins=["*"]  # Allow all origins
```

Production (restrictive):
```python
allow_origins=[
    "https://yourdomain.com",
    "https://app.yourdomain.com"
]
```

---

## Troubleshooting

### Google OAuth Issues

#### Error: "redirect_uri_mismatch"

**Cause**: OAuth client configured for wrong application type

**Solution**:
1. Delete existing OAuth client
2. Create new client with type "Desktop app"
3. Download new credentials

#### Error: "access_denied"

**Cause**: User denied permission or app not approved

**Solution**:
1. Check OAuth consent screen configuration
2. Ensure all required scopes are added
3. Add user as test user (if External app)

#### Error: "invalid_grant"

**Cause**: Refresh token expired or revoked

**Solution**:
```bash
# Delete token file and re-authorize
rm credentials/calendar_token.pickle

# Restart server and trigger API call
```

### API Key Issues

#### Error: "Invalid API key"

**Solution**:
1. Verify key format: `jobautomation_XXXXX`
2. Check if key is active in database
3. Verify correct header: `X-API-Key`

### WebSocket Issues

#### Connection Rejected

**Solution**:
1. Check if token is valid (not expired)
2. Verify WebSocket URL (ws:// or wss://)
3. Check firewall/proxy settings

---

## Testing Authentication

### Test OAuth Setup

```python
# test_oauth.py
from app.services.calendar_service import get_calendar_service

def test_calendar_auth():
    """Test Google Calendar authentication"""
    calendar = get_calendar_service()

    # Try to fetch events
    events = calendar.get_upcoming_events(days=7)
    print(f"✓ Authentication successful")
    print(f"✓ Found {len(events)} upcoming events")

if __name__ == "__main__":
    test_calendar_auth()
```

### Test API Key

```bash
# Generate test API key
python utils/generate_api_key.py

# Add to database
# ...

# Test authenticated request
curl -X GET http://localhost:8000/api/v1/jobs \
  -H "X-API-Key: jobautomation_TEST_KEY_XXXXX"

# Expected: 200 OK with job list
```

---

## Next Steps

- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [WebSocket Guide](./WEBSOCKET_GUIDE.md) - Real-time updates
- [Integration Guide](./INTEGRATION_GUIDE.md) - Feature workflows
- [Production Deployment](./DEPLOYMENT.md) - Deploy to production
