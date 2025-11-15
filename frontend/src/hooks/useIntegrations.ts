'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

export interface Integration {
  name: string;
  type: 'google_calendar' | 'google_drive' | 'google_gmail' | 'linkedin' | 'indeed';
  status: 'connected' | 'disconnected' | 'error';
  connected_at?: string;
  last_sync?: string;
  error_message?: string;
  metadata?: {
    email?: string;
    scopes?: string[];
    expires_at?: string;
  };
}

export interface IntegrationsResponse {
  integrations: Integration[];
  google_auth_configured: boolean;
  google_credentials_valid: boolean;
}

/**
 * Hook to fetch all integration statuses
 */
export function useIntegrations() {
  return useQuery<IntegrationsResponse>({
    queryKey: ['integrations'],
    queryFn: async () => {
      const response = await apiClient.get('/integrations/status');
      return response.data;
    },
    staleTime: 60000, // 1 minute
    refetchInterval: 300000, // Refetch every 5 minutes
  });
}

/**
 * Hook to get a specific integration status
 */
export function useIntegration(type: Integration['type']) {
  const { data } = useIntegrations();
  return data?.integrations.find((i) => i.type === type);
}

/**
 * Hook to connect Google services
 */
export function useConnectGoogle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/integrations/google/connect');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });
}

/**
 * Hook to disconnect an integration
 */
export function useDisconnectIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (type: Integration['type']) => {
      const response = await apiClient.post(`/integrations/${type}/disconnect`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });
}

/**
 * Hook to test an integration connection
 */
export function useTestIntegration() {
  return useMutation({
    mutationFn: async (type: Integration['type']) => {
      const response = await apiClient.post(`/integrations/${type}/test`);
      return response.data;
    },
  });
}
