# Job Application Automation System – Build Guide (for Vibe Coding)

> This document tells the AI *how to build* the system step-by-step: architecture, folders, components, and the order to implement things.
> It is optimized for vibe coding in tools like Windsurf, Cursor, etc.  [oai_citation:0‡Jobautomation.txt](sediment://file_0000000084e471f5982d030fd42f4676)

---

## 1. High-Level Goal

We are building a **one-click job application assistant** that:

- Scrapes/searches for relevant jobs across multiple job boards (LinkedIn, Indeed, Glassdoor, etc.)
- Semantically matches roles against a **predefined candidate profile** and existing “job-match analyzer” skill
- Runs a **deep LLM analysis** on high-potential jobs (Claude)  
- Generates a tailored **resume (DOCX)** and **cover letter (text)** using a building-block approach
- Saves everything in **Google Drive** under a structured folder per job
- Logs jobs + match scores in a **database** (and optionally Google Sheets)
- Sends **email notifications** with results
- Can be triggered:
  - from a **Chrome extension “Analyze Job” button**, and  
  - from a **batch job search/scrape** endpoint  [oai_citation:1‡Jobautomation.txt](sediment://file_0000000084e471f5982d030fd42f4676)

---

## 2. Target Stack

Backend:

- Python 3.11+
- FastAPI (REST API)
- SQLite for early MVP (upgradeable to PostgreSQL)
- Celery + Redis for async/background tasks  [oai_citation:2‡Jobautomation.txt](sediment://file_0000000084e471f5982d030fd42f4676)  

AI / Matching:

- Anthropic Claude API (job analysis & doc generation)
- Sentence Transformers (e.g. `all-MiniLM-L6-v2`) for semantic job–candidate similarity  [oai_citation:3‡JobAutomationPart2.txt](sediment://file_00000000633471f7844cbae5852badc1)  

Integrations:

- Google Drive API (create folders, upload files)
- Gmail API (send notifications)
- Google Sheets API (optional job tracking sheet)
- Selenium-based scrapers (LinkedIn, Indeed, Glassdoor) or future API-based scrapers  [oai_citation:4‡JobAutomationPart2.txt](sediment://file_00000000633471f7844cbae5852badc1)  

Frontend:

- Chrome Extension (Manifest V3)
- Content script + floating button
- Simple popup for basic settings (API URL, min score, auto-generate)  [oai_citation:5‡JobAutomationPart2.txt](sediment://file_00000000633471f7844cbae5852badc1)  

Infra:

- Local dev: `uvicorn`, `redis-server`, Celery worker
- Containerized: Docker + docker-compose (backend + redis + celery worker)  [oai_citation:6‡JobAutomationPart3.txt](sediment://file_000000001fbc71f7bf5a1f442e6ba3ca)
- Optional cloud deploy (Railway/Render)  [oai_citation:7‡JobAutomationPart3.txt](sediment://file_000000001fbc71f7bf5a1f442e6ba3ca)  

---

## 3. Project Structure

Create this structure at the repo root:

```text
job-automation-system/
  backend/
    app/
      main.py
      config.py
      database.py
      api/
        __init__.py
        jobs.py
        analysis.py
        scraping.py
        documents.py
      models/
        __init__.py
        job.py
        document.py
        candidate.py (optional)
        analysis.py
      schemas/
        __init__.py
        job.py
        analysis.py
        document.py
      services/
        __init__.py
        claude_service.py
        job_analyzer.py
        semantic_matcher.py
        document_generator.py
        template_service.py
        scraper_service.py
        google_drive_service.py
        email_service.py
      tasks/
        __init__.py
        celery_app.py
        job_tasks.py
        scraping_tasks.py
      scrapers/
        __init__.py
        base_scraper.py
        linkedin_scraper.py
        indeed_scraper.py
        glassdoor_scraper.py
      prompts/
        __init__.py
        job_analysis.py
        resume_generation.py
        cover_letter.py
      utils/
        __init__.py
        logging.py
        validators.py
        formatters.py
    requirements.txt
    Dockerfile
    tests/
  extension/
    manifest.json
    background.js
    content.js
    styles.css
    popup/
      popup.html
      popup.js
      popup.css
    icons/
  skills/
    job-match-analyzer/
      SKILL.md
      experience_inventory.csv
      skills_taxonomy.csv
      corporate_translation.csv
      achievement_library.csv
    voice_profile.md
  resume_templates/
    paragraphs/
      opening_summaries/
      experience_blocks/
      skills_sections/
      achievements/
    full_templates/
  scripts/
    setup_google_auth.py
    test_claude_connection.py
    migrate_existing_jobs.py
  docs/
    API.md
    DEPLOYMENT.md
    PROMPTS.md
  .env
  .env.example
  docker-compose.yml
  README.md