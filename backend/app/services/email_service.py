from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from typing import Dict, Any
from loguru import logger
from datetime import datetime
from pathlib import Path

from ..config import settings


class EmailService:
    """Service for sending email notifications"""

    def __init__(self):
        self.sender_email = settings.SENDER_EMAIL
        self.recipient_email = settings.NOTIFICATION_EMAIL
        self._init_gmail_service()

    def _init_gmail_service(self):
        """Initialize Gmail API service"""
        try:
            creds = Credentials.from_authorized_user_file(
                'credentials/token.json',
                scopes=['https://www.googleapis.com/auth/gmail.send']
            )
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("✅ Gmail service initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing Gmail: {e}")
            self.service = None

    def send_job_analysis_notification(
        self,
        job_data: Dict[str, Any],
        analysis_results: Dict[str, Any],
        drive_folder_url: str
    ):
        """Send email notification after job analysis"""
        try:
            match_score = analysis_results.get("match_score", 0)
            company = job_data.get("company", "Unknown")
            job_title = job_data.get("job_title", "Unknown")

            # Determine status
            if match_score >= 85:
                status_emoji = "🎯"
                status_text = "Excellent Match"
                status_color = "#10B981"
            elif match_score >= 70:
                status_emoji = "✅"
                status_text = "Good Match"
                status_color = "#3B82F6"
            elif match_score >= 55:
                status_emoji = "⚠️"
                status_text = "Moderate Match"
                status_color = "#F59E0B"
            else:
                status_emoji = "❌"
                status_text = "Low Match"
                status_color = "#EF4444"

            # Build email
            subject = f"{status_emoji} Job Analysis: {company} - {job_title} ({match_score}%)"

            # Get key details
            key_strengths = analysis_results.get("key_strengths", [])[:3]
            potential_gaps = analysis_results.get("potential_gaps", [])[:3]
            should_apply = analysis_results.get("should_apply", False)

            # HTML email body
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                              color: white; padding: 30px; border-radius: 10px 10px 0 0; }}
                    .header h1 {{ margin: 0; font-size: 24px; }}
                    .score-badge {{ background: {status_color}; color: white; padding: 10px 20px;
                                   border-radius: 20px; display: inline-block; margin-top: 10px;
                                   font-size: 18px; font-weight: bold; }}
                    .content {{ background: #f9fafb; padding: 30px; }}
                    .section {{ margin-bottom: 25px; }}
                    .section h2 {{ color: #1a202c; font-size: 18px; margin-bottom: 10px;
                                  border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; }}
                    .list-item {{ background: white; padding: 12px; margin-bottom: 8px;
                                 border-left: 3px solid #667eea; border-radius: 4px; }}
                    .cta-button {{ background: #667eea; color: white; padding: 15px 30px;
                                  text-decoration: none; border-radius: 8px; display: inline-block;
                                  margin-top: 20px; font-weight: bold; }}
                    .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{status_emoji} Job Analysis Complete</h1>
                        <p style="margin: 5px 0;">{company}</p>
                        <p style="margin: 5px 0; font-size: 20px; font-weight: bold;">{job_title}</p>
                        <div class="score-badge">
                            {status_text}: {match_score}%
                        </div>
                    </div>

                    <div class="content">
                        <div class="section">
                            <h2>💪 Top Strengths</h2>
                            {''.join([f'<div class="list-item"><strong>{s.get("strength", "")}</strong><br><small>{s.get("relevance", "")}</small></div>' for s in key_strengths])}
                        </div>

                        <div class="section">
                            <h2>🔍 Potential Gaps</h2>
                            {''.join([f'<div class="list-item"><strong>{g.get("gap", "")}</strong> ({g.get("severity", "moderate")})<br><small>{g.get("mitigation", "")}</small></div>' for g in potential_gaps])}
                        </div>

                        <div class="section">
                            <h2>📋 Recommendation</h2>
                            <div class="list-item">
                                <strong>{'✅ Apply' if should_apply else '🤔 Consider carefully'}</strong><br>
                                <p>{analysis_results.get('reasoning', '')[:300]}...</p>
                            </div>
                        </div>

                        <div style="text-align: center;">
                            <a href="{drive_folder_url}" class="cta-button">
                                📁 View Documents in Google Drive
                            </a>
                        </div>
                    </div>

                    <div class="footer">
                        <p>Job Application Automation System</p>
                        <p>Processed on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Send email
            self._send_email(
                to_email=self.recipient_email,
                subject=subject,
                html_body=html_body
            )

            logger.info(f"✅ Email notification sent for {company} - {job_title}")

        except Exception as e:
            logger.error(f"❌ Error sending email notification: {e}")

    def _send_email(self, to_email: str, subject: str, html_body: str):
        """Send email via Gmail API"""
        if not self.service:
            logger.warning("⚠️  Gmail service not initialized, skipping email")
            return

        try:
            message = MIMEMultipart('alternative')
            message['To'] = to_email
            message['From'] = self.sender_email
            message['Subject'] = subject

            html_part = MIMEText(html_body, 'html')
            message.attach(html_part)

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"✅ Email sent to {to_email}")

        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
            raise


# Singleton
_email_service = None

def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
