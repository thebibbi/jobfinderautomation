"""
Script to set up Google OAuth authentication
Run this once to get the token.json file
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes required
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/spreadsheets'
]


def setup_google_auth():
    """Set up Google OAuth and save credentials"""
    creds = None
    token_path = 'credentials/token.json'
    credentials_path = 'credentials/oauth-credentials.json'

    # Check if we have saved credentials
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            # Use fixed port 8080 for OAuth redirect
            creds = flow.run_local_server(port=8080)

        # Save credentials
        os.makedirs('credentials', exist_ok=True)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    print("✅ Google authentication successful!")
    print(f"✅ Credentials saved to {token_path}")

    # Test the connection
    try:
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(pageSize=10).execute()
        print(f"✅ Successfully connected to Google Drive")
        print(f"   Found {len(results.get('files', []))} files in your drive")
    except Exception as e:
        print(f"❌ Error testing Drive connection: {e}")


if __name__ == '__main__':
    setup_google_auth()
