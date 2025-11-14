# Job Application Automation System - Implementation Complete

## Overview

This system provides end-to-end automation for job search and application processes:

- **Job Discovery**: Scrapes/searches job boards (LinkedIn, Indeed, Glassdoor)
- **Semantic Matching**: AI-powered pre-filtering using sentence transformers
- **Deep Analysis**: Claude AI analyzes job fit using your existing job-match-analyzer skill
- **Document Generation**: Creates tailored resumes and cover letters
- **Google Drive Integration**: Auto-organizes everything in structured folders
- **Email Notifications**: Sends analysis summaries with match scores
- **Chrome Extension**: One-click button on job pages for instant processing

## Project Structure

```
jobfinderautomation/
├── backend/                      # Python FastAPI backend
│   ├── app/
│   │   ├── api/                 # REST API endpoints
│   │   ├── models/              # Database models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   ├── tasks/               # Celery async tasks
│   │   ├── scrapers/            # Job board scrapers
│   │   ├── prompts/             # Claude AI prompts
│   │   └── utils/               # Utility functions
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile              # Container definition
├── extension/                   # Chrome extension
│   ├── manifest.json
│   ├── content.js              # Job data extraction
│   ├── background.js           # Service worker
│   ├── styles.css
│   └── popup/                  # Settings popup
├── skills/                      # Job-match-analyzer skill
│   └── job-match-analyzer/
│       ├── SKILL.md
│       ├── experience_inventory.csv
│       ├── skills_taxonomy.csv
│       ├── corporate_translation.csv
│       └── achievement_library.csv
├── resume_templates/            # Resume building blocks
├── scripts/                     # Setup and utility scripts
├── docker-compose.yml          # Multi-service deployment
└── .env                        # Configuration (create from .env.example)
```

## Setup Instructions

### 1. Prerequisites

- Python 3.11+
- Redis (for task queue)
- Google Cloud account (free tier)
- Anthropic Claude API key
- Chrome browser (for extension)

### 2. Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your API keys:
   - `ANTHROPIC_API_KEY`: Get from https://console.anthropic.com/
   - `GOOGLE_CREDENTIALS_PATH`: Path to your service account JSON
   - `GOOGLE_DRIVE_FOLDER_ID`: Create a folder in Drive for jobs
   - `NOTIFICATION_EMAIL`: Email to receive notifications
   - Other settings as needed

### 3. Google Cloud Setup

1. Create a new project at https://console.cloud.google.com/
2. Enable these APIs:
   - Google Drive API
   - Gmail API
   - Google Sheets API (optional)
3. Create OAuth 2.0 credentials:
   - Application type: Desktop app
   - Download as `oauth-credentials.json` in `credentials/` folder
4. Run the auth setup script:
   ```bash
   python scripts/setup_google_auth.py
   ```

### 4. Populate Your Skills Data

Edit the CSV files in `skills/job-match-analyzer/` with your actual data:
- `experience_inventory.csv`: Your work history and achievements
- `skills_taxonomy.csv`: Your technical and soft skills
- `corporate_translation.csv`: Education-to-corporate terminology
- `achievement_library.csv`: Quantified achievements

Also update `skills/voice_profile.md` with actual writing samples.

### 5. Install Dependencies

**Option A: Docker (Recommended)**
```bash
docker-compose up --build
```

**Option B: Local Development**
```bash
# Backend
cd backend
pip install -r requirements.txt

# Start Redis (in separate terminal)
redis-server

# Start FastAPI (in separate terminal)
uvicorn app.main:app --reload

# Start Celery worker (in separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info
```

### 6. Initialize Database

```bash
cd backend
python -c "from app.database import init_db; init_db()"
```

### 7. Install Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked"
4. Select the `extension/` folder
5. The extension should now appear in your browser

### 8. Configure Extension

1. Click the extension icon in Chrome
2. Set API URL (default: `http://localhost:8000`)
3. Set minimum match score (default: 70)
4. Save settings

## Usage

### One-Click Job Processing

1. Navigate to a job posting on LinkedIn, Indeed, or Glassdoor
2. Wait for the "Analyze Job" button to appear (bottom-right corner)
3. Click the button
4. Wait for processing (2-3 minutes)
5. Check your email for the analysis notification
6. Review documents in Google Drive

### Manual Job Analysis via API

```bash
curl -X POST http://localhost:8000/api/v1/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Example Corp",
    "job_title": "Business Analyst",
    "job_description": "Full job description here...",
    "job_url": "https://example.com/job/123",
    "source": "manual"
  }'
```

### Batch Job Scraping

```bash
curl -X POST http://localhost:8000/api/v1/scraping/search \
  -H "Content-Type: application/json" \
  -d '{
    "job_titles": ["Business Analyst", "Operations Manager"],
    "locations": ["Remote"],
    "sources": ["linkedin", "indeed"],
    "max_per_source": 25,
    "min_semantic_score": 40.0,
    "auto_analyze": true
  }'
```

## API Endpoints

- `GET /`: Health check
- `POST /api/v1/jobs/`: Create job entry
- `GET /api/v1/jobs/`: List all jobs
- `GET /api/v1/jobs/{job_id}`: Get specific job
- `POST /api/v1/jobs/process`: Process job from extension
- `POST /api/v1/analysis/{job_id}`: Analyze job fit
- `GET /api/v1/documents/job/{job_id}`: Get job documents
- `POST /api/v1/scraping/search`: Search and scrape jobs

## Workflow

1. **Job Discovery**: Extension extracts job data OR scraper finds jobs
2. **Semantic Filter**: Pre-filters using sentence transformers (40%+ similarity)
3. **Deep Analysis**: Claude analyzes using job-match-analyzer skill
4. **Scoring**: Generates 0-100 match score with detailed feedback
5. **Document Generation**: If score ≥ 70%, generates resume + 2 cover letters
6. **Google Drive**: Creates folder, uploads all documents
7. **Email**: Sends notification with results and Drive link

## Cost Estimates

- **Claude API**: ~$1-2 per job analysis (with document generation)
- **Google Cloud**: Free tier covers most usage
- **Hosting**: $0 (local) to $10/month (cloud via Railway/Render)

**Monthly estimate** (50 jobs analyzed): $50-100 in Claude API calls

## Troubleshooting

**Extension not appearing on job pages:**
- Check you're on a supported job board (LinkedIn, Indeed, Glassdoor)
- Refresh the page after installing extension
- Check browser console for errors

**"API error" in extension:**
- Ensure backend is running (`docker-compose up` or local servers)
- Check API URL in extension settings matches backend
- Verify CORS is enabled in backend

**No documents generated:**
- Check match score - documents only for scores ≥ 70%
- Verify Claude API key is valid
- Check Celery worker logs for errors

**Email not sending:**
- Verify Gmail API is enabled
- Run `python scripts/setup_google_auth.py` again
- Check `credentials/token.json` exists and is valid

**Database errors:**
- Run: `python -c "from backend.app.database import init_db; init_db()"`
- Delete `job_automation.db` and reinitialize if corrupted

## Development

### Running Tests

```bash
cd backend
pytest
```

### Code Quality

```bash
# Format code
black backend/app/

# Lint
flake8 backend/app/

# Type checking
mypy backend/app/
```

### Adding New Scrapers

1. Create new scraper in `backend/app/scrapers/`
2. Inherit from `BaseScraper`
3. Implement `search_jobs()` and `extract_job_details()`
4. Register in `ScraperService._scrape_source()`

## Deployment

### Docker Deployment

```bash
docker-compose up -d
```

### Cloud Deployment (Railway)

1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Create project: `railway init`
4. Add Redis: `railway add -d redis`
5. Deploy: `railway up`
6. Set environment variables in Railway dashboard

## Next Steps

1. **Populate your skills data** with real information
2. **Test with a few jobs** manually before batch processing
3. **Refine prompts** based on output quality
4. **Add resume building blocks** from your existing resumes
5. **Implement proper scrapers** for production use (current ones are placeholders)

## Support

For issues or questions:
- Check logs: Docker logs or terminal outputs
- Review `.env` configuration
- Verify all API keys are valid
- Check Google Cloud API quotas

## License

Private use only - configured for personal job search automation.
