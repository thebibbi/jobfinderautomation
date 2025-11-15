'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

export interface Activity {
  id: number;
  type: 'job_added' | 'application_submitted' | 'interview_scheduled' | 'status_changed' | 'recommendation';
  title: string;
  description: string;
  timestamp: string;
  metadata?: {
    company?: string;
    position?: string;
    status?: string;
    score?: number;
    [key: string]: any;
  };
}

export interface ActivitiesResponse {
  activities: Activity[];
  total: number;
}

/**
 * Hook to fetch recent activities
 */
export function useActivities(limit: number = 10) {
  return useQuery<ActivitiesResponse>({
    queryKey: ['activities', limit],
    queryFn: async () => {
      const response = await apiClient.get('/activities', {
        params: { limit }
      });
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  });
}

/**
 * Hook to fetch activities for a specific job
 */
export function useJobActivities(jobId: number) {
  return useQuery<ActivitiesResponse>({
    queryKey: ['activities', 'job', jobId],
    queryFn: async () => {
      const response = await apiClient.get(`/activities/job/${jobId}`);
      return response.data;
    },
    enabled: !!jobId,
    staleTime: 30000,
  });
}
