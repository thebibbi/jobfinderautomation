"""
Google Calendar Integration Service

Schedule interviews, follow-ups, and job-related events in Google Calendar.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.warning("Google Calendar API not available. Install google-api-python-client.")

import os
import pickle
from pathlib import Path

from ..config import settings


class CalendarService:
    """
    Google Calendar integration for job automation events
    """

    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self):
        self.service = None
        self.credentials = None

        if GOOGLE_AVAILABLE:
            self._initialize()
        else:
            logger.warning("Google Calendar service unavailable")

    def _initialize(self):
        """Initialize Google Calendar API"""
        try:
            # Load credentials
            token_path = Path("credentials/calendar_token.pickle")
            creds_path = Path(settings.GOOGLE_OAUTH_CREDENTIALS_PATH)

            creds = None

            # Check for saved token
            if token_path.exists():
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)

            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    logger.info("Refreshed Google Calendar credentials")
                elif creds_path.exists():
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(creds_path),
                        self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    logger.info("Obtained new Google Calendar credentials")

                # Save credentials
                token_path.parent.mkdir(exist_ok=True)
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)

            self.credentials = creds
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("✅ Google Calendar service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar: {e}")
            self.service = None

    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        reminders: Optional[List[int]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a calendar event

        Args:
            summary: Event title
            start_time: Event start time
            end_time: Event end time
            description: Event description
            location: Event location
            attendees: List of attendee emails
            reminders: List of reminder minutes before event

        Returns:
            Created event or None if failed
        """
        if not self.service:
            logger.warning("Calendar service not available")
            return None

        try:
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }

            if description:
                event['description'] = description

            if location:
                event['location'] = location

            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]

            if reminders:
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': mins} for mins in reminders
                    ] + [
                        {'method': 'popup', 'minutes': mins} for mins in reminders
                    ]
                }

            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()

            logger.info(f"Created calendar event: {summary}")
            return created_event

        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            return None

    def create_interview_event(
        self,
        job_title: str,
        company: str,
        interview_type: str,
        start_time: datetime,
        duration_minutes: int = 60,
        location: Optional[str] = None,
        interviewer_email: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create an interview event

        Args:
            job_title: Job title
            company: Company name
            interview_type: Type of interview (phone, video, onsite, etc.)
            start_time: Interview start time
            duration_minutes: Interview duration
            location: Interview location
            interviewer_email: Interviewer's email
            notes: Additional notes

        Returns:
            Created event or None
        """
        end_time = start_time + timedelta(minutes=duration_minutes)

        summary = f"{interview_type.title()} Interview: {job_title} at {company}"

        description_parts = [
            f"Interview Type: {interview_type}",
            f"Position: {job_title}",
            f"Company: {company}"
        ]

        if notes:
            description_parts.append(f"\nNotes:\n{notes}")

        description = "\n".join(description_parts)

        attendees = [interviewer_email] if interviewer_email else None

        # Reminders: 1 day, 1 hour, and 15 minutes before
        reminders = [24 * 60, 60, 15]

        return self.create_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            attendees=attendees,
            reminders=reminders
        )

    def create_follow_up_reminder(
        self,
        job_title: str,
        company: str,
        follow_up_type: str,
        reminder_time: datetime,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a follow-up reminder event

        Args:
            job_title: Job title
            company: Company name
            follow_up_type: Type of follow-up (application, interview, offer)
            reminder_time: When to send reminder
            notes: Additional notes

        Returns:
            Created event or None
        """
        summary = f"Follow-up: {job_title} at {company}"

        description_parts = [
            f"Follow-up Type: {follow_up_type}",
            f"Position: {job_title}",
            f"Company: {company}"
        ]

        if notes:
            description_parts.append(f"\nAction Items:\n{notes}")

        description = "\n".join(description_parts)

        # 30-minute reminder block
        end_time = reminder_time + timedelta(minutes=30)

        # Reminder 1 day and 1 hour before
        reminders = [24 * 60, 60]

        return self.create_event(
            summary=summary,
            start_time=reminder_time,
            end_time=end_time,
            description=description,
            reminders=reminders
        )

    def create_application_deadline(
        self,
        job_title: str,
        company: str,
        deadline: datetime,
        job_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create an application deadline reminder

        Args:
            job_title: Job title
            company: Company name
            deadline: Application deadline
            job_url: URL to job posting

        Returns:
            Created event or None
        """
        summary = f"Application Deadline: {job_title} at {company}"

        description_parts = [
            f"Position: {job_title}",
            f"Company: {company}",
            f"⚠️ This is the application deadline!"
        ]

        if job_url:
            description_parts.append(f"\nApply at: {job_url}")

        description = "\n".join(description_parts)

        # All-day event
        end_time = deadline + timedelta(hours=1)

        # Reminders 3 days, 1 day, and 3 hours before
        reminders = [3 * 24 * 60, 24 * 60, 3 * 60]

        return self.create_event(
            summary=summary,
            start_time=deadline,
            end_time=end_time,
            description=description,
            reminders=reminders
        )

    def update_event(
        self,
        event_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing calendar event

        Args:
            event_id: Google Calendar event ID
            updates: Dictionary of fields to update

        Returns:
            Updated event or None
        """
        if not self.service:
            return None

        try:
            # Get existing event
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()

            # Apply updates
            for key, value in updates.items():
                if key in ['start', 'end'] and isinstance(value, datetime):
                    event[key] = {
                        'dateTime': value.isoformat(),
                        'timeZone': 'UTC'
                    }
                else:
                    event[key] = value

            # Update event
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()

            logger.info(f"Updated calendar event: {event_id}")
            return updated_event

        except Exception as e:
            logger.error(f"Failed to update calendar event: {e}")
            return None

    def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event

        Args:
            event_id: Google Calendar event ID

        Returns:
            True if successful
        """
        if not self.service:
            return False

        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()

            logger.info(f"Deleted calendar event: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete calendar event: {e}")
            return False

    def get_upcoming_events(
        self,
        days_ahead: int = 7,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming events

        Args:
            days_ahead: How many days ahead to look
            max_results: Maximum number of results

        Returns:
            List of upcoming events
        """
        if not self.service:
            return []

        try:
            now = datetime.utcnow()
            time_max = now + timedelta(days=days_ahead)

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            return events

        except Exception as e:
            logger.error(f"Failed to get upcoming events: {e}")
            return []

    def get_events_for_job(
        self,
        job_title: str,
        company: str
    ) -> List[Dict[str, Any]]:
        """
        Get all calendar events related to a specific job

        Args:
            job_title: Job title to search for
            company: Company name to search for

        Returns:
            List of matching events
        """
        if not self.service:
            return []

        try:
            # Search for events mentioning the job and company
            query = f"{job_title} {company}"

            events_result = self.service.events().list(
                calendarId='primary',
                q=query,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            return events

        except Exception as e:
            logger.error(f"Failed to get events for job: {e}")
            return []


# Global calendar service instance
_calendar_service: Optional[CalendarService] = None


def get_calendar_service() -> CalendarService:
    """Get global calendar service instance"""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = CalendarService()
    return _calendar_service
