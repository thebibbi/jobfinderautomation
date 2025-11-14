'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recommendationsApi } from '@/lib/api';
import { RecommendationFilters } from '@/types/recommendation';

export function useRecommendations(filters: RecommendationFilters = {}) {
  return useQuery({
    queryKey: ['recommendations', filters],
    queryFn: async () => {
      const response = await recommendationsApi.list(filters);
      return response.data;
    },
    staleTime: 60000, // 1 minute
  });
}

export function useLearnClick() {
  return useMutation({
    mutationFn: (jobId: number) => recommendationsApi.learnClick(jobId),
  });
}

export function useLearnDismiss() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ jobId, reason }: { jobId: number; reason: string }) =>
      recommendationsApi.learnDismiss(jobId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
    },
  });
}
