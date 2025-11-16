'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import StatusBadge from './StatusBadge';
import { formatDate } from '@/lib/utils';
import { apiClient } from '@/lib/api';
import { LoadingPage } from '@/components/common/LoadingSpinner';

interface TimelineEvent {
  id: number;
  event_type: string;
  old_status?: string;
  new_status?: string;
  notes?: string;
  created_at: string;
  metadata?: Record<string, any>;
}

interface ApplicationTimelineProps {
  jobId: number;
}

export default function ApplicationTimeline({ jobId }: ApplicationTimelineProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTimeline = async () => {
      try {
        const response = await apiClient.get(`/applications/${jobId}/timeline`);
        setEvents(response.data.events || []);
      } catch (error) {
        console.error('Failed to fetch timeline:', error);
        setEvents([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTimeline();
  }, [jobId]);

  if (loading) {
    return <LoadingPage />;
  }

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'status_change':
        return (
          <div className="bg-blue-100 rounded-full p-2">
            <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M8 5a1 1 0 100 2h5.586l-1.293 1.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L13.586 5H8zM12 15a1 1 0 100-2H6.414l1.293-1.293a1 1 0 10-1.414-1.414l-3 3a1 1 0 000 1.414l3 3a1 1 0 001.414-1.414L6.414 15H12z" />
            </svg>
          </div>
        );
      case 'note_added':
        return (
          <div className="bg-yellow-100 rounded-full p-2">
            <svg className="w-4 h-4 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
            </svg>
          </div>
        );
      case 'interview_scheduled':
        return (
          <div className="bg-purple-100 rounded-full p-2">
            <svg className="w-4 h-4 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
            </svg>
          </div>
        );
      case 'document_uploaded':
        return (
          <div className="bg-green-100 rounded-full p-2">
            <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="bg-gray-100 rounded-full p-2">
            <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
          </div>
        );
    }
  };

  const getEventTitle = (event: TimelineEvent) => {
    switch (event.event_type) {
      case 'status_change':
        return 'Status Changed';
      case 'note_added':
        return 'Note Added';
      case 'interview_scheduled':
        return 'Interview Scheduled';
      case 'document_uploaded':
        return 'Document Uploaded';
      default:
        return event.event_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flow-root">
          <ul className="-mb-8">
            {events.map((event, index) => (
              <li key={event.id}>
                <div className="relative pb-8">
                  {index !== events.length - 1 && (
                    <span
                      className="absolute top-5 left-5 -ml-px h-full w-0.5 bg-gray-200"
                      aria-hidden="true"
                    />
                  )}
                  <div className="relative flex items-start space-x-3">
                    <div className="relative">
                      {getEventIcon(event.event_type)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {getEventTitle(event)}
                        </p>
                        <p className="mt-0.5 text-xs text-gray-500">
                          {formatDate(event.created_at)}
                        </p>
                      </div>

                      {event.event_type === 'status_change' && event.old_status && event.new_status && (
                        <div className="mt-2 flex items-center gap-2">
                          <StatusBadge status={event.old_status} size="sm" />
                          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                          </svg>
                          <StatusBadge status={event.new_status} size="sm" />
                        </div>
                      )}

                      {event.notes && (
                        <div className="mt-2 text-sm text-gray-600 bg-gray-50 rounded p-2">
                          {event.notes}
                        </div>
                      )}

                      {event.metadata && Object.keys(event.metadata).length > 0 && (
                        <div className="mt-2 text-xs text-gray-500">
                          {Object.entries(event.metadata).map(([key, value]) => (
                            <div key={key}>
                              <span className="font-medium">{key}:</span> {String(value)}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {events.length === 0 && (
          <div className="text-center py-12">
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
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-500">No timeline events yet</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
