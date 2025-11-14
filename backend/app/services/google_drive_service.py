from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from typing import Optional, Dict, Any, List
import io
from pathlib import Path
from loguru import logger

from ..config import settings


class GoogleDriveService:
    """Service for Google Drive operations"""

    def __init__(self):
        self.creds = self._get_credentials()
        self.service = build('drive', 'v3', credentials=self.creds)
        self.base_folder_id = settings.GOOGLE_DRIVE_FOLDER_ID

    def _get_credentials(self):
        """Get Google Drive credentials"""
        try:
            # Try service account first
            if Path(settings.GOOGLE_CREDENTIALS_PATH).exists():
                return service_account.Credentials.from_service_account_file(
                    settings.GOOGLE_CREDENTIALS_PATH,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
            # Fall back to OAuth
            elif Path('credentials/token.json').exists():
                return Credentials.from_authorized_user_file(
                    'credentials/token.json',
                    scopes=['https://www.googleapis.com/auth/drive']
                )
            else:
                raise FileNotFoundError("No Google credentials found")
        except Exception as e:
            logger.error(f"❌ Error loading Google credentials: {e}")
            raise

    def create_job_folder(
        self,
        company: str,
        job_title: str,
        parent_folder_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create a folder for a job application

        Returns:
            {"folder_id": "...", "folder_url": "..."}
        """
        try:
            folder_name = f"{company} - {job_title}"
            parent_id = parent_folder_id or self.base_folder_id

            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }

            folder = self.service.files().create(
                body=file_metadata,
                fields='id, webViewLink'
            ).execute()

            logger.info(f"✅ Created folder: {folder_name}")

            return {
                "folder_id": folder['id'],
                "folder_url": folder['webViewLink']
            }

        except Exception as e:
            logger.error(f"❌ Error creating folder: {e}")
            raise

    def upload_document(
        self,
        content: str,
        filename: str,
        folder_id: str,
        mime_type: str = 'application/vnd.google-apps.document'
    ) -> Dict[str, str]:
        """
        Upload a document to Google Drive

        Args:
            content: Document content (text or bytes)
            filename: Name for the file
            folder_id: Parent folder ID
            mime_type: MIME type of file

        Returns:
            {"file_id": "...", "file_url": "..."}
        """
        try:
            # Convert content to bytes if string
            if isinstance(content, str):
                content_bytes = content.encode('utf-8')
            else:
                content_bytes = content

            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }

            media = MediaIoBaseUpload(
                io.BytesIO(content_bytes),
                mimetype=mime_type,
                resumable=True
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()

            logger.info(f"✅ Uploaded: {filename}")

            return {
                "file_id": file['id'],
                "file_url": file['webViewLink']
            }

        except Exception as e:
            logger.error(f"❌ Error uploading document: {e}")
            raise

    def upload_job_description(
        self,
        jd_content: str,
        folder_id: str,
        company: str,
        job_title: str
    ) -> Dict[str, str]:
        """Upload job description as Google Doc"""
        filename = f"{company} - {job_title} - JD"
        return self.upload_document(
            content=jd_content,
            filename=filename,
            folder_id=folder_id,
            mime_type='application/vnd.google-apps.document'
        )

    def upload_resume(
        self,
        resume_content: bytes,
        folder_id: str,
        filename: str = "Resume.pdf"
    ) -> Dict[str, str]:
        """Upload resume as PDF"""
        return self.upload_document(
            content=resume_content,
            filename=filename,
            folder_id=folder_id,
            mime_type='application/pdf'
        )

    def upload_cover_letter(
        self,
        content: str,
        folder_id: str,
        letter_type: str = "conversational"
    ) -> Dict[str, str]:
        """Upload cover letter as Google Doc"""
        filename = f"Cover Letter - {letter_type.title()}"
        return self.upload_document(
            content=content,
            filename=filename,
            folder_id=folder_id,
            mime_type='application/vnd.google-apps.document'
        )

    def move_file(
        self,
        file_id: str,
        new_parent_id: str,
        old_parent_id: Optional[str] = None
    ):
        """Move a file to a new folder"""
        try:
            # Get current parents if not provided
            if not old_parent_id:
                file = self.service.files().get(
                    fileId=file_id,
                    fields='parents'
                ).execute()
                old_parent_id = ','.join(file.get('parents', []))

            # Move file
            self.service.files().update(
                fileId=file_id,
                addParents=new_parent_id,
                removeParents=old_parent_id,
                fields='id, parents'
            ).execute()

            logger.info(f"✅ Moved file {file_id} to folder {new_parent_id}")

        except Exception as e:
            logger.error(f"❌ Error moving file: {e}")
            raise


# Singleton
_drive_service = None

def get_drive_service() -> GoogleDriveService:
    global _drive_service
    if _drive_service is None:
        _drive_service = GoogleDriveService()
    return _drive_service
