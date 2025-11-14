# Job Automation API Reference

Complete API documentation for the Job Application Automation System.

**Base URL**: `http://localhost:8000/api/v1`
**Version**: 1.0.0
**Environment**: Development

---

## Table of Contents

1. [Authentication](#authentication)
2. [Jobs API](#jobs-api)
3. [Job Analysis API](#job-analysis-api)
4. [Document Generation API](#document-generation-api)
5. [Application Tracking System (ATS)](#application-tracking-system-ats)
6. [Follow-up Automation](#follow-up-automation)
7. [Company Research](#company-research)
8. [Recommendations Engine](#recommendations-engine)
9. [Skills Gap Analysis](#skills-gap-analysis)
10. [Calendar Integration](#calendar-integration)
11. [Analytics & Statistics](#analytics--statistics)
12. [Cache Management](#cache-management)
13. [WebSocket Real-time Updates](#websocket-real-time-updates)
14. [Job Scraping](#job-scraping)

---

## Authentication

Currently using development mode. Production should implement:
- API Key authentication via `X-API-Key` header
- OAuth 2.0 for Google Calendar integration
- JWT tokens for user sessions

### Google Calendar OAuth Setup

1. Create Google Cloud Project
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials (Desktop application)
4. Download credentials.json to `credentials/google_oauth_credentials.json`
5. First API call will open browser for authorization
6. Token cached in `credentials/calendar_token.pickle`

---

## Jobs API

Manage job postings and applications.

### Create Job

**Endpoint**: `POST /jobs`
**Description**: Create new job entry with automatic processing

**Request Body**:
```json
{
  "company": "Google",
  "job_title": "Senior Software Engineer",
  "job_description": "We are looking for...",
  "job_url": "https://careers.google.com/jobs/123",
  "location": "Mountain View, CA",
  "salary_min": 150000,
  "salary_max": 220000,
  "source": "linkedin"
}
```

**Response**: `201 Created`
```json
{
  "id": 1,
  "job_id": "linkedin_123456",
  "company": "Google",
  "job_title": "Senior Software Engineer",
  "job_description": "We are looking for...",
  "job_url": "https://careers.google.com/jobs/123",
  "location": "Mountain View, CA",
  "salary_min": 150000,
  "salary_max": 220000,
  "source": "linkedin",
  "status": "processing",
  "match_score": null,
  "created_at": "2025-11-14T10:30:00Z",
  "updated_at": "2025-11-14T10:30:00Z"
}
```

**Automatic Processing Triggered**:
- Company research (cached)
- Skills gap analysis
- Recommendation engine update
- WebSocket notification: `job.created`

---

### List Jobs

**Endpoint**: `GET /jobs`
**Description**: List all jobs with optional filters

**Query Parameters**:
- `skip` (int): Offset for pagination (default: 0)
- `limit` (int): Max results to return (default: 100)
- `status_filter` (string): Filter by status (e.g., "saved", "applied")
- `min_score` (float): Minimum match score (0-100)

**Example Request**:
```
GET /jobs?status_filter=saved&min_score=70&limit=20
```

**Response**: `200 OK`
```json
{
  "total": 45,
  "jobs": [
    {
      "id": 1,
      "company": "Google",
      "job_title": "Senior Software Engineer",
      "status": "saved",
      "match_score": 85.5,
      "created_at": "2025-11-14T10:30:00Z"
    }
  ],
  "skip": 0,
  "limit": 20
}
```

---

### Get Job by ID

**Endpoint**: `GET /jobs/{job_id}`
**Description**: Get detailed job information

**Response**: `200 OK`
```json
{
  "id": 1,
  "job_id": "linkedin_123456",
  "company": "Google",
  "job_title": "Senior Software Engineer",
  "job_description": "Full description...",
  "job_url": "https://careers.google.com/jobs/123",
  "location": "Mountain View, CA",
  "salary_min": 150000,
  "salary_max": 220000,
  "source": "linkedin",
  "status": "saved",
  "match_score": 85.5,
  "recommendation": "apply_now",
  "created_at": "2025-11-14T10:30:00Z",
  "updated_at": "2025-11-14T10:32:00Z"
}
```

---

### Update Job

**Endpoint**: `PATCH /jobs/{job_id}`
**Description**: Update job details (partial update)

**Request Body**:
```json
{
  "status": "applied",
  "notes": "Applied via company website"
}
```

**Response**: `200 OK` (updated job object)

---

### Delete Job

**Endpoint**: `DELETE /jobs/{job_id}`
**Description**: Delete job from database

**Response**: `204 No Content`

---

### Process Job from Extension

**Endpoint**: `POST /jobs/process`
**Description**: Main endpoint called by Chrome extension for one-click processing

**Request Body**:
```json
{
  "company": "Google",
  "jobTitle": "Senior Software Engineer",
  "jobDescription": "We are looking for...",
  "jobUrl": "https://careers.google.com/jobs/123",
  "location": "Mountain View, CA",
  "source": "linkedin"
}
```

**Response**: `200 OK`
```json
{
  "success": true,
  "jobId": 1,
  "matchScore": 85.5,
  "message": "Job queued for processing",
  "driveUrl": "https://drive.google.com/drive/folders/...",
  "status": "processing"
}
```

**Background Processing**:
1. Save job to database
2. Analyze with Claude AI (semantic matching + job-match-analyzer skill)
3. Generate documents if score >= 70 (resume, cover letter)
4. Upload to Google Drive
5. Send email notification
6. WebSocket notification: `job.analyzed`

---

## Job Analysis API

Job matching and semantic analysis.

### Analyze Job

**Endpoint**: `POST /analysis/jobs/{job_id}/analyze`
**Description**: Run semantic analysis and Claude AI matching

**Response**: `200 OK`
```json
{
  "job_id": 1,
  "match_score": 85.5,
  "recommendation": "apply_now",
  "strengths": [
    "Strong match for Python and FastAPI experience",
    "Location preference aligns",
    "Salary range matches expectations"
  ],
  "concerns": [
    "Requires 7+ years experience (you have 5)",
    "Prefers PhD (you have Masters)"
  ],
  "analysis_details": {
    "semantic_similarity": 0.87,
    "skill_match": 0.84,
    "location_match": 1.0,
    "salary_match": 0.92
  },
  "created_at": "2025-11-14T10:32:00Z"
}
```

**Match Score Breakdown**:
- **90-100**: Excellent match - Apply immediately
- **70-89**: Good match - Apply with confidence
- **50-69**: Moderate match - Review carefully
- **0-49**: Weak match - Consider carefully

**Recommendation Values**:
- `apply_now`: High confidence match
- `apply_with_confidence`: Good match
- `consider_carefully`: Moderate match
- `not_recommended`: Weak match

---

### Get Job Analysis

**Endpoint**: `GET /analysis/jobs/{job_id}`
**Description**: Retrieve existing analysis results

**Response**: `200 OK` (same as analyze endpoint)

---

### Batch Analyze Jobs

**Endpoint**: `POST /analysis/batch`
**Description**: Analyze multiple jobs at once

**Request Body**:
```json
{
  "job_ids": [1, 2, 3, 4, 5],
  "force_reanalyze": false
}
```

**Response**: `200 OK`
```json
{
  "total": 5,
  "analyzed": 5,
  "skipped": 0,
  "results": [
    {
      "job_id": 1,
      "match_score": 85.5,
      "recommendation": "apply_now"
    }
  ]
}
```

---

## Document Generation API

Automated resume and cover letter generation.

### Generate Documents

**Endpoint**: `POST /documents/generate`
**Description**: Generate tailored resume and cover letter for job

**Request Body**:
```json
{
  "job_id": 1,
  "include_resume": true,
  "include_cover_letter": true,
  "template": "modern",
  "customizations": {
    "highlight_skills": ["Python", "FastAPI", "AWS"],
    "emphasize_experience": "backend_engineering"
  }
}
```

**Response**: `200 OK`
```json
{
  "job_id": 1,
  "documents": {
    "resume": {
      "file_id": "doc_123",
      "file_name": "Resume_Google_SeniorSWE.pdf",
      "drive_url": "https://drive.google.com/file/d/...",
      "local_path": "/uploads/doc_123.pdf"
    },
    "cover_letter": {
      "file_id": "doc_124",
      "file_name": "CoverLetter_Google_SeniorSWE.pdf",
      "drive_url": "https://drive.google.com/file/d/...",
      "local_path": "/uploads/doc_124.pdf"
    }
  },
  "folder_url": "https://drive.google.com/drive/folders/...",
  "generated_at": "2025-11-14T10:35:00Z"
}
```

---

### List Generated Documents

**Endpoint**: `GET /documents/jobs/{job_id}`
**Description**: Get all documents for specific job

**Response**: `200 OK`
```json
{
  "job_id": 1,
  "documents": [
    {
      "id": 1,
      "document_type": "resume",
      "file_name": "Resume_Google_SeniorSWE.pdf",
      "drive_url": "https://drive.google.com/file/d/...",
      "created_at": "2025-11-14T10:35:00Z"
    }
  ]
}
```

---

### Delete Document

**Endpoint**: `DELETE /documents/{document_id}`
**Description**: Delete document from database and Google Drive

**Query Parameters**:
- `delete_from_drive` (bool): Also delete from Google Drive (default: false)

**Response**: `204 No Content`

---

## Application Tracking System (ATS)

Track application lifecycle from submission to offer.

### Update Job Status

**Endpoint**: `POST /ats/jobs/{job_id}/status`
**Description**: Update application status with validation and event tracking

**Request Body**:
```json
{
  "status": "interviewing",
  "notes": "Phone screen scheduled for next Tuesday"
}
```

**Valid Status Transitions**:
```
saved → applied → interviewing → offer_received → accepted
                                              ↘ declined
       → rejected
       → withdrawn
```

**Response**: `200 OK`
```json
{
  "job_id": 1,
  "old_status": "applied",
  "new_status": "interviewing",
  "status_changed_at": "2025-11-14T11:00:00Z",
  "event_id": 42
}
```

**Automatic Integrations Triggered**:
- Follow-up sequence scheduling (based on status)
- WebSocket notification: `application.status_changed`
- Recommendation engine learning
- Cache invalidation

---

### Get Application Timeline

**Endpoint**: `GET /ats/jobs/{job_id}/timeline`
**Description**: Get complete history of application events

**Response**: `200 OK`
```json
{
  "job_id": 1,
  "events": [
    {
      "id": 1,
      "event_type": "status_change",
      "from_status": "saved",
      "to_status": "applied",
      "notes": "Applied via company website",
      "created_at": "2025-11-10T09:00:00Z"
    },
    {
      "id": 2,
      "event_type": "interview_scheduled",
      "interview_type": "phone",
      "scheduled_date": "2025-11-15T14:00:00Z",
      "created_at": "2025-11-12T10:30:00Z"
    }
  ],
  "interviews": [
    {
      "id": 1,
      "interview_type": "phone",
      "scheduled_date": "2025-11-15T14:00:00Z",
      "duration_minutes": 60,
      "interviewer_name": "Jane Smith",
      "outcome": null,
      "calendar_event_id": "cal_abc123"
    }
  ],
  "offers": [],
  "notes": [
    {
      "id": 1,
      "note_type": "general",
      "content": "Really excited about this role",
      "created_at": "2025-11-10T09:05:00Z"
    }
  ]
}
```

---

### Schedule Interview

**Endpoint**: `POST /ats/interviews`
**Description**: Schedule interview and create calendar event

**Request Body**:
```json
{
  "job_id": 1,
  "interview_type": "phone",
  "scheduled_date": "2025-11-15T14:00:00Z",
  "duration_minutes": 60,
  "location": "Zoom - link in email",
  "interviewer_name": "Jane Smith",
  "interviewer_email": "jane@google.com",
  "preparation_notes": "Review system design questions"
}
```

**Interview Types**:
- `phone`: Phone screen
- `video`: Video interview
- `onsite`: On-site interview
- `technical`: Technical/coding interview
- `behavioral`: Behavioral interview
- `panel`: Panel interview

**Response**: `201 Created`
```json
{
  "id": 1,
  "job_id": 1,
  "interview_type": "phone",
  "scheduled_date": "2025-11-15T14:00:00Z",
  "duration_minutes": 60,
  "location": "Zoom - link in email",
  "interviewer_name": "Jane Smith",
  "interviewer_email": "jane@google.com",
  "preparation_notes": "Review system design questions",
  "outcome": null,
  "feedback": null,
  "calendar_event_id": "cal_abc123",
  "created_at": "2025-11-14T11:00:00Z"
}
```

**Automatic Integrations**:
- Google Calendar event created with reminders (1 day, 1 hour, 15 min)
- WebSocket notification: `interview.scheduled`
- Job status updated to `interview_scheduled` if not already `interviewing`

---

### Update Interview

**Endpoint**: `PUT /ats/interviews/{interview_id}`
**Description**: Update interview details or record outcome

**Request Body**:
```json
{
  "outcome": "passed",
  "feedback": "Great conversation, moving to technical round",
  "preparation_notes": "Ask about team structure"
}
```

**Interview Outcomes**:
- `passed`: Advanced to next round
- `rejected`: Did not advance
- `pending`: Waiting for decision
- `cancelled`: Interview cancelled

**Response**: `200 OK` (updated interview object)

---

### Get Upcoming Interviews

**Endpoint**: `GET /ats/interviews/upcoming`
**Description**: Get interviews scheduled in near future

**Query Parameters**:
- `days_ahead` (int): Number of days to look ahead (default: 7)

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "job_id": 1,
    "company": "Google",
    "job_title": "Senior Software Engineer",
    "interview_type": "phone",
    "scheduled_date": "2025-11-15T14:00:00Z",
    "calendar_event_id": "cal_abc123"
  }
]
```

---

### Get Job Interviews

**Endpoint**: `GET /ats/jobs/{job_id}/interviews`
**Description**: Get all interviews for specific job

**Response**: `200 OK` (array of interview objects)

---

### Record Offer

**Endpoint**: `POST /ats/offers`
**Description**: Record job offer received

**Request Body**:
```json
{
  "job_id": 1,
  "base_salary": 180000,
  "bonus": 30000,
  "equity": "100000 RSUs over 4 years",
  "other_benefits": "Health insurance, 401k match, unlimited PTO",
  "received_date": "2025-11-20T10:00:00Z",
  "expiration_date": "2025-11-27T17:00:00Z",
  "notes": "Verbal offer received, waiting for written offer"
}
```

**Response**: `201 Created`
```json
{
  "id": 1,
  "job_id": 1,
  "base_salary": 180000,
  "bonus": 30000,
  "equity": "100000 RSUs over 4 years",
  "other_benefits": "Health insurance, 401k match, unlimited PTO",
  "offer_status": "pending",
  "received_date": "2025-11-20T10:00:00Z",
  "expiration_date": "2025-11-27T17:00:00Z",
  "decision_date": null,
  "negotiation_history": [],
  "notes": "Verbal offer received, waiting for written offer",
  "created_at": "2025-11-20T10:05:00Z"
}
```

**Automatic Integrations**:
- Job status updated to `offer_received`
- WebSocket notification: `offer.received`
- Calendar deadline reminder created

---

### Update Offer

**Endpoint**: `PUT /ats/offers/{offer_id}`
**Description**: Update offer details or record decision

**Request Body**:
```json
{
  "offer_status": "accepted",
  "decision_date": "2025-11-22T09:00:00Z",
  "notes": "Accepted! Start date is December 1st"
}
```

**Offer Statuses**:
- `pending`: Waiting for candidate decision
- `negotiating`: Counter-offer in progress
- `accepted`: Candidate accepted
- `declined`: Candidate declined
- `expired`: Offer expired

**Response**: `200 OK` (updated offer object)

**Automatic Integrations** (if accepted):
- Job status updated to `accepted`
- All other active applications moved to `withdrawn`
- WebSocket notification: `offer.accepted`
- Recommendation engine learns from successful outcome

---

### Add Negotiation Entry

**Endpoint**: `POST /ats/offers/{offer_id}/negotiate`
**Description**: Record counter-offer or negotiation attempt

**Request Body**:
```json
{
  "negotiation_type": "counter_offer",
  "requested_changes": "Requesting $190k base and 120k RSUs",
  "employer_response": "Agreed to $185k base",
  "notes": "Successful negotiation on base salary"
}
```

**Response**: `200 OK` (updated offer with negotiation_history)

---

### Get Job Offers

**Endpoint**: `GET /ats/jobs/{job_id}/offers`
**Description**: Get all offers for specific job

**Response**: `200 OK` (array of offer objects)

---

### Add Note

**Endpoint**: `POST /ats/notes`
**Description**: Add note to job application

**Request Body**:
```json
{
  "job_id": 1,
  "note_type": "communication",
  "content": "Spoke with recruiter, she mentioned team is expanding",
  "is_important": true
}
```

**Note Types**:
- `general`: General note
- `communication`: Communication with company
- `preparation`: Interview preparation
- `research`: Company research findings
- `follow_up`: Follow-up reminder

**Response**: `201 Created`
```json
{
  "id": 1,
  "job_id": 1,
  "note_type": "communication",
  "content": "Spoke with recruiter, she mentioned team is expanding",
  "is_important": true,
  "created_at": "2025-11-14T12:00:00Z",
  "updated_at": "2025-11-14T12:00:00Z"
}
```

---

### Update Note

**Endpoint**: `PUT /ats/notes/{note_id}`
**Description**: Update existing note

**Response**: `200 OK` (updated note object)

---

### Get Job Notes

**Endpoint**: `GET /ats/jobs/{job_id}/notes`
**Description**: Get all notes for specific job

**Response**: `200 OK` (array of note objects)

---

### Get Statistics

**Endpoint**: `GET /ats/statistics`
**Description**: Get overall application statistics

**Response**: `200 OK`
```json
{
  "total_applications": 45,
  "by_status": {
    "saved": 12,
    "applied": 18,
    "interviewing": 8,
    "offer_received": 3,
    "accepted": 1,
    "rejected": 2,
    "withdrawn": 1
  },
  "interview_stats": {
    "total_interviews": 15,
    "upcoming": 3,
    "completed": 12,
    "passed": 8,
    "rejected": 4
  },
  "offer_stats": {
    "total_offers": 3,
    "pending": 2,
    "accepted": 1,
    "declined": 0,
    "average_base_salary": 175000
  },
  "success_rate": 0.067,
  "average_days_to_offer": 21
}
```

---

## Follow-up Automation

Automated follow-up email scheduling and management.

### Schedule Follow-up

**Endpoint**: `POST /followup/schedule`
**Description**: Schedule follow-up email

**Request Body**:
```json
{
  "job_id": 1,
  "followup_type": "post_application",
  "scheduled_date": "2025-11-17T09:00:00Z",
  "email_template": "Thank you for considering my application...",
  "send_automatically": false
}
```

**Follow-up Types**:
- `post_application`: After submitting application (3 days)
- `post_interview`: After interview (1 day)
- `second_followup`: Second follow-up (7 days after application)
- `final_followup`: Final follow-up (14 days after application)
- `offer_response`: Follow-up on pending offer
- `custom`: Custom follow-up

**Response**: `201 Created`
```json
{
  "id": 1,
  "job_id": 1,
  "followup_type": "post_application",
  "status": "scheduled",
  "scheduled_date": "2025-11-17T09:00:00Z",
  "sent_date": null,
  "email_template": "Thank you for considering my application...",
  "send_automatically": false,
  "created_at": "2025-11-14T12:00:00Z"
}
```

---

### Schedule Follow-up Sequence

**Endpoint**: `POST /followup/sequence`
**Description**: Schedule predefined follow-up sequence

**Request Body**:
```json
{
  "job_id": 1,
  "sequence_name": "post_application",
  "variables": {
    "job_title": "Senior Software Engineer",
    "company": "Google",
    "recruiter_name": "Jane Smith"
  }
}
```

**Predefined Sequences**:

**post_application**:
- Day 3: Initial follow-up
- Day 7: Second check-in
- Day 14: Final follow-up

**post_interview**:
- Day 1: Thank you note
- Day 3: Status inquiry (if no response)

**offer_pending**:
- Day 3: Decision timeline inquiry
- Day 5: Final decision notification

**Response**: `201 Created`
```json
{
  "sequence_id": "seq_123",
  "job_id": 1,
  "followups_scheduled": 3,
  "followups": [
    {
      "id": 1,
      "followup_type": "post_application",
      "scheduled_date": "2025-11-13T09:00:00Z"
    },
    {
      "id": 2,
      "followup_type": "second_followup",
      "scheduled_date": "2025-11-17T09:00:00Z"
    },
    {
      "id": 3,
      "followup_type": "final_followup",
      "scheduled_date": "2025-11-24T09:00:00Z"
    }
  ]
}
```

**Automatic Scheduling**:
- Applied status → `post_application` sequence
- Interviewing status → `post_interview` sequence

---

### Get Follow-ups

**Endpoint**: `GET /followup/jobs/{job_id}`
**Description**: Get all follow-ups for job

**Response**: `200 OK` (array of follow-up objects)

---

### Get Due Follow-ups

**Endpoint**: `GET /followup/due`
**Description**: Get follow-ups due soon

**Query Parameters**:
- `hours_ahead` (int): Hours to look ahead (default: 24)

**Response**: `200 OK`
```json
{
  "count": 3,
  "followups": [
    {
      "id": 1,
      "job_id": 1,
      "company": "Google",
      "job_title": "Senior Software Engineer",
      "followup_type": "post_application",
      "scheduled_date": "2025-11-14T15:00:00Z",
      "hours_until_due": 3
    }
  ]
}
```

**Integration**: WebSocket notification sent when follow-up becomes due

---

### Mark Follow-up Sent

**Endpoint**: `POST /followup/{followup_id}/sent`
**Description**: Mark follow-up as manually sent

**Request Body**:
```json
{
  "sent_date": "2025-11-14T14:00:00Z",
  "notes": "Sent via LinkedIn message instead of email"
}
```

**Response**: `200 OK` (updated follow-up with status: "sent")

---

### Cancel Follow-up

**Endpoint**: `DELETE /followup/{followup_id}`
**Description**: Cancel scheduled follow-up

**Response**: `204 No Content`

---

## Company Research

Automated company research and intelligence gathering.

### Research Company

**Endpoint**: `POST /research/company`
**Description**: Perform automated company research

**Request Body**:
```json
{
  "company_name": "Google",
  "deep_research": false
}
```

**Research Methods** (Safe & Ethical):
- Public APIs (Crunchbase, Clearbit)
- Company website scraping (public info only)
- LinkedIn company pages
- News aggregation
- Glassdoor reviews (public data)
- Financial reports (for public companies)

**Response**: `200 OK`
```json
{
  "company_name": "Google",
  "research_data": {
    "overview": {
      "industry": "Technology / Internet",
      "founded": 1998,
      "employees": "150,000+",
      "headquarters": "Mountain View, CA",
      "website": "https://www.google.com"
    },
    "financial": {
      "revenue": "$282.8B (2023)",
      "revenue_growth": "+9% YoY",
      "public_status": "Public (NASDAQ: GOOGL)"
    },
    "culture": {
      "glassdoor_rating": 4.3,
      "work_life_balance": 4.2,
      "culture_values": 4.1,
      "reviews_summary": "Innovative culture, great benefits, work-life balance varies by team"
    },
    "tech_stack": {
      "languages": ["Python", "Java", "C++", "Go"],
      "frameworks": ["TensorFlow", "Angular", "Kubernetes"],
      "infrastructure": ["Google Cloud Platform", "Borg", "Spanner"]
    },
    "hiring_insights": {
      "active_openings": 2500,
      "common_interview_questions": [
        "System design scenarios",
        "Algorithm optimization",
        "Google-specific behavioral questions"
      ],
      "average_interview_duration": "4-6 weeks"
    }
  },
  "cached": false,
  "researched_at": "2025-11-14T12:30:00Z",
  "expires_at": "2025-12-14T12:30:00Z"
}
```

**Caching**: Results cached for 30 days to avoid redundant API calls

---

### Get Cached Research

**Endpoint**: `GET /research/company/{company_name}`
**Description**: Get cached company research

**Response**: `200 OK` (same as research endpoint, with cached: true)

---

### List Researched Companies

**Endpoint**: `GET /research/companies`
**Description**: List all companies with cached research

**Response**: `200 OK`
```json
{
  "total": 25,
  "companies": [
    {
      "company_name": "Google",
      "researched_at": "2025-11-14T12:30:00Z",
      "expires_at": "2025-12-14T12:30:00Z",
      "has_tech_stack": true,
      "has_culture_data": true
    }
  ]
}
```

---

### Delete Company Research

**Endpoint**: `DELETE /research/company/{company_name}`
**Description**: Delete cached company research

**Response**: `204 No Content`

---

## Recommendations Engine

AI-powered job recommendations based on preferences and behavior.

### Get Recommendations

**Endpoint**: `GET /recommendations`
**Description**: Get personalized job recommendations

**Query Parameters**:
- `limit` (int): Number of recommendations (default: 10)
- `algorithm` (string): Algorithm to use (default: "hybrid")
  - `content`: Content-based filtering (skills, experience)
  - `collaborative`: Collaborative filtering (similar users)
  - `hybrid`: Combination of both
- `include_reasons` (bool): Include recommendation reasons (default: true)
- `filter_applied` (bool): Exclude already applied jobs (default: true)
- `min_score` (float): Minimum recommendation score (0-100, default: 50)

**Example Request**:
```
GET /recommendations?limit=10&algorithm=hybrid&min_score=70
```

**Response**: `200 OK`
```json
{
  "recommendations": [
    {
      "job_id": 42,
      "company": "Netflix",
      "job_title": "Senior Backend Engineer",
      "location": "Los Gatos, CA",
      "recommendation_score": 92.5,
      "match_score": 88.0,
      "reasons": [
        "Strong match for Python and microservices experience",
        "Salary range aligns with your expectations",
        "Similar to other jobs you applied to",
        "Company culture matches your preferences"
      ],
      "preference_factors": {
        "skills_match": 0.90,
        "location_match": 0.85,
        "salary_match": 0.95,
        "company_size_match": 0.92,
        "behavioral_score": 0.94
      }
    }
  ],
  "algorithm_used": "hybrid",
  "generated_at": "2025-11-14T13:00:00Z"
}
```

**Recommendation Score Components**:
- Skills match (35%)
- Behavioral signals - clicks, applications, time spent (30%)
- Salary/location preferences (20%)
- Company culture fit (15%)

---

### Learn from Click

**Endpoint**: `POST /recommendations/learn/click/{job_id}`
**Description**: Record job view/click for learning

**Response**: `200 OK`
```json
{
  "job_id": 42,
  "event": "click",
  "recorded": true
}
```

**Integration**: Automatically called by frontend when job is viewed

---

### Learn from Application

**Endpoint**: `POST /recommendations/learn/application/{job_id}`
**Description**: Record job application for learning (strong positive signal)

**Response**: `200 OK`
```json
{
  "job_id": 42,
  "event": "application",
  "recorded": true,
  "preferences_updated": true
}
```

**Integration**: Automatically called when job status changes to "applied"

---

### Learn from Dismissal

**Endpoint**: `POST /recommendations/learn/dismiss/{job_id}`
**Description**: Record job dismissal/not interested

**Request Body**:
```json
{
  "reason": "location_mismatch"
}
```

**Dismissal Reasons**:
- `location_mismatch`: Location not preferred
- `salary_too_low`: Salary below expectations
- `not_interested_role`: Role type not interesting
- `company_culture`: Company culture concerns
- `other`: Other reason

**Response**: `200 OK`
```json
{
  "job_id": 42,
  "event": "dismiss",
  "reason": "location_mismatch",
  "recorded": true,
  "preferences_updated": true
}
```

---

### Get Similar Jobs

**Endpoint**: `GET /recommendations/jobs/{job_id}/similar`
**Description**: Find jobs similar to given job

**Query Parameters**:
- `limit` (int): Number of similar jobs (default: 5)

**Response**: `200 OK`
```json
{
  "source_job_id": 42,
  "similar_jobs": [
    {
      "job_id": 43,
      "company": "Uber",
      "job_title": "Staff Backend Engineer",
      "similarity_score": 0.87,
      "similar_aspects": [
        "Python and Go required",
        "Microservices architecture",
        "Similar company size"
      ]
    }
  ]
}
```

---

### Generate Daily Digest

**Endpoint**: `POST /recommendations/digest/generate`
**Description**: Generate daily recommendations digest

**Response**: `200 OK`
```json
{
  "digest_id": "digest_20251114",
  "date": "2025-11-14",
  "recommendations_count": 10,
  "new_jobs_count": 5,
  "summary": {
    "top_recommendation": {
      "job_id": 42,
      "company": "Netflix",
      "job_title": "Senior Backend Engineer",
      "score": 92.5
    },
    "total_high_matches": 7,
    "total_medium_matches": 3
  },
  "email_sent": false
}
```

---

### Get Preferences

**Endpoint**: `GET /recommendations/preferences`
**Description**: Get learned user preferences

**Response**: `200 OK`
```json
{
  "skills_preferences": {
    "Python": 0.95,
    "FastAPI": 0.88,
    "PostgreSQL": 0.82,
    "AWS": 0.79
  },
  "location_preferences": {
    "Mountain View, CA": 0.90,
    "San Francisco, CA": 0.85,
    "Remote": 0.95
  },
  "company_size_preferences": {
    "large": 0.75,
    "startup": 0.60
  },
  "salary_expectations": {
    "min": 150000,
    "preferred": 180000,
    "max": 220000
  },
  "behavioral_patterns": {
    "avg_time_on_job": 145,
    "application_rate": 0.23,
    "preferred_job_types": ["backend", "full_stack"]
  }
}
```

---

## Skills Gap Analysis

Analyze skill gaps and get learning recommendations.

### Analyze Skills Gap

**Endpoint**: `POST /skills/analyze/{job_id}`
**Description**: Analyze skills gap for specific job

**Request Body**:
```json
{
  "include_resources": true
}
```

**Response**: `200 OK`
```json
{
  "job_id": 42,
  "overall_match_score": 78.5,
  "skill_analysis": {
    "matching_skills": [
      {
        "skill_name": "Python",
        "candidate_level": "advanced",
        "required_level": "advanced",
        "match_score": 100
      },
      {
        "skill_name": "FastAPI",
        "candidate_level": "intermediate",
        "required_level": "advanced",
        "match_score": 80
      }
    ],
    "missing_skills": [
      {
        "skill_name": "Kubernetes",
        "required_level": "intermediate",
        "importance": "high",
        "learning_resources": [
          {
            "title": "Kubernetes Basics Course",
            "type": "course",
            "url": "https://kubernetes.io/docs/tutorials/",
            "duration": "10 hours",
            "cost": "free"
          }
        ]
      },
      {
        "skill_name": "GraphQL",
        "required_level": "intermediate",
        "importance": "medium",
        "learning_resources": [
          {
            "title": "GraphQL Tutorial",
            "type": "tutorial",
            "url": "https://graphql.org/learn/",
            "duration": "5 hours",
            "cost": "free"
          }
        ]
      }
    ],
    "transferable_skills": [
      {
        "candidate_skill": "REST API Design",
        "relevant_to": "GraphQL",
        "transferability": 0.75
      }
    ]
  },
  "recommendations": {
    "immediate_actions": [
      "Complete Kubernetes basics course (10 hours)",
      "Build a small GraphQL API project"
    ],
    "timeline_estimate": "2-3 weeks to close critical gaps",
    "readiness_assessment": "Strong candidate with minor skill gaps"
  },
  "analyzed_at": "2025-11-14T14:00:00Z"
}
```

**Integration**: WebSocket notification sent when analysis completes

---

### Add Candidate Skills

**Endpoint**: `POST /skills/candidate`
**Description**: Add/update candidate skills profile

**Request Body**:
```json
{
  "skills": [
    {
      "skill_name": "Python",
      "skill_level": "advanced",
      "years_experience": 5,
      "category": "programming_language"
    },
    {
      "skill_name": "FastAPI",
      "skill_level": "intermediate",
      "years_experience": 2,
      "category": "framework"
    }
  ]
}
```

**Skill Levels**:
- `beginner`: 0-1 years
- `intermediate`: 1-3 years
- `advanced`: 3-5 years
- `expert`: 5+ years

**Skill Categories**:
- `programming_language`
- `framework`
- `database`
- `cloud_platform`
- `devops_tool`
- `soft_skill`
- `domain_knowledge`

**Response**: `201 Created`
```json
{
  "total_skills": 2,
  "skills": [
    {
      "id": 1,
      "skill_name": "Python",
      "skill_level": "advanced",
      "years_experience": 5,
      "category": "programming_language",
      "is_active": true
    }
  ]
}
```

---

### Get Candidate Skills

**Endpoint**: `GET /skills/candidate`
**Description**: Get candidate's skill profile

**Query Parameters**:
- `include_inactive` (bool): Include inactive skills (default: false)

**Response**: `200 OK` (array of skill objects)

---

### Get Skill Gaps Summary

**Endpoint**: `GET /skills/gaps/summary`
**Description**: Get summary of skill gaps across all saved jobs

**Response**: `200 OK`
```json
{
  "total_jobs_analyzed": 15,
  "overall_readiness": 72.5,
  "most_common_gaps": [
    {
      "skill_name": "Kubernetes",
      "frequency": 12,
      "average_importance": "high",
      "learning_priority": 1
    },
    {
      "skill_name": "GraphQL",
      "frequency": 8,
      "average_importance": "medium",
      "learning_priority": 2
    }
  ],
  "strongest_skills": [
    "Python",
    "FastAPI",
    "PostgreSQL"
  ],
  "recommended_learning_path": [
    {
      "skill": "Kubernetes",
      "reason": "Required by 80% of target jobs",
      "estimated_learning_time": "20 hours",
      "priority": "high"
    }
  ]
}
```

---

### Get Learning Resources

**Endpoint**: `GET /skills/resources/{skill_name}`
**Description**: Get curated learning resources for skill

**Query Parameters**:
- `resource_type` (string): Filter by type (course, tutorial, book, video)
- `max_cost` (float): Maximum cost filter

**Response**: `200 OK`
```json
{
  "skill_name": "Kubernetes",
  "resources": [
    {
      "id": 1,
      "title": "Kubernetes Basics Course",
      "type": "course",
      "provider": "Kubernetes.io",
      "url": "https://kubernetes.io/docs/tutorials/",
      "duration": "10 hours",
      "difficulty": "beginner",
      "cost": "free",
      "rating": 4.8,
      "description": "Official Kubernetes tutorial..."
    }
  ]
}
```

---

## Calendar Integration

Google Calendar integration for interviews and deadlines.

### Schedule Interview in Calendar

**Endpoint**: `POST /calendar/interview`
**Description**: Create interview event in Google Calendar

**Request Body**:
```json
{
  "job_id": 1,
  "interview_type": "technical",
  "start_time": "2025-11-15T14:00:00Z",
  "duration_minutes": 90,
  "location": "Zoom - https://zoom.us/j/123456789",
  "interviewer_email": "interviewer@company.com",
  "notes": "Technical round - system design focus"
}
```

**Response**: `201 Created`
```json
{
  "event_id": "cal_abc123",
  "summary": "Technical Interview: Senior Software Engineer at Google",
  "start_time": "2025-11-15T14:00:00Z",
  "end_time": "2025-11-15T15:30:00Z",
  "location": "Zoom - https://zoom.us/j/123456789",
  "calendar_link": "https://calendar.google.com/calendar/event?eid=...",
  "reminders": [
    {"method": "popup", "minutes": 1440},
    {"method": "popup", "minutes": 60},
    {"method": "popup", "minutes": 15}
  ],
  "created_at": "2025-11-14T10:00:00Z"
}
```

**Automatic Integration**:
- Interview record created in database with calendar_event_id
- WebSocket notification: `interview.scheduled`

---

### Create Follow-up Reminder

**Endpoint**: `POST /calendar/follow-up-reminder`
**Description**: Create follow-up reminder in calendar

**Request Body**:
```json
{
  "job_id": 1,
  "follow_up_type": "post_application",
  "reminder_time": "2025-11-17T09:00:00Z",
  "notes": "Follow up on application status"
}
```

**Response**: `201 Created`
```json
{
  "event_id": "cal_def456",
  "summary": "Follow-up: Senior Software Engineer at Google",
  "start_time": "2025-11-17T09:00:00Z",
  "end_time": "2025-11-17T09:30:00Z",
  "calendar_link": "https://calendar.google.com/calendar/event?eid=...",
  "reminders": [
    {"method": "popup", "minutes": 1440},
    {"method": "popup", "minutes": 60}
  ]
}
```

---

### Create Deadline Reminder

**Endpoint**: `POST /calendar/deadline-reminder`
**Description**: Create application deadline reminder (all-day event)

**Request Body**:
```json
{
  "job_id": 1,
  "deadline": "2025-11-20",
  "job_url": "https://careers.google.com/jobs/123"
}
```

**Response**: `201 Created`
```json
{
  "event_id": "cal_ghi789",
  "summary": "Application Deadline: Senior Software Engineer at Google",
  "date": "2025-11-20",
  "all_day": true,
  "calendar_link": "https://calendar.google.com/calendar/event?eid=...",
  "reminders": [
    {"method": "popup", "minutes": 4320},
    {"method": "popup", "minutes": 1440},
    {"method": "popup", "minutes": 180}
  ]
}
```

---

### Get Upcoming Events

**Endpoint**: `GET /calendar/upcoming`
**Description**: Get upcoming calendar events

**Query Parameters**:
- `days` (int): Days to look ahead (default: 7)
- `limit` (int): Max events to return (default: 10)

**Response**: `200 OK`
```json
{
  "events": [
    {
      "event_id": "cal_abc123",
      "summary": "Technical Interview: Senior Software Engineer at Google",
      "start_time": "2025-11-15T14:00:00Z",
      "event_type": "interview",
      "job_id": 1,
      "company": "Google"
    },
    {
      "event_id": "cal_def456",
      "summary": "Follow-up: Senior Software Engineer at Netflix",
      "start_time": "2025-11-17T09:00:00Z",
      "event_type": "follow_up",
      "job_id": 2,
      "company": "Netflix"
    }
  ]
}
```

---

### Get Events for Job

**Endpoint**: `GET /calendar/job/{job_id}`
**Description**: Get all calendar events for specific job

**Response**: `200 OK` (array of event objects)

---

### Delete Calendar Event

**Endpoint**: `DELETE /calendar/event/{event_id}`
**Description**: Delete event from Google Calendar

**Response**: `204 No Content`

---

## Analytics & Statistics

Success analytics and performance metrics.

### Get Overview Stats

**Endpoint**: `GET /analytics/overview`
**Description**: Get high-level statistics dashboard

**Response**: `200 OK`
```json
{
  "period": "all_time",
  "summary": {
    "total_jobs_tracked": 120,
    "total_applications": 45,
    "active_applications": 15,
    "interviews_scheduled": 12,
    "offers_received": 3,
    "offers_accepted": 1
  },
  "conversion_funnel": {
    "jobs_saved": 120,
    "jobs_applied": 45,
    "applications_to_interview": 12,
    "interviews_to_offer": 3,
    "offers_to_acceptance": 1
  },
  "conversion_rates": {
    "save_to_apply": 0.375,
    "apply_to_interview": 0.267,
    "interview_to_offer": 0.250,
    "offer_to_accept": 0.333,
    "overall_success_rate": 0.008
  },
  "timeline_metrics": {
    "average_days_to_apply": 2.5,
    "average_days_to_interview": 8.3,
    "average_days_to_offer": 21.7,
    "average_application_lifetime": 18.5
  }
}
```

---

### Get Funnel Analysis

**Endpoint**: `GET /analytics/funnel`
**Description**: Detailed conversion funnel analysis

**Query Parameters**:
- `start_date` (date): Start of analysis period
- `end_date` (date): End of analysis period
- `group_by` (string): Group by dimension (company, location, source)

**Response**: `200 OK`
```json
{
  "period": {
    "start": "2025-10-01",
    "end": "2025-11-14"
  },
  "overall_funnel": {
    "stage_1_saved": 50,
    "stage_2_applied": 20,
    "stage_3_interviewing": 6,
    "stage_4_offer": 2,
    "stage_5_accepted": 1
  },
  "breakdown_by_source": {
    "linkedin": {
      "saved": 30,
      "applied": 12,
      "conversion_rate": 0.40
    },
    "indeed": {
      "saved": 20,
      "applied": 8,
      "conversion_rate": 0.40
    }
  },
  "drop_off_analysis": {
    "highest_drop_off": "saved_to_applied",
    "drop_off_rate": 0.60,
    "reasons": [
      "Low match score",
      "Location mismatch",
      "Salary below expectations"
    ]
  }
}
```

---

### Get Success Patterns

**Endpoint**: `GET /analytics/success-patterns`
**Description**: Analyze patterns in successful applications

**Response**: `200 OK`
```json
{
  "successful_applications": 3,
  "common_patterns": {
    "match_score_range": {
      "min": 75,
      "avg": 85.7,
      "max": 92
    },
    "company_characteristics": {
      "size": ["large", "enterprise"],
      "industries": ["Technology", "SaaS"],
      "locations": ["Mountain View, CA", "San Francisco, CA"]
    },
    "skills_frequently_matched": [
      "Python",
      "FastAPI",
      "Microservices",
      "AWS"
    ],
    "timeline_patterns": {
      "avg_days_to_apply": 1.3,
      "avg_days_to_interview": 7.0,
      "avg_days_to_offer": 19.7
    }
  },
  "recommendations": [
    "Focus on jobs with match score >= 75",
    "Prioritize applications in Technology/SaaS",
    "Apply within 2 days of saving for best results"
  ]
}
```

---

### Get Performance Trends

**Endpoint**: `GET /analytics/trends`
**Description**: Time-series performance trends

**Query Parameters**:
- `metric` (string): Metric to track (applications, interviews, offers)
- `granularity` (string): Time granularity (day, week, month)
- `period_days` (int): Days to look back (default: 90)

**Response**: `200 OK`
```json
{
  "metric": "applications",
  "granularity": "week",
  "data_points": [
    {
      "period": "2025-W42",
      "start_date": "2025-10-14",
      "end_date": "2025-10-20",
      "value": 8,
      "change_from_previous": "+2"
    },
    {
      "period": "2025-W43",
      "start_date": "2025-10-21",
      "end_date": "2025-10-27",
      "value": 10,
      "change_from_previous": "+2"
    }
  ],
  "trend": "increasing",
  "average": 7.5,
  "peak": {
    "period": "2025-W43",
    "value": 10
  }
}
```

---

### Learn from Success

**Endpoint**: `POST /analytics/learn/{job_id}`
**Description**: Record successful outcome for machine learning

**Request Body**:
```json
{
  "outcome": "offer_accepted",
  "factors": {
    "match_score": 85.5,
    "applied_within_days": 1,
    "company_size": "large",
    "had_referral": false
  }
}
```

**Integration**: Automatically called when offer is accepted

---

## Cache Management

Redis cache management and monitoring.

### Get Cache Stats

**Endpoint**: `GET /cache/stats`
**Description**: Get cache statistics and health

**Response**: `200 OK`
```json
{
  "cache_type": "redis",
  "redis_available": true,
  "connection_healthy": true,
  "stats": {
    "total_keys": 147,
    "memory_used": "2.5 MB",
    "hit_rate": 0.87,
    "total_hits": 1250,
    "total_misses": 180
  },
  "by_namespace": {
    "job_analysis": {
      "keys": 45,
      "avg_ttl": 86400,
      "hit_rate": 0.92
    },
    "company_research": {
      "keys": 25,
      "avg_ttl": 2592000,
      "hit_rate": 0.95
    },
    "recommendations": {
      "keys": 30,
      "avg_ttl": 3600,
      "hit_rate": 0.78
    }
  }
}
```

**Cache Namespaces**:
- `job_analysis`: Job analysis results (1 day TTL)
- `company_research`: Company research data (30 days TTL)
- `recommendations`: Recommendation results (1 hour TTL)
- `skills_gap`: Skills gap analysis (1 day TTL)
- `job_details`: Job details (12 hours TTL)
- `stats`: Statistics (5 minutes TTL)
- `calendar`: Calendar data (1 hour TTL)
- `follow_ups`: Follow-up data (1 hour TTL)
- `websocket`: WebSocket state (5 minutes TTL)
- `rate_limit`: Rate limiting (1 minute TTL)
- `session`: User sessions (24 hours TTL)

---

### Get Cached Item

**Endpoint**: `GET /cache/{namespace}/{key}`
**Description**: Get specific cached item

**Example Request**:
```
GET /cache/job_analysis/job:42
```

**Response**: `200 OK`
```json
{
  "namespace": "job_analysis",
  "key": "job:42",
  "value": {
    "match_score": 85.5,
    "recommendation": "apply_now",
    "analyzed_at": "2025-11-14T10:32:00Z"
  },
  "ttl_remaining": 82800,
  "cached_at": "2025-11-14T10:32:00Z"
}
```

---

### Invalidate Cache

**Endpoint**: `DELETE /cache/{namespace}/{key}`
**Description**: Invalidate specific cache entry

**Response**: `204 No Content`

---

### Clear Namespace

**Endpoint**: `DELETE /cache/{namespace}`
**Description**: Clear all cache entries in namespace

**Response**: `200 OK`
```json
{
  "namespace": "recommendations",
  "keys_deleted": 30,
  "success": true
}
```

---

### Warm Cache

**Endpoint**: `POST /cache/warm`
**Description**: Pre-populate cache with frequently accessed data

**Request Body**:
```json
{
  "namespaces": ["job_analysis", "company_research"],
  "priority": "high"
}
```

**Response**: `200 OK`
```json
{
  "namespaces_warmed": 2,
  "total_keys_created": 75,
  "duration_seconds": 12.5
}
```

---

## WebSocket Real-time Updates

Real-time event notifications via WebSocket.

See [WEBSOCKET_GUIDE.md](./WEBSOCKET_GUIDE.md) for detailed documentation.

### Connect to WebSocket

**Endpoint**: `WS /ws`
**Description**: Establish WebSocket connection

**Query Parameters**:
- `user_id` (string): User identifier for multi-device sync
- `channels` (string): Comma-separated channel list to subscribe

**Available Channels**:
- `jobs`: Job-related events
- `applications`: Application status changes
- `recommendations`: New recommendations
- `skills`: Skills gap analysis
- `followups`: Follow-up reminders
- `interviews`: Interview events
- `system`: System notifications

**Example Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws?user_id=user123&channels=jobs,applications');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.data);
};
```

**Welcome Message**:
```json
{
  "type": "system.connected",
  "data": {
    "connection_id": "conn_abc123",
    "user_id": "user123",
    "channels": ["jobs", "applications"],
    "message": "Connected to WebSocket server"
  },
  "timestamp": "2025-11-14T15:00:00Z"
}
```

---

### Subscribe to Channel

**Client → Server**:
```json
{
  "action": "subscribe",
  "channel": "interviews"
}
```

**Server → Client**:
```json
{
  "type": "system.subscribed",
  "data": {
    "channel": "interviews",
    "subscriber_count": 5
  },
  "timestamp": "2025-11-14T15:01:00Z"
}
```

---

### Event Types

**job.created**:
```json
{
  "type": "job.created",
  "data": {
    "job_id": 42,
    "company": "Google",
    "job_title": "Senior Software Engineer"
  },
  "timestamp": "2025-11-14T15:00:00Z"
}
```

**job.analyzed**:
```json
{
  "type": "job.analyzed",
  "data": {
    "job_id": 42,
    "match_score": 85.5,
    "recommendation": "apply_now"
  },
  "timestamp": "2025-11-14T15:02:00Z"
}
```

**application.status_changed**:
```json
{
  "type": "application.status_changed",
  "data": {
    "job_id": 42,
    "old_status": "applied",
    "new_status": "interviewing"
  },
  "timestamp": "2025-11-14T15:05:00Z"
}
```

**recommendations.new**:
```json
{
  "type": "recommendations.new",
  "data": {
    "count": 10,
    "top_recommendations": [
      {"job_id": 50, "score": 92.5}
    ]
  },
  "timestamp": "2025-11-14T15:10:00Z"
}
```

**interview.scheduled**:
```json
{
  "type": "interview.scheduled",
  "data": {
    "job_id": 42,
    "interview_type": "technical",
    "scheduled_date": "2025-11-15T14:00:00Z"
  },
  "timestamp": "2025-11-14T15:15:00Z"
}
```

**skill_gap.completed**:
```json
{
  "type": "skill_gap.completed",
  "data": {
    "job_id": 42,
    "overall_match": 78.5,
    "missing_skills_count": 3
  },
  "timestamp": "2025-11-14T15:20:00Z"
}
```

**followup.due**:
```json
{
  "type": "followup.due",
  "data": {
    "followup_id": 10,
    "job_title": "Senior Software Engineer",
    "company": "Google",
    "hours_until_due": 2
  },
  "timestamp": "2025-11-14T15:25:00Z"
}
```

---

### Get Connection Stats

**Endpoint**: `GET /connections`
**Description**: Get WebSocket connection statistics (admin)

**Response**: `200 OK`
```json
{
  "total_connections": 15,
  "unique_users": 12,
  "channels": {
    "jobs": 10,
    "applications": 8,
    "recommendations": 5,
    "interviews": 3
  },
  "channel_details": [
    {
      "channel": "jobs",
      "subscribers": 10,
      "last_event": "2025-11-14T15:25:00Z"
    }
  ]
}
```

---

### Broadcast Message

**Endpoint**: `POST /broadcast`
**Description**: Broadcast message to all connected clients (admin)

**Request Body**:
```json
{
  "message": "System maintenance in 5 minutes",
  "channel": "system",
  "severity": "warning"
}
```

**Response**: `200 OK`
```json
{
  "success": true,
  "recipients": 15,
  "channel": "system"
}
```

---

## Job Scraping

Automated job scraping from multiple sources.

### Scrape LinkedIn

**Endpoint**: `POST /scraping/linkedin`
**Description**: Scrape jobs from LinkedIn

**Request Body**:
```json
{
  "keywords": "software engineer",
  "location": "San Francisco Bay Area",
  "experience_level": "mid_senior",
  "job_type": "full_time",
  "max_results": 50
}
```

**Response**: `200 OK`
```json
{
  "source": "linkedin",
  "jobs_found": 45,
  "jobs_saved": 32,
  "jobs_skipped": 13,
  "scrape_duration": 45.2,
  "jobs": [
    {
      "job_id": "linkedin_123456",
      "company": "Google",
      "job_title": "Senior Software Engineer",
      "location": "Mountain View, CA",
      "posted_date": "2 days ago",
      "saved": true
    }
  ]
}
```

---

### Scrape Indeed

**Endpoint**: `POST /scraping/indeed`
**Description**: Scrape jobs from Indeed

**Similar to LinkedIn endpoint**

---

### Scrape Glassdoor

**Endpoint**: `POST /scraping/glassdoor`
**Description**: Scrape jobs from Glassdoor

**Similar to LinkedIn endpoint**

---

### Batch Scrape

**Endpoint**: `POST /scraping/batch`
**Description**: Scrape from multiple sources

**Request Body**:
```json
{
  "sources": ["linkedin", "indeed", "glassdoor"],
  "keywords": "software engineer",
  "location": "San Francisco Bay Area",
  "max_results_per_source": 20
}
```

**Response**: `200 OK`
```json
{
  "total_jobs_found": 85,
  "total_jobs_saved": 52,
  "by_source": {
    "linkedin": {
      "found": 30,
      "saved": 20
    },
    "indeed": {
      "found": 32,
      "saved": 18
    },
    "glassdoor": {
      "found": 23,
      "saved": 14
    }
  },
  "duration": 120.5
}
```

---

## Error Responses

All endpoints follow consistent error format:

**400 Bad Request**:
```json
{
  "detail": "Invalid job_id provided"
}
```

**404 Not Found**:
```json
{
  "detail": "Job not found"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Error analyzing job: Connection timeout"
}
```

---

## Rate Limiting

**Development**: No rate limiting
**Production**:
- Anonymous: 100 requests/hour
- Authenticated: 1000 requests/hour
- Cached endpoints: Higher limits

**Rate Limit Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1699900000
```

---

## Pagination

List endpoints support pagination:

**Query Parameters**:
- `skip` (int): Offset (default: 0)
- `limit` (int): Page size (default: 100, max: 1000)

**Response Format**:
```json
{
  "total": 250,
  "items": [...],
  "skip": 0,
  "limit": 100,
  "has_more": true
}
```

---

## Versioning

Current version: `v1`

**API Path**: `/api/v1/...`

Breaking changes will increment version number (`v2`, `v3`, etc.)

---

## Support

- **Documentation**: [Full documentation](../README.md)
- **Integration Guide**: [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)
- **WebSocket Guide**: [WEBSOCKET_GUIDE.md](./WEBSOCKET_GUIDE.md)
- **Issues**: GitHub Issues
- **Email**: support@example.com
