from celery import shared_task
from loguru import logger
from datetime import datetime

from .celery_app import celery_app
from ..database import SessionLocal
from ..models.job import Job
from ..models.document import Document, DocumentType
from ..services.job_analyzer import get_job_analyzer
from ..services.document_generator import get_document_generator
from ..services.google_drive_service import get_drive_service
from ..services.email_service import get_email_service
from ..config import settings


@celery_app.task(name='process_job_complete_workflow')
def process_job_complete_workflow(job_id: int):
    """
    Complete workflow for processing a job:
    1. Analyze job fit
    2. If score >= threshold, generate documents
    3. Upload to Google Drive
    4. Send email notification
    """
    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"❌ Job {job_id} not found")
            return

        logger.info(f"🚀 Starting complete workflow for job {job_id}: {job.company} - {job.job_title}")

        # Step 1: Analyze job
        logger.info("📊 Step 1: Analyzing job fit...")
        analyzer = get_job_analyzer()
        # Note: analyze_job is async, need to run in sync context
        import asyncio
        analysis_result = asyncio.run(analyzer.analyze_job(job_id))

        match_score = analysis_result['match_score']
        analysis_data = analysis_result['analysis']

        logger.info(f"✅ Analysis complete. Match score: {match_score}%")

        # Step 2: Create Google Drive folder
        logger.info("📁 Step 2: Creating Google Drive folder...")
        drive_service = get_drive_service()
        folder_info = drive_service.create_job_folder(
            company=job.company,
            job_title=job.job_title
        )

        # Update job with folder info
        job.drive_folder_id = folder_info['folder_id']
        job.drive_folder_url = folder_info['folder_url']
        db.commit()

        logger.info(f"✅ Folder created: {folder_info['folder_url']}")

        # Step 3: Upload JD to Drive
        logger.info("📄 Step 3: Uploading job description...")
        jd_file = drive_service.upload_job_description(
            jd_content=job.job_description,
            folder_id=folder_info['folder_id'],
            company=job.company,
            job_title=job.job_title
        )

        # Save JD document record
        jd_doc = Document(
            job_id=job.id,
            document_type=DocumentType.JOB_DESCRIPTION,
            title=f"{job.company} - {job.job_title} - JD",
            content=job.job_description,
            drive_file_id=jd_file['file_id'],
            drive_file_url=jd_file['file_url']
        )
        db.add(jd_doc)
        db.commit()

        # Step 4: Generate documents if score is high enough
        if match_score >= settings.MIN_MATCH_SCORE:
            logger.info(f"📝 Step 4: Generating documents (score {match_score}% >= {settings.MIN_MATCH_SCORE}%)...")

            doc_generator = get_document_generator()

            # Generate resume
            logger.info("   📄 Generating resume...")
            resume_bytes = asyncio.run(doc_generator.generate_resume(
                job_data={
                    'company': job.company,
                    'job_title': job.job_title,
                    'job_description': job.job_description
                },
                analysis_results=analysis_data
            ))

            # Upload resume
            resume_file = drive_service.upload_resume(
                resume_content=resume_bytes,
                folder_id=folder_info['folder_id'],
                filename=f"{job.company} - Resume.docx"
            )

            resume_doc = Document(
                job_id=job.id,
                document_type=DocumentType.RESUME,
                title=f"{job.company} - Resume",
                content="",  # Binary content
                drive_file_id=resume_file['file_id'],
                drive_file_url=resume_file['file_url']
            )
            db.add(resume_doc)

            # Generate conversational cover letter
            logger.info("   📝 Generating conversational cover letter...")
            cover_letter_conv = asyncio.run(doc_generator.generate_cover_letter(
                job_data={
                    'company': job.company,
                    'job_title': job.job_title,
                    'job_description': job.job_description
                },
                analysis_results=analysis_data,
                style="conversational"
            ))

            cl_conv_file = drive_service.upload_cover_letter(
                content=cover_letter_conv,
                folder_id=folder_info['folder_id'],
                letter_type="conversational"
            )

            cl_conv_doc = Document(
                job_id=job.id,
                document_type=DocumentType.COVER_LETTER_CONVERSATIONAL,
                title="Cover Letter - Conversational",
                content=cover_letter_conv,
                drive_file_id=cl_conv_file['file_id'],
                drive_file_url=cl_conv_file['file_url']
            )
            db.add(cl_conv_doc)

            # Generate formal cover letter
            logger.info("   📝 Generating formal cover letter...")
            cover_letter_formal = asyncio.run(doc_generator.generate_cover_letter(
                job_data={
                    'company': job.company,
                    'job_title': job.job_title,
                    'job_description': job.job_description
                },
                analysis_results=analysis_data,
                style="formal"
            ))

            cl_formal_file = drive_service.upload_cover_letter(
                content=cover_letter_formal,
                folder_id=folder_info['folder_id'],
                letter_type="formal"
            )

            cl_formal_doc = Document(
                job_id=job.id,
                document_type=DocumentType.COVER_LETTER_FORMAL,
                title="Cover Letter - Formal",
                content=cover_letter_formal,
                drive_file_id=cl_formal_file['file_id'],
                drive_file_url=cl_formal_file['file_url']
            )
            db.add(cl_formal_doc)

            job.status = "documents_generated"
            logger.info("✅ All documents generated and uploaded")
        else:
            logger.info(f"⏭️  Skipping document generation (score {match_score}% < {settings.MIN_MATCH_SCORE}%)")
            job.status = "analyzed_low_score"

        db.commit()

        # Step 5: Send email notification
        logger.info("📧 Step 5: Sending email notification...")
        email_service = get_email_service()
        email_service.send_job_analysis_notification(
            job_data={
                'company': job.company,
                'job_title': job.job_title,
                'job_url': job.job_url
            },
            analysis_results=analysis_data,
            drive_folder_url=folder_info['folder_url']
        )

        logger.info(f"🎉 Complete workflow finished for job {job_id}")

        return {
            'job_id': job_id,
            'match_score': match_score,
            'drive_url': folder_info['folder_url'],
            'status': job.status
        }

    except Exception as e:
        logger.error(f"❌ Error in complete workflow for job {job_id}: {e}")
        if job:
            job.status = "error"
            db.commit()
        raise
    finally:
        db.close()


@celery_app.task(name='analyze_job_task')
def analyze_job_task(job_id: int):
    """Simple task to just analyze a job"""
    import asyncio
    analyzer = get_job_analyzer()
    return asyncio.run(analyzer.analyze_job(job_id))


@celery_app.task(name='scrape_jobs_task')
def scrape_jobs_task(
    job_titles: list,
    locations: list = None,
    sources: list = None,
    max_per_source: int = 20
):
    """
    Background task to scrape jobs from various platforms
    
    Args:
        job_titles: List of job titles to search for
        locations: List of locations to search in
        sources: List of platforms to scrape (linkedin, indeed, etc.)
        max_per_source: Maximum number of jobs to scrape per source
    """
    db = SessionLocal()
    
    try:
        from ..services.scraper_service import get_scraper_service
        
        logger.info(f"🔍 Starting job scraping task...")
        logger.info(f"   Job titles: {job_titles}")
        logger.info(f"   Locations: {locations or ['Any']}")
        logger.info(f"   Sources: {sources or ['linkedin', 'indeed']}")
        logger.info(f"   Max per source: {max_per_source}")
        
        scraper = get_scraper_service()
        
        # Scrape jobs
        jobs = scraper.scrape_jobs(
            job_titles=job_titles,
            locations=locations or [],
            sources=sources or ['linkedin', 'indeed'],
            max_per_source=max_per_source,
            min_semantic_score=40.0
        )
        
        logger.info(f"✅ Scraped {len(jobs)} jobs")
        
        # Save to database
        created_ids = scraper.save_scraped_jobs(jobs)
        
        logger.info(f"✅ Saved {len(created_ids)} new jobs to database")
        
        # Optionally trigger analysis for high-scoring jobs
        for job_id in created_ids[:5]:  # Analyze top 5 jobs
            analyze_job_task.delay(job_id)
        
        return {
            'success': True,
            'total_scraped': len(jobs),
            'saved_to_database': len(created_ids),
            'job_ids': created_ids
        }
        
    except Exception as e:
        logger.error(f"❌ Error in scrape_jobs_task: {e}")
        raise
    finally:
        db.close()
