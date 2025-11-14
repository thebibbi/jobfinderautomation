'use client';

import React, { useState } from 'react';
import InterviewCard from '@/components/interviews/InterviewCard';
import ScheduleModal from '@/components/interviews/ScheduleModal';
import Button from '@/components/common/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { LoadingPage } from '@/components/common/LoadingSpinner';
import { useUpcomingInterviews, useDueFollowUps, useCreateInterview } from '@/hooks/useInterviews';
import { formatDate } from '@/lib/utils';

export default function InterviewsPage() {
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const { data: interviews, isLoading: interviewsLoading } = useUpcomingInterviews(30);
  const { data: followUps, isLoading: followUpsLoading } = useDueFollowUps(72);
  const createInterview = useCreateInterview();

  if (interviewsLoading || followUpsLoading) {
    return <LoadingPage text="Loading interviews..." />;
  }

  const handleScheduleInterview = async (data: any) => {
    await createInterview.mutateAsync(data);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Interviews & Follow-ups</h1>
          <p className="mt-2 text-gray-600">
            Manage your upcoming interviews and follow-up actions
          </p>
        </div>
        <Button variant="primary" onClick={() => setIsScheduleModalOpen(true)}>
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Schedule Interview
        </Button>
      </div>

      {/* Follow-ups Section */}
      {followUps && followUps.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              Pending Follow-ups ({followUps.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {followUps.map((followUp: any) => (
                <div
                  key={followUp.id}
                  className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg"
                >
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{followUp.follow_up_type}</p>
                    <p className="text-sm text-gray-600 mt-1">
                      {followUp.company} - {followUp.job_title}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Due: {formatDate(followUp.due_date)}
                    </p>
                  </div>
                  <Button size="sm" variant="primary">
                    Complete
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upcoming Interviews */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Upcoming Interviews ({interviews?.length || 0})
        </h2>
        {interviews && interviews.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {interviews.map((interview: any) => (
              <InterviewCard key={interview.id} interview={interview} />
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
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No upcoming interviews</h3>
            <p className="mt-1 text-sm text-gray-500">
              Schedule an interview to get started.
            </p>
          </div>
        )}
      </div>

      {/* Schedule Interview Modal */}
      <ScheduleModal
        isOpen={isScheduleModalOpen}
        onClose={() => setIsScheduleModalOpen(false)}
        jobId={0}
        jobTitle="Select a job"
        company=""
        onSchedule={handleScheduleInterview}
      />
    </div>
  );
}
