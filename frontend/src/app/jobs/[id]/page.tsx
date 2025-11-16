'use client';

import React, { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import JobDetails from '@/components/jobs/JobDetails';
import ApplicationTimeline from '@/components/applications/ApplicationTimeline';
import ScheduleModal from '@/components/interviews/ScheduleModal';
import UpdateStatusModal from '@/components/applications/UpdateStatusModal';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Button from '@/components/common/Button';
import { LoadingPage } from '@/components/common/LoadingSpinner';
import { useToast } from '@/components/common/Toast';
import { useJob, useUpdateJob, useDeleteJob } from '@/hooks/useJobs';
import { useUpdateStatus } from '@/hooks/useApplications';
import { useCreateInterview } from '@/hooks/useInterviews';
import { apiClient } from '@/lib/api';

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = parseInt(params.id as string);
  const { showToast } = useToast();

  const { data: job, isLoading, error } = useJob(jobId);
  const updateJob = useUpdateJob();
  const deleteJob = useDeleteJob();
  const updateStatus = useUpdateStatus();
  const createInterview = useCreateInterview();

  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isGeneratingDocs, setIsGeneratingDocs] = useState(false);

  if (isLoading) {
    return <LoadingPage text="Loading job details..." />;
  }

  if (error || !job) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Failed to load job details. Please try again.</p>
        <Button variant="secondary" onClick={() => router.push('/jobs')} className="mt-4">
          Back to Jobs
        </Button>
      </div>
    );
  }

  const handleApply = async () => {
    try {
      await updateStatus.mutateAsync({
        jobId: job.id,
        status: { status: 'applied' },
      });
      showToast('success', 'Application status updated to Applied');
    } catch (error) {
      showToast('error', 'Failed to update status');
    }
  };

  const handleUpdateStatus = async (newStatus: string, notes?: string) => {
    try {
      await updateStatus.mutateAsync({
        jobId: job.id,
        status: { status: newStatus, notes },
      });
      showToast('success', 'Status updated successfully');
      setIsStatusModalOpen(false);
    } catch (error) {
      showToast('error', 'Failed to update status');
      throw error;
    }
  };

  const handleScheduleInterview = async (data: any) => {
    try {
      await createInterview.mutateAsync(data);
      showToast('success', 'Interview scheduled successfully');
      setIsScheduleModalOpen(false);
    } catch (error) {
      showToast('error', 'Failed to schedule interview');
      throw error;
    }
  };

  const handleAnalyzeJob = async () => {
    setIsAnalyzing(true);
    try {
      const response = await apiClient.post(`/analysis/jobs/${job.id}/analyze`);
      showToast('success', 'Job analysis completed');
      // Refresh job data
      window.location.reload();
    } catch (error: any) {
      showToast('error', error.response?.data?.detail || 'Failed to analyze job');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerateDocuments = async () => {
    setIsGeneratingDocs(true);
    try {
      const response = await apiClient.post(`/documents/jobs/${job.id}/generate`);
      showToast('success', 'Documents generated successfully');

      // Show links to documents if available
      if (response.data.resume_url) {
        showToast('info', 'Resume available in Google Drive');
      }
      if (response.data.cover_letter_url) {
        showToast('info', 'Cover letter available in Google Drive');
      }
    } catch (error: any) {
      showToast('error', error.response?.data?.detail || 'Failed to generate documents');
    } finally {
      setIsGeneratingDocs(false);
    }
  };

  const handleDeleteJob = async () => {
    if (!confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
      return;
    }

    try {
      await deleteJob.mutateAsync(job.id);
      showToast('success', 'Job deleted successfully');
      router.push('/jobs');
    } catch (error) {
      showToast('error', 'Failed to delete job');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => router.push('/jobs')}>
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Jobs
        </Button>

        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => setIsStatusModalOpen(true)}
          >
            Update Status
          </Button>
          <Button
            variant="danger"
            onClick={handleDeleteJob}
            disabled={deleteJob.isPending}
          >
            Delete Job
          </Button>
        </div>
      </div>

      {/* Main Job Details */}
      <JobDetails
        job={job}
        onApply={handleApply}
        onUpdateStatus={(status) => handleUpdateStatus(status)}
      />

      {/* Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* AI Analysis Card */}
        <Card>
          <CardHeader>
            <CardTitle>AI Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                {job.match_score
                  ? 'This job has been analyzed. Re-analyze to get updated insights.'
                  : 'Analyze this job to get AI-powered match scoring and insights.'}
              </p>
              <Button
                variant="primary"
                fullWidth
                onClick={handleAnalyzeJob}
                isLoading={isAnalyzing}
                disabled={isAnalyzing}
              >
                {job.match_score ? 'Re-analyze Job' : 'Analyze Job'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Document Generation Card */}
        <Card>
          <CardHeader>
            <CardTitle>Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Generate a tailored resume and cover letter for this position.
              </p>
              <Button
                variant="primary"
                fullWidth
                onClick={handleGenerateDocuments}
                isLoading={isGeneratingDocs}
                disabled={isGeneratingDocs}
              >
                Generate Documents
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Interview Scheduling Card */}
        <Card>
          <CardHeader>
            <CardTitle>Interviews</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Schedule and track interviews for this position.
              </p>
              <Button
                variant="primary"
                fullWidth
                onClick={() => setIsScheduleModalOpen(true)}
              >
                Schedule Interview
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Application Timeline Card */}
        <Card>
          <CardHeader>
            <CardTitle>Application Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <ApplicationTimeline jobId={job.id} />
          </CardContent>
        </Card>
      </div>

      {/* Modals */}
      <ScheduleModal
        isOpen={isScheduleModalOpen}
        onClose={() => setIsScheduleModalOpen(false)}
        jobId={job.id}
        jobTitle={job.job_title}
        company={job.company}
        onSchedule={handleScheduleInterview}
      />

      <UpdateStatusModal
        isOpen={isStatusModalOpen}
        onClose={() => setIsStatusModalOpen(false)}
        currentStatus={job.status}
        onUpdate={handleUpdateStatus}
      />
    </div>
  );
}
