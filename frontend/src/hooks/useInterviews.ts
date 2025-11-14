'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { interviewsApi, followUpsApi } from '@/lib/api';

export function useUpcomingInterviews(daysAhead: number = 7) {
  return useQuery({
    queryKey: ['interviews', 'upcoming', daysAhead],
    queryFn: async () => {
      const response = await interviewsApi.upcoming({ days_ahead: daysAhead });
      return response.data;
    },
    staleTime: 60000,
  });
}

export function useJobInterviews(jobId: number) {
  return useQuery({
    queryKey: ['interviews', 'job', jobId],
    queryFn: async () => {
      const response = await interviewsApi.getForJob(jobId);
      return response.data;
    },
    enabled: !!jobId,
  });
}

export function useCreateInterview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => interviewsApi.create(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
      queryClient.invalidateQueries({ queryKey: ['interviews', 'job', variables.job_id] });
    },
  });
}

export function useUpdateInterview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      interviewsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
    },
  });
}

export function useDueFollowUps(hoursAhead: number = 24) {
  return useQuery({
    queryKey: ['followups', 'due', hoursAhead],
    queryFn: async () => {
      const response = await followUpsApi.due({ hours_ahead: hoursAhead });
      return response.data;
    },
    staleTime: 60000,
  });
}
