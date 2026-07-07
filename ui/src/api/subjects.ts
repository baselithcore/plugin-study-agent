import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type { Subject } from './types';

export const subjectKeys = {
  all: ['subjects'] as const,
};

export function useSubjects() {
  return useQuery({
    queryKey: subjectKeys.all,
    queryFn: () => api.get<Subject[]>('/subjects'),
  });
}

export function useCreateSubject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name: string; description?: string }) =>
      api.post<Subject>('/subjects', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: subjectKeys.all }),
  });
}

export function useDeleteSubject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (subjectId: number) => api.delete(`/subjects/${subjectId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: subjectKeys.all }),
  });
}
