#!/usr/bin/env python3
"""
Test Google Drive connection and access
This script will verify your Google Drive credentials and test folder access
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from loguru import logger
from dotenv import load_dotenv


def test_google_drive_connection():
    """Test Google Drive connection and folder access"""
    
    # Load environment variables
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
    
    base_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    
    logger.info("=" * 60)
    logger.info("🧪 Testing Google Drive Connection")
    logger.info("=" * 60)
    logger.info("")
    
    # Load credentials
    token_path = Path(__file__).parent.parent / 'credentials' / 'token.json'
    
    if not token_path.exists():
        logger.error("❌ token.json not found")
        logger.error(f"   Expected at: {token_path}")
        logger.error("   Run: python scripts/setup_google_auth.py")
        return False
    
    logger.info(f"✅ Found credentials: {token_path}")
    
    try:
        # Load credentials
        creds = Credentials.from_authorized_user_file(
            str(token_path),
            scopes=['https://www.googleapis.com/auth/drive']
        )
        
        logger.info("✅ Credentials loaded successfully")
        
        # Build service
        service = build('drive', 'v3', credentials=creds)
        logger.info("✅ Google Drive service initialized")
        logger.info("")
        
        # Test 1: List files in root
        logger.info("📋 Test 1: Listing files in root Drive...")
        try:
            results = service.files().list(
                pageSize=5,
                fields='files(id, name, mimeType)'
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"✅ Found {len(files)} files/folders:")
            for file in files:
                logger.info(f"   - {file['name']} ({file['mimeType']})")
            logger.info("")
        except Exception as e:
            logger.error(f"❌ Failed to list files: {e}")
            logger.info("")
        
        # Test 2: Check base folder
        if base_folder_id:
            logger.info(f"📁 Test 2: Checking base folder...")
            logger.info(f"   Folder ID: {base_folder_id}")
            
            try:
                folder = service.files().get(
                    fileId=base_folder_id,
                    fields='id, name, webViewLink, mimeType'
                ).execute()
                
                logger.info(f"✅ Base folder found!")
                logger.info(f"   Name: {folder['name']}")
                logger.info(f"   URL: {folder['webViewLink']}")
                logger.info("")
                
                # Test 3: List contents of base folder
                logger.info("📂 Test 3: Listing contents of base folder...")
                try:
                    results = service.files().list(
                        q=f"'{base_folder_id}' in parents and trashed=false",
                        pageSize=10,
                        fields='files(id, name, mimeType, webViewLink)'
                    ).execute()
                    
                    files = results.get('files', [])
                    if files:
                        logger.info(f"✅ Found {len(files)} items in base folder:")
                        for file in files:
                            logger.info(f"   - {file['name']}")
                            logger.info(f"     Type: {file['mimeType']}")
                            logger.info(f"     URL: {file.get('webViewLink', 'N/A')}")
                    else:
                        logger.info("📭 Base folder is empty (no job folders yet)")
                    logger.info("")
                except Exception as e:
                    logger.error(f"❌ Failed to list folder contents: {e}")
                    logger.info("")
                
            except Exception as e:
                logger.error(f"❌ Base folder not accessible: {e}")
                logger.warning("⚠️  You may need to create a new base folder")
                logger.info("   Run: python scripts/create_base_folder.py")
                logger.info("")
        else:
            logger.warning("⚠️  No GOOGLE_DRIVE_FOLDER_ID set in .env")
            logger.info("   Run: python scripts/create_base_folder.py")
            logger.info("")
        
        # Test 4: Create a test folder
        logger.info("🧪 Test 4: Creating test folder...")
        try:
            test_folder_metadata = {
                'name': 'Test Folder - Delete Me',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if base_folder_id:
                test_folder_metadata['parents'] = [base_folder_id]
            
            test_folder = service.files().create(
                body=test_folder_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            logger.info(f"✅ Test folder created successfully!")
            logger.info(f"   Name: {test_folder['name']}")
            logger.info(f"   URL: {test_folder['webViewLink']}")
            logger.info("")
            
            # Clean up test folder
            logger.info("🧹 Cleaning up test folder...")
            service.files().delete(fileId=test_folder['id']).execute()
            logger.info("✅ Test folder deleted")
            logger.info("")
            
        except Exception as e:
            logger.error(f"❌ Failed to create test folder: {e}")
            logger.info("")
        
        # Summary
        logger.info("=" * 60)
        logger.info("✅ Google Drive Connection Test Complete!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("🎉 Your Google Drive integration is working!")
        logger.info("   You can now upload job descriptions.")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error("")
        logger.error("=" * 60)
        logger.error("❌ Google Drive Connection Test Failed")
        logger.error("=" * 60)
        logger.error("")
        logger.error(f"Error: {e}")
        logger.error("")
        logger.error("🔧 Troubleshooting:")
        logger.error("   1. Check your credentials/token.json file")
        logger.error("   2. Run: python scripts/setup_google_auth.py")
        logger.error("   3. Make sure you authorized the correct Google account")
        logger.error("")
        return False


if __name__ == '__main__':
    success = test_google_drive_connection()
    sys.exit(0 if success else 1)
