// Content script that runs on job posting pages

class JobExtractor {
  constructor() {
    this.currentSite = this.detectSite();
    this.button = null;
  }

  detectSite() {
    const hostname = window.location.hostname;
    if (hostname.includes('linkedin.com')) return 'linkedin';
    if (hostname.includes('indeed.com')) return 'indeed';
    if (hostname.includes('glassdoor.com')) return 'glassdoor';
    return 'unknown';
  }

  // Extract job data based on site
  extractJobData() {
    if (this.currentSite === 'linkedin') {
      return this.extractLinkedIn();
    } else if (this.currentSite === 'indeed') {
      return this.extractIndeed();
    } else if (this.currentSite === 'glassdoor') {
      return this.extractGlassdoor();
    }
    return null;
  }

  extractLinkedIn() {
    try {
      const jobTitle = document.querySelector('h1.top-card-layout__title')?.textContent.trim();
      const company = document.querySelector('a.topcard__org-name-link')?.textContent.trim();
      const location = document.querySelector('span.topcard__flavor--bullet')?.textContent.trim();

      // Get full job description
      const descElement = document.querySelector('div.show-more-less-html__markup');
      const jobDescription = descElement?.innerText.trim();

      // Get job URL
      const jobUrl = window.location.href.split('?')[0];

      // Try to get salary
      let salary = null;
      const salaryElement = document.querySelector('span.compensation__salary');
      if (salaryElement) {
        salary = salaryElement.textContent.trim();
      }

      return {
        jobTitle,
        company,
        location,
        jobDescription,
        jobUrl,
        salary,
        source: 'linkedin'
      };
    } catch (error) {
      console.error('Error extracting LinkedIn data:', error);
      return null;
    }
  }

  extractIndeed() {
    try {
      const jobTitle = document.querySelector('h1.jobsearch-JobInfoHeader-title')?.textContent.trim();
      const company = document.querySelector('div[data-company-name="true"]')?.textContent.trim();
      const location = document.querySelector('div[data-testid="inlineHeader-companyLocation"]')?.textContent.trim();

      const descElement = document.querySelector('div#jobDescriptionText');
      const jobDescription = descElement?.innerText.trim();

      const jobUrl = window.location.href.split('?')[0];

      let salary = null;
      const salaryElement = document.querySelector('div.salary-snippet');
      if (salaryElement) {
        salary = salaryElement.textContent.trim();
      }

      return {
        jobTitle,
        company,
        location,
        jobDescription,
        jobUrl,
        salary,
        source: 'indeed'
      };
    } catch (error) {
      console.error('Error extracting Indeed data:', error);
      return null;
    }
  }

  extractGlassdoor() {
    try {
      const jobTitle = document.querySelector('div[data-test="job-title"]')?.textContent.trim();
      const company = document.querySelector('div[data-test="employer-name"]')?.textContent.trim();
      const location = document.querySelector('div[data-test="location"]')?.textContent.trim();

      const descElement = document.querySelector('div[data-test="job-description"]');
      const jobDescription = descElement?.innerText.trim();

      const jobUrl = window.location.href.split('?')[0];

      let salary = null;
      const salaryElement = document.querySelector('div[data-test="salary-estimate"]');
      if (salaryElement) {
        salary = salaryElement.textContent.trim();
      }

      return {
        jobTitle,
        company,
        location,
        jobDescription,
        jobUrl,
        salary,
        source: 'glassdoor'
      };
    } catch (error) {
      console.error('Error extracting Glassdoor data:', error);
      return null;
    }
  }

  // Create floating button
  createButton() {
    if (this.button) return;

    this.button = document.createElement('button');
    this.button.id = 'job-automation-button';
    this.button.innerHTML = `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M9 11l3 3L22 4"></path>
        <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"></path>
      </svg>
      <span>Analyze Job</span>
    `;

    this.button.addEventListener('click', () => this.handleButtonClick());

    document.body.appendChild(this.button);
  }

  async handleButtonClick() {
    this.setButtonState('loading', 'Analyzing...');

    try {
      // Extract job data
      const jobData = this.extractJobData();

      if (!jobData || !jobData.jobDescription) {
        throw new Error('Could not extract job data from page');
      }

      // Get API URL from storage
      const { apiUrl } = await browser.storage.sync.get(['apiUrl']);
      const baseUrl = apiUrl || 'http://localhost:8000';

      // Send to backend
      const response = await fetch(`${baseUrl}/api/v1/jobs/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(jobData)
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const result = await response.json();

      // Show success
      this.setButtonState('success', `Score: ${result.matchScore}%`);

      // Send notification
      browser.runtime.sendMessage({
        type: 'JOB_PROCESSED',
        data: result
      });

      // Reset button after 3 seconds
      setTimeout(() => {
        this.setButtonState('default', 'Analyze Job');
      }, 3000);

    } catch (error) {
      console.error('Error processing job:', error);
      this.setButtonState('error', 'Error!');

      setTimeout(() => {
        this.setButtonState('default', 'Analyze Job');
      }, 3000);
    }
  }

  setButtonState(state, text) {
    this.button.className = `job-automation-btn job-automation-btn--${state}`;
    this.button.querySelector('span').textContent = text;
    this.button.disabled = state === 'loading';
  }
}

// Initialize when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

function init() {
  const extractor = new JobExtractor();
  // Wait a bit for dynamic content to load
  setTimeout(() => {
    extractor.createButton();
  }, 2000);
}
