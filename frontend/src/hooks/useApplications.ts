'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { applicationsApi } from '@/lib/api';
import { StatusUpdate } from '@/types/application';

export function useApplications(statusFilter?: string) {
  return useQuery({
    queryKey: ['applications', statusFilter],
    queryFn: async () => {
      const response = await applicationsApi.getStatistics();
      return response.data;
    },
    staleTime: 30000,
  });
}

export function useApplicationTimeline(jobId: number) {
  return useQuery({
    queryKey: ['timeline', jobId],
    queryFn: async () => {
      const response = await applicationsApi.getTimeline(jobId);
      return response.data;
    },
    enabled: !!jobId,
  });
}

export function useUpdateStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ jobId, status }: { jobId: number; status: StatusUpdate }) =>
      applicationsApi.updateStatus(jobId, status),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['job', variables.jobId] });
      queryClient.invalidateQueries({ queryKey: ['applications'] });
      queryClient.invalidateQueries({ queryKey: ['timeline', variables.jobId] });
    },
  });
}

export function useATSStatistics() {
  return useQuery({
    queryKey: ['ats-statistics'],
    queryFn: async () => {
      const response = await applicationsApi.getStatistics();
      return response.data;
    },
    staleTime: 60000, // 1 minute
  });
}
