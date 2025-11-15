'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import JobCard from '@/components/jobs/JobCard';
import JobFilters from '@/components/jobs/JobFilters';
import AddJobModal from '@/components/jobs/AddJobModal';
import ScrapeJobsModal from '@/components/jobs/ScrapeJobsModal';
import Button from '@/components/common/Button';
import { LoadingPage } from '@/components/common/LoadingSpinner';
import { useJobs, useCreateJob } from '@/hooks/useJobs';
import { useToast } from '@/components/common/Toast';
import { scrapingApi } from '@/lib/api';
import { JobFilters as JobFiltersType } from '@/types/job';

export default function JobsPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<JobFiltersType>({});
  const [isAddJobModalOpen, setIsAddJobModalOpen] = useState(false);
  const [isScrapeModalOpen, setIsScrapeModalOpen] = useState(false);
  const { data: jobs, isLoading, error } = useJobs(filters);
  const createJob = useCreateJob();
  const { showToast } = useToast();

  const handleAddJob = async (data: any) => {
    try {
      const response = await createJob.mutateAsync(data);
      showToast('success', 'Job added successfully');
      setIsAddJobModalOpen(false);
      // Navigate to the new job
      if (response.data?.id) {
        router.push(`/jobs/${response.data.id}`);
      }
    } catch (error) {
      showToast('error', 'Failed to add job');
      throw error;
    }
  };

  const handleScrapeJobs = async (data: any) => {
    try {
      const response = await scrapingApi.trigger(data);
      showToast('success', 'Scraping job started! You\'ll be notified when it completes.');
      setIsScrapeModalOpen(false);

      // Optionally, you could poll for results or use websockets
      if (response.data?.task_id) {
        showToast('info', `Task ID: ${response.data.task_id}`);
      }
    } catch (error: any) {
      showToast('error', error.response?.data?.detail || 'Failed to start scraping');
      throw error;
    }
  };

  if (isLoading) {
    return <LoadingPage text="Loading jobs..." />;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Failed to load jobs. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Jobs</h1>
          <p className="mt-2 text-gray-600">
            {jobs?.length || 0} job{jobs?.length !== 1 ? 's' : ''} found
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={() => setIsScrapeModalOpen(true)}>
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Scrape Jobs
          </Button>
          <Button variant="primary" onClick={() => setIsAddJobModalOpen(true)}>
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Job
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1">
          <JobFilters filters={filters} onFiltersChange={setFilters} />
        </div>

        {/* Jobs Grid */}
        <div className="lg:col-span-3">
          {jobs && jobs.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {jobs.map((job) => (
                <JobCard key={job.id} job={job} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No jobs found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by adding a new job or adjusting your filters.
              </p>
              <div className="mt-6">
                <Button variant="primary" onClick={() => setIsAddJobModalOpen(true)}>
                  Add your first job
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <AddJobModal
        isOpen={isAddJobModalOpen}
        onClose={() => setIsAddJobModalOpen(false)}
        onAdd={handleAddJob}
      />
      <ScrapeJobsModal
        isOpen={isScrapeModalOpen}
        onClose={() => setIsScrapeModalOpen(false)}
        onScrape={handleScrapeJobs}
      />
    </div>
  );
}
