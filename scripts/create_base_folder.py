#!/usr/bin/env python3
"""
Create the base Google Drive folder for job applications
This script will create a folder called "Job Applications" in your Google Drive
and output the folder ID to use in your .env file
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from loguru import logger


def create_base_folder():
    """Create base folder in Google Drive"""
    
    # Load credentials
    token_path = Path(__file__).parent.parent / 'credentials' / 'token.json'
    
    if not token_path.exists():
        logger.error("❌ token.json not found. Please run setup_google_auth.py first")
        return None
    
    logger.info(f"📂 Loading credentials from: {token_path}")
    
    try:
        creds = Credentials.from_authorized_user_file(
            str(token_path),
            scopes=['https://www.googleapis.com/auth/drive']
        )
        
        service = build('drive', 'v3', credentials=creds)
        
        # Check if folder already exists
        logger.info("🔍 Checking for existing 'Job Applications' folder...")
        
        results = service.files().list(
            q="name='Job Applications' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name, webViewLink)'
        ).execute()
        
        folders = results.get('files', [])
        
        if folders:
            folder = folders[0]
            logger.info(f"✅ Found existing folder: {folder['name']}")
            logger.info(f"📁 Folder ID: {folder['id']}")
            logger.info(f"🔗 Folder URL: {folder['webViewLink']}")
            return folder['id']
        
        # Create new folder
        logger.info("📁 Creating new 'Job Applications' folder...")
        
        file_metadata = {
            'name': 'Job Applications',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = service.files().create(
            body=file_metadata,
            fields='id, name, webViewLink'
        ).execute()
        
        logger.info(f"✅ Created folder: {folder['name']}")
        logger.info(f"📁 Folder ID: {folder['id']}")
        logger.info(f"🔗 Folder URL: {folder['webViewLink']}")
        
        return folder['id']
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None


def update_env_file(folder_id: str):
    """Update .env file with the folder ID"""
    
    env_path = Path(__file__).parent.parent / '.env'
    
    if not env_path.exists():
        logger.warning("⚠️ .env file not found")
        return
    
    # Read current .env
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update GOOGLE_DRIVE_FOLDER_ID
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('GOOGLE_DRIVE_FOLDER_ID='):
            lines[i] = f'GOOGLE_DRIVE_FOLDER_ID={folder_id}\n'
            updated = True
            break
    
    if updated:
        with open(env_path, 'w') as f:
            f.writelines(lines)
        logger.info(f"✅ Updated .env file with folder ID: {folder_id}")
    else:
        logger.warning("⚠️ GOOGLE_DRIVE_FOLDER_ID not found in .env file")
        logger.info(f"💡 Add this line to your .env file:")
        logger.info(f"   GOOGLE_DRIVE_FOLDER_ID={folder_id}")


if __name__ == '__main__':
    logger.info("🚀 Creating Google Drive base folder...")
    logger.info("")
    
    folder_id = create_base_folder()
    
    if folder_id:
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ SUCCESS!")
        logger.info("=" * 60)
        logger.info("")
        logger.info(f"📋 Copy this folder ID to your .env file:")
        logger.info(f"   GOOGLE_DRIVE_FOLDER_ID={folder_id}")
        logger.info("")
        
        # Try to update .env automatically
        update_env_file(folder_id)
        
        logger.info("")
        logger.info("🔄 Next steps:")
        logger.info("   1. Restart Docker: docker-compose restart backend")
        logger.info("   2. Try uploading a job description again")
        logger.info("")
    else:
        logger.error("")
        logger.error("❌ Failed to create folder")
        logger.error("   Please check your Google Drive credentials")
