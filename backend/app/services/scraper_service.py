from typing import List, Dict, Any
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..scrapers.linkedin_scraper import LinkedInScraper
from ..scrapers.indeed_scraper import IndeedScraper
from .semantic_matcher import get_semantic_matcher
from ..models.job import Job
from ..database import SessionLocal


class ScraperService:
    """Orchestrates job scraping across multiple platforms"""

    def __init__(self):
        self.semantic_matcher = get_semantic_matcher()

    def scrape_jobs(
        self,
        job_titles: List[str],
        locations: List[str] = ["Remote"],
        sources: List[str] = ["linkedin", "indeed"],
        max_per_source: int = 25,
        min_semantic_score: float = 40.0
    ) -> List[Dict[str, Any]]:
        """
        Scrape jobs from multiple sources

        Args:
            job_titles: List of job titles to search for
            locations: List of locations
            sources: Which job boards to scrape
            max_per_source: Max results per source
            min_semantic_score: Minimum semantic similarity score

        Returns:
            List of job dictionaries
        """
        all_jobs = []

        with ThreadPoolExecutor(max_workers=len(sources)) as executor:
            futures = []

            # Submit scraping tasks
            for source in sources:
                future = executor.submit(
                    self._scrape_source,
                    source,
                    job_titles,
                    locations,
                    max_per_source
                )
                futures.append(future)

            # Collect results
            for future in as_completed(futures):
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                except Exception as e:
                    logger.error(f"❌ Error in scraping task: {e}")

        logger.info(f"📊 Total jobs scraped: {len(all_jobs)}")

        # Remove duplicates based on job_url
        unique_jobs = {job['job_url']: job for job in all_jobs}.values()
        logger.info(f"📊 Unique jobs after deduplication: {len(unique_jobs)}")

        # Semantic filtering
        logger.info("🔍 Performing semantic matching...")
        ranked_jobs = self.semantic_matcher.rank_jobs(
            list(unique_jobs),
            min_score=min_semantic_score
        )

        # Add semantic scores
        filtered_jobs = []
        for job, score in ranked_jobs:
            job['semantic_score'] = score
            filtered_jobs.append(job)

        logger.info(f"✅ {len(filtered_jobs)} jobs passed semantic filter (min score: {min_semantic_score})")

        return filtered_jobs

    def _scrape_source(
        self,
        source: str,
        job_titles: List[str],
        locations: List[str],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Scrape from a single source"""
        try:
            if source == "linkedin":
                with LinkedInScraper(headless=True) as scraper:
                    jobs = scraper.search_jobs(
                        keywords=job_titles,
                        location=locations[0],
                        max_results=max_results
                    )
                    return jobs

            elif source == "indeed":
                with IndeedScraper(headless=True) as scraper:
                    jobs = scraper.search_jobs(
                        keywords=job_titles,
                        location=locations[0],
                        max_results=max_results
                    )
                    return jobs

            else:
                logger.warning(f"⚠️ Unknown source: {source}")
                return []

        except Exception as e:
            logger.error(f"❌ Error scraping {source}: {e}")
            return []

    def save_scraped_jobs(self, jobs: List[Dict[str, Any]]) -> List[int]:
        """
        Save scraped jobs to database

        Returns:
            List of created job IDs
        """
        db = SessionLocal()
        created_ids = []

        try:
            for job_data in jobs:
                # Check if job already exists
                existing = db.query(Job).filter(
                    Job.job_url == job_data['job_url']
                ).first()

                if existing:
                    logger.debug(f"⏭️  Job already exists: {job_data['job_title']}")
                    continue

                # Create new job
                job = Job(
                    job_id=job_data.get('job_id', ''),
                    company=job_data['company'],
                    job_title=job_data['job_title'],
                    job_description=job_data.get('job_description', ''),
                    job_url=job_data['job_url'],
                    location=job_data.get('location', ''),
                    source=job_data['source'],
                    remote_type=job_data.get('remote_type', 'unknown'),
                    status='discovered'
                )

                db.add(job)
                db.flush()
                created_ids.append(job.id)

                logger.info(f"✅ Saved job: {job.company} - {job.job_title}")

            db.commit()
            logger.info(f"✅ Saved {len(created_ids)} new jobs to database")

        except Exception as e:
            logger.error(f"❌ Error saving jobs: {e}")
            db.rollback()
            raise
        finally:
            db.close()

        return created_ids


# Singleton
_scraper_service = None

def get_scraper_service() -> ScraperService:
    global _scraper_service
    if _scraper_service is None:
        _scraper_service = ScraperService()
    return _scraper_service
