# Feature Integration Guide

Complete guide to understanding how all features work together seamlessly in the Job Automation System.

---

## Table of Contents

1. [Overview](#overview)
2. [Integration Architecture](#integration-architecture)
3. [Workflow Examples](#workflow-examples)
4. [Feature Interactions](#feature-interactions)
5. [Event Flow Diagrams](#event-flow-diagrams)
6. [Customizing Integrations](#customizing-integrations)

---

## Overview

The Job Automation System is built with **tight integration** between all features, creating seamless workflows that reduce manual work and improve job search efficiency.

### Integration Orchestrator

The `IntegrationOrchestrator` class (in `backend/app/services/integration_service.py`) coordinates all feature interactions:

- **Automatic Triggers**: Features trigger each other based on events
- **Event Propagation**: Real-time WebSocket notifications across features
- **Cache Coordination**: Smart cache invalidation across systems
- **Learning Loops**: Preferences learned from user actions

### Key Integration Points

```
┌─────────────────────────────────────────────────────────┐
│                   Integration Layer                      │
│              (IntegrationOrchestrator)                   │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬────┘
   │      │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼
  Jobs   ATS   Recs  Skills  F-up  Calendar Cache  WS
```

---

## Integration Architecture

### Layer 1: Core Services

Individual feature services operate independently:

- **JobService**: Job CRUD operations
- **ATSService**: Application tracking
- **AnalysisService**: Job matching
- **DocumentService**: Resume/cover letter generation

### Layer 2: Integration Orchestrator

Coordinates workflows across services:

```python
class IntegrationOrchestrator:
    async def on_job_created(job_id):
        # 1. Research company (if new)
        # 2. Analyze skills gap
        # 3. Invalidate recommendation cache
        # 4. Send WebSocket notification

    async def on_application_status_changed(job_id, old, new):
        # 1. Schedule follow-ups
        # 2. Create calendar events
        # 3. Learn from outcome
        # 4. Send WebSocket notification
```

### Layer 3: Event Broadcasting

WebSocket manager broadcasts events to connected clients:

```python
class WebSocketManager:
    async def emit_event(event_type, data, channel):
        # Broadcast to all subscribers on channel
```

### Layer 4: Cache Management

Redis cache reduces duplicate API calls and improves performance:

```python
class CacheService:
    def get(namespace, key):
        # Return cached value or None

    def set(namespace, key, value, ttl):
        # Store with expiration
```

---

## Workflow Examples

### Workflow 1: One-Click Job Processing

**Trigger**: User clicks "Save Job" in Chrome extension

**Steps**:

1. **Extension** → **POST /jobs/process**
   - Sends job data from LinkedIn/Indeed/Glassdoor

2. **Jobs API** → Save to database
   - Creates Job record with status "processing"

3. **Jobs API** → **integrate_job_created()**
   - Triggers integration orchestrator

4. **Integration Orchestrator** → **Company Research**
   - Checks cache for company research
   - If not cached: Fetches company info, tech stack, culture
   - Caches for 30 days

5. **Integration Orchestrator** → **Skills Gap Analysis**
   - Extracts required skills from job description
   - Compares with candidate skills
   - Calculates match score
   - Generates learning recommendations

6. **Integration Orchestrator** → **WebSocket Notification**
   - Sends `job.created` event to subscribers

7. **Background Task** → **Job Analysis**
   - Claude AI semantic matching
   - job-match-analyzer skill evaluation
   - Generates detailed analysis

8. **Analysis Complete** → **integrate_job_analyzed()**
   - Updates job with match score
   - Sends `job.analyzed` WebSocket event
   - Caches analysis results

9. **If Match Score >= 70** → **Document Generation**
   - Generates tailored resume
   - Generates tailored cover letter
   - Uploads to Google Drive
   - Sends email notification

**Result**: Job fully processed, analyzed, and documents ready in under 30 seconds.

**User Experience**:
```
[Extension Click] → [Processing...] → [WebSocket: 85% match!]
                                   → [Documents ready!]
```

---

### Workflow 2: Application Status Change

**Trigger**: User updates application status to "applied"

**Steps**:

1. **Frontend** → **POST /ats/jobs/{job_id}/status**
   ```json
   {"status": "applied", "notes": "Applied via company website"}
   ```

2. **ATS Service** → Validate status transition
   - Checks if transition is valid (saved → applied)
   - Creates status change event

3. **ATS API** → **integrate_status_change()**
   - Triggers integration orchestrator

4. **Integration Orchestrator** → **Schedule Follow-ups**
   - Creates follow-up sequence:
     - Day 3: Post-application follow-up
     - Day 7: Second check-in
     - Day 14: Final follow-up

5. **Integration Orchestrator** → **WebSocket Notification**
   - Sends `application.status_changed` event

6. **Integration Orchestrator** → **Recommendation Learning**
   - Records application as positive signal
   - Updates user preference model
   - Increases weight for similar jobs

7. **Integration Orchestrator** → **Cache Invalidation**
   - Invalidates job details cache
   - Invalidates statistics cache

**Result**: Follow-ups automatically scheduled, preferences learned, real-time UI update.

---

### Workflow 3: Interview Scheduling

**Trigger**: User schedules interview

**Steps**:

1. **Frontend** → **POST /ats/interviews**
   ```json
   {
     "job_id": 42,
     "interview_type": "technical",
     "scheduled_date": "2025-11-15T14:00:00Z",
     "duration_minutes": 90,
     "interviewer_email": "interviewer@company.com"
   }
   ```

2. **ATS Service** → Create interview record
   - Stores in database

3. **ATS Service** → **Calendar Integration**
   - Calls Google Calendar API
   - Creates calendar event with:
     - Title: "Technical Interview: [Job Title] at [Company]"
     - Duration: 90 minutes
     - Reminders: 1 day, 1 hour, 15 minutes
     - Attendees: interviewer@company.com

4. **Calendar Service** → Returns event ID
   - Stores `calendar_event_id` in interview record

5. **Integration Orchestrator** → **Update Job Status**
   - If status is "applied": Changes to "interview_scheduled"
   - If already "interviewing": Keeps status

6. **Integration Orchestrator** → **Schedule Post-Interview Follow-up**
   - Creates follow-up for 1 day after interview
   - Thank you note template pre-filled

7. **Integration Orchestrator** → **WebSocket Notifications**
   - Sends `interview.scheduled` event
   - Sends `application.status_changed` event (if status changed)

**Result**: Interview in Google Calendar, auto follow-up scheduled, status updated, real-time notification sent.

**Calendar Event Created**:
```
Title: Technical Interview: Senior Software Engineer at Google
Time: Nov 15, 2025 2:00 PM - 3:30 PM
Location: Zoom - [link]
Reminders: 1 day before, 1 hour before, 15 minutes before
```

---

### Workflow 4: Recommendation Generation

**Trigger**: Daily cron job or manual request

**Steps**:

1. **Cron/Manual** → **GET /recommendations**
   - Request with filters: `algorithm=hybrid&min_score=70`

2. **Recommendation Engine** → Load user preferences
   - Analyzes past applications
   - Extracts preferred skills, locations, companies
   - Calculates behavioral patterns

3. **Recommendation Engine** → Content-based filtering
   - Matches jobs based on skills and requirements
   - Scores based on similarity to successful applications

4. **Recommendation Engine** → Collaborative filtering
   - Finds similar users (by application patterns)
   - Recommends jobs they applied to

5. **Recommendation Engine** → Hybrid scoring
   - Combines content + collaborative scores
   - Applies preference weights
   - Ranks by final score

6. **Integration Orchestrator** → **Cache Results**
   - Caches top recommendations (1 hour TTL)

7. **Integration Orchestrator** → **WebSocket Notification**
   - Sends `recommendations.new` event with count and top 5

**Result**: Personalized recommendations delivered, cached for fast access.

**Recommendation Output**:
```json
[
  {
    "job_id": 50,
    "company": "Netflix",
    "score": 92.5,
    "reasons": [
      "Strong Python + microservices match",
      "Similar to jobs you applied to",
      "Salary aligns with preferences"
    ]
  }
]
```

---

### Workflow 5: Skills Gap Analysis

**Trigger**: New job created or manual analysis

**Steps**:

1. **Integration Orchestrator** → Extract job requirements
   - Parses job description
   - Identifies required skills with importance levels

2. **Skills Service** → Load candidate skills
   - Retrieves candidate skill profile from database

3. **Skills Service** → Compare skills
   - **Matching**: Skills candidate has at required level
   - **Partial**: Skills candidate has but below required level
   - **Missing**: Skills candidate doesn't have

4. **Skills Service** → Identify transferable skills
   - Finds candidate skills related to missing skills
   - Calculates transferability scores

5. **Skills Service** → Generate learning recommendations
   - Fetches curated resources for missing skills
   - Prioritizes by importance
   - Estimates learning time

6. **Integration Orchestrator** → **Cache Analysis**
   - Caches results (1 day TTL)

7. **Integration Orchestrator** → **WebSocket Notification**
   - Sends `skill_gap.completed` event

**Result**: Detailed gap analysis with actionable learning plan.

**Analysis Output**:
```
Overall Match: 78.5%

Matching Skills (8):
- Python (Advanced) ✓
- FastAPI (Intermediate) ✓
- PostgreSQL (Advanced) ✓

Partial Matches (2):
- Kubernetes (You: Beginner, Required: Intermediate)
  → Recommendation: Complete Kubernetes Basics (10 hours)

Missing Skills (3):
- GraphQL (Required: Intermediate)
  → Resource: GraphQL Tutorial (5 hours)
  → Transferable: REST API experience (75% relevant)
```

---

## Feature Interactions

### 1. Jobs ↔ Analysis

**Trigger**: Job created
**Action**: Automatic analysis
**Result**: Match score, recommendation, strengths/concerns

```python
# In jobs.py
job = Job(**job_data)
db.add(job)
db.commit()

# Trigger analysis
await integrate_job_created(db, job.id, auto_process=True)
```

---

### 2. ATS ↔ Follow-ups

**Trigger**: Status change to "applied" or "interviewing"
**Action**: Schedule follow-up sequence
**Result**: Automated follow-up emails scheduled

```python
# In integration_service.py
if new_status == "applied":
    followup_service.schedule_followup_sequence(
        job_id=job_id,
        sequence_name="post_application"
    )
```

**Follow-up Sequence**:
- Day 3: "Thank you for considering my application..."
- Day 7: "I wanted to follow up on my application..."
- Day 14: "I remain very interested in this position..."

---

### 3. ATS ↔ Calendar

**Trigger**: Interview scheduled
**Action**: Create Google Calendar event
**Result**: Interview in calendar with reminders

```python
# In integration_service.py
if new_status == "interview_scheduled" and interview_data:
    calendar = get_calendar_service()
    event = calendar.create_interview_event(...)
    interview.calendar_event_id = event.get("id")
```

---

### 4. Jobs ↔ Company Research

**Trigger**: Job created with new company
**Action**: Auto-research company
**Result**: Company info, tech stack, culture cached

```python
# In integration_service.py
if job.company and auto_process:
    cached = cache.get(CacheNamespace.COMPANY_RESEARCH, f"company:{job.company}")
    if not cached:
        research_service.research_company(job.company, auto_cache=True)
```

**Research Data Cached**:
- Company overview (size, industry, founded)
- Financial data (revenue, growth)
- Culture data (Glassdoor rating, reviews)
- Tech stack (languages, frameworks, tools)
- Hiring insights (interview questions, timeline)

---

### 5. Jobs ↔ Skills Gap Analysis

**Trigger**: Job created
**Action**: Analyze skill gaps
**Result**: Match score, missing skills, learning resources

```python
# In integration_service.py
if auto_process and has_candidate_skills:
    analysis = skills_service.analyze_skill_gaps(job_id, include_resources=False)
    await notify_skill_gap_completed(job_id, analysis.overall_match_score)
```

---

### 6. Recommendations ↔ Learning

**Trigger**: Job applied, dismissed, or clicked
**Action**: Update preference model
**Result**: Better recommendations

```python
# Application (strong positive signal)
if new_status in ["applied", "interviewing", "offer_received"]:
    rec_service.learn_from_application(job_id)

# Dismissal (negative signal)
elif new_status in ["rejected", "withdrawn"]:
    rec_service.learn_from_dismissal(job_id, reason=f"Status: {new_status}")
```

---

### 7. All Features ↔ WebSocket

**Trigger**: Any significant event
**Action**: Broadcast via WebSocket
**Result**: Real-time UI updates

```python
# Job analyzed
await notify_job_analyzed(job_id, match_score, recommendation)

# Status changed
await notify_application_status_changed(job_id, old_status, new_status)

# Interview scheduled
await notify_interview_scheduled(job_id, interview_data)

# Skills analysis done
await notify_skill_gap_completed(job_id, overall_match)

# Follow-up due
await notify_follow_up_due(followup_id, job_id)
```

---

### 8. All Features ↔ Cache

**Trigger**: Read/write operations
**Action**: Cache frequently accessed data
**Result**: Faster response times, reduced API calls

**Cache Strategy**:
```python
# Read-through caching
cached = cache.get(namespace, key)
if not cached:
    data = fetch_from_database()
    cache.set(namespace, key, data, ttl)
    return data
return cached

# Write-through caching
def update_job(job_id, data):
    job = db.update(job_id, data)
    cache.set(CacheNamespace.JOB_DETAILS, f"job:{job_id}", job, ttl)
    return job

# Cache invalidation
def delete_job(job_id):
    db.delete(job_id)
    cache.delete(CacheNamespace.JOB_DETAILS, f"job:{job_id}")
    cache.delete_pattern(CacheNamespace.STATS, "*")
```

---

## Event Flow Diagrams

### Complete Job Processing Flow

```
User Action (Extension Click)
    │
    ▼
POST /jobs/process
    │
    ├─→ Save Job to DB ───────────────┐
    │                                  │
    ├─→ integrate_job_created()       │
    │       │                          │
    │       ├─→ Company Research ──────┤
    │       │   (cached 30 days)       │
    │       │                          │
    │       ├─→ Skills Gap Analysis ───┤
    │       │   (match score calc)     │
    │       │                          │
    │       └─→ WS: job.created ───────┤
    │                                  │
    ├─→ Background: Analyze Job        │
    │       │                          │
    │       ├─→ Claude AI Analysis     │
    │       ├─→ Semantic Matching      │
    │       └─→ Match Score            │
    │                                  │
    ├─→ integrate_job_analyzed()       │
    │       │                          │
    │       ├─→ Cache Analysis ────────┤
    │       ├─→ WS: job.analyzed ──────┤
    │       └─→ Learn Preferences ─────┤
    │                                  │
    └─→ IF score >= 70:                │
            │                          │
            ├─→ Generate Resume ───────┤
            ├─→ Generate Cover Letter ─┤
            ├─→ Upload to Drive ───────┤
            └─→ Send Email ────────────┘
```

### Application Status Change Flow

```
User Updates Status to "Applied"
    │
    ▼
POST /ats/jobs/{id}/status
    │
    ├─→ Validate Transition
    │   (saved → applied ✓)
    │
    ├─→ Update Status in DB
    │
    ├─→ Create Status Event
    │
    ├─→ integrate_status_change()
    │       │
    │       ├─→ Schedule Follow-ups
    │       │   ├─→ Day 3: Post-app
    │       │   ├─→ Day 7: Check-in
    │       │   └─→ Day 14: Final
    │       │
    │       ├─→ Learn from Application
    │       │   ├─→ Update preferences
    │       │   └─→ Adjust rec weights
    │       │
    │       ├─→ Invalidate Caches
    │       │   ├─→ Job details
    │       │   └─→ Statistics
    │       │
    │       └─→ WebSocket Broadcast
    │           └─→ application.status_changed
    │
    └─→ Return Updated Status
```

### Interview Scheduling Flow

```
User Schedules Interview
    │
    ▼
POST /ats/interviews
    │
    ├─→ Create Interview Record
    │
    ├─→ Google Calendar Integration
    │   │
    │   ├─→ Authenticate OAuth
    │   ├─→ Create Event
    │   │   ├─→ Title: [Type] Interview: [Job] at [Company]
    │   │   ├─→ Duration: [X] minutes
    │   │   ├─→ Location: [Zoom/Address]
    │   │   ├─→ Reminders: 1d, 1h, 15m
    │   │   └─→ Attendees: [Interviewer]
    │   │
    │   └─→ Return Event ID
    │
    ├─→ Store calendar_event_id
    │
    ├─→ Update Job Status
    │   └─→ applied → interview_scheduled
    │
    ├─→ Schedule Post-Interview Follow-up
    │   └─→ 1 day after: Thank you note
    │
    └─→ WebSocket Notifications
        ├─→ interview.scheduled
        └─→ application.status_changed
```

---

## Customizing Integrations

### Adding Custom Integration Points

Extend the IntegrationOrchestrator with custom workflows:

```python
# In integration_service.py

class IntegrationOrchestrator:
    # ... existing methods ...

    async def on_custom_event(self, data):
        """
        Custom integration workflow

        Example: Send Slack notification when high-match job found
        """
        if data["match_score"] >= 90:
            # Send Slack notification
            slack_webhook = settings.SLACK_WEBHOOK_URL
            message = {
                "text": f"🎯 Excellent match found! {data['job_title']} at {data['company']}"
            }
            # Send webhook...

            # Also create calendar reminder to apply
            calendar = get_calendar_service()
            calendar.create_application_deadline(
                job_title=data["job_title"],
                company=data["company"],
                deadline=datetime.now() + timedelta(days=2)
            )
```

### Custom Follow-up Sequences

Define custom follow-up sequences in `followup_service.py`:

```python
CUSTOM_SEQUENCES = {
    "aggressive_followup": [
        {"days": 2, "type": "post_application", "priority": "high"},
        {"days": 5, "type": "second_followup", "priority": "high"},
        {"days": 10, "type": "final_followup", "priority": "medium"}
    ],
    "passive_followup": [
        {"days": 7, "type": "post_application", "priority": "low"},
        {"days": 21, "type": "final_followup", "priority": "low"}
    ]
}
```

### Custom Recommendation Weights

Adjust recommendation algorithm weights:

```python
# In recommendation_service.py

SCORING_WEIGHTS = {
    "skills_match": 0.35,        # Adjust these
    "behavioral_score": 0.30,     # to tune
    "salary_match": 0.20,         # recommendation
    "location_match": 0.10,       # algorithm
    "company_culture": 0.05
}
```

### Custom WebSocket Events

Add custom event types:

```python
# In websocket_service.py

class EventType(str, Enum):
    # ... existing events ...
    CUSTOM_ALERT = "custom.alert"
    SALARY_THRESHOLD_MET = "salary.threshold_met"

# Emit custom event
await get_ws_manager().emit_event(
    EventType.SALARY_THRESHOLD_MET,
    {"job_id": 42, "salary": 200000},
    channel="jobs"
)
```

---

## Integration Testing

Test integrations with pytest:

```python
# tests/test_integration/test_job_workflow.py

@pytest.mark.asyncio
async def test_complete_job_workflow(db_session):
    """Test complete job processing workflow"""

    # 1. Create job
    job = Job(company="Test Corp", job_title="Engineer", ...)
    db_session.add(job)
    db_session.commit()

    # 2. Trigger integration
    await integrate_job_created(db_session, job.id, auto_process=True)

    # 3. Verify company research cached
    cached_research = cache.get(
        CacheNamespace.COMPANY_RESEARCH,
        f"company:{job.company}"
    )
    assert cached_research is not None

    # 4. Verify skills gap analysis created
    analysis = db_session.query(SkillGapAnalysis).filter(
        SkillGapAnalysis.job_id == job.id
    ).first()
    assert analysis is not None

    # 5. Verify WebSocket event sent (mock)
    # ...
```

---

## Monitoring Integrations

Monitor integration health:

```python
# GET /integrations/health
{
  "status": "healthy",
  "checks": {
    "redis_cache": "connected",
    "websocket": "15 connections",
    "google_calendar": "authenticated",
    "background_tasks": "3 running"
  },
  "integration_stats": {
    "jobs_processed_today": 45,
    "follow_ups_scheduled_today": 32,
    "calendar_events_created_today": 8,
    "websocket_events_sent_today": 287
  }
}
```

---

## Next Steps

- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [WebSocket Guide](./WEBSOCKET_GUIDE.md) - Real-time updates guide
- [Authentication Setup](./AUTHENTICATION.md) - OAuth configuration
