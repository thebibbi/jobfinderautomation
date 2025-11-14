'use client';

import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api';

export function useAnalyticsOverview() {
  return useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: async () => {
      const response = await analyticsApi.overview();
      return response.data;
    },
    staleTime: 300000, // 5 minutes
  });
}

export function useFunnelAnalysis(params?: any) {
  return useQuery({
    queryKey: ['analytics', 'funnel', params],
    queryFn: async () => {
      const response = await analyticsApi.funnel(params);
      return response.data;
    },
    staleTime: 300000,
  });
}

export function useTrends(params?: any) {
  return useQuery({
    queryKey: ['analytics', 'trends', params],
    queryFn: async () => {
      const response = await analyticsApi.trends(params);
      return response.data;
    },
    staleTime: 300000,
  });
}

export function useSuccessPatterns() {
  return useQuery({
    queryKey: ['analytics', 'success-patterns'],
    queryFn: async () => {
      const response = await analyticsApi.successPatterns();
      return response.data;
    },
    staleTime: 300000,
  });
}
