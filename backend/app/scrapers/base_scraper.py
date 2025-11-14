from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time


class BaseScraper(ABC):
    """Base class for job board scrapers"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        """Initialize Selenium WebDriver"""
        if self.driver is not None:
            return

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("✅ WebDriver initialized")

    def _close_driver(self):
        """Close WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("✅ WebDriver closed")

    def _wait_for_element(
        self,
        by: By,
        value: str,
        timeout: int = 10
    ):
        """Wait for element to be present"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def _safe_find_element(
        self,
        element,
        by: By,
        value: str,
        default: str = ""
    ) -> str:
        """Safely find element and return text"""
        try:
            found = element.find_element(by, value)
            return found.text.strip()
        except:
            return default

    @abstractmethod
    def search_jobs(
        self,
        keywords: List[str],
        location: str = "Remote",
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs on the platform

        Returns:
            List of job dictionaries with keys:
            - job_title
            - company
            - location
            - job_url
            - job_description
            - salary (optional)
            - source
        """
        pass

    @abstractmethod
    def extract_job_details(self, job_url: str) -> Dict[str, Any]:
        """Extract full job details from job page"""
        pass

    def __enter__(self):
        """Context manager entry"""
        self._init_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self._close_driver()
