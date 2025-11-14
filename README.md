# Job Application Automation System

Automated end-to-end job search and application system powered by Claude AI.

## Features

- 🔍 **Job Discovery**: Scrape and search across LinkedIn, Indeed, Glassdoor
- 🤖 **AI Analysis**: Claude-powered job matching using your career profile
- 📄 **Auto-Documentation**: Generate tailored resumes and cover letters
- 📁 **Smart Organization**: Auto-organize in Google Drive
- 📧 **Notifications**: Email alerts with match scores and documents
- ⚡ **One-Click**: Chrome extension for instant job processing

## Quick Start

1. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start Services**:
   ```bash
   docker-compose up
   ```

3. **Install Extension**:
   - Open Chrome → Extensions → Load unpacked
   - Select the `extension/` folder

4. **Process Jobs**:
   - Navigate to any job posting
   - Click "Analyze Job" button
   - Receive email with results!

## Documentation

- **[Implementation Guide](README_IMPLEMENTATION.md)** - Complete setup and usage
- **[Build Guide](JOB_AUTOMATION_BUILD_GUIDE.md)** - Architecture and design
- **[API Reference](docs/API.md)** - API endpoints (coming soon)

## Tech Stack

- **Backend**: Python, FastAPI, SQLite, Celery, Redis
- **AI**: Anthropic Claude, Sentence Transformers
- **Integrations**: Google Drive, Gmail, Sheets
- **Frontend**: Chrome Extension (Manifest V3)

## Requirements

- Python 3.11+
- Redis
- Anthropic Claude API key
- Google Cloud account (free tier)

## Status

✅ Core system implemented and ready for use
⚠️ Job scrapers are placeholders - implement proper scraping logic for production

See [README_IMPLEMENTATION.md](README_IMPLEMENTATION.md) for detailed setup instructions.
