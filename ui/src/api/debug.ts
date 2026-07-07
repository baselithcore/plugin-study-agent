import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type { DebugEvent } from './types';

export function useDebugEvents(enabled: boolean) {
  return useQuery({
    queryKey: ['debug-events'],
    queryFn: () => api.get<DebugEvent[]>('/debug/events'),
    enabled,
    refetchInterval: enabled ? 3000 : false,
  });
}

export function useClearDebugEvents() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post('/debug/clear'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['debug-events'] }),
  });
}
