import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type { DeconstructedData, FeynmanEvaluation } from './types';

export function useFeynmanConcept(subjectId: number, enabled: boolean) {
  return useQuery({
    queryKey: ['feynman-concept', subjectId],
    queryFn: () => api.get<{ concept: string }>(`/active/feynman/concept?subject_id=${subjectId}`),
    enabled: enabled && Number.isFinite(subjectId),
    staleTime: Infinity,
  });
}

export interface FeynmanHistoryItem {
  role: 'assistant' | 'student';
  text: string;
}

export function useFeynmanRespond() {
  return useMutation({
    mutationFn: (payload: {
      subjectId: number;
      conceptName: string;
      explanation: string;
      history: FeynmanHistoryItem[];
    }) => {
      const form = new FormData();
      form.append('subject_id', String(payload.subjectId));
      form.append('concept_name', payload.conceptName);
      form.append('explanation', payload.explanation);
      form.append('history_json', JSON.stringify(payload.history));
      return api.postForm<FeynmanEvaluation>('/active/feynman/respond', form);
    },
  });
}

export function useDeconstructSubject(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (forceRefresh: boolean) =>
      api.post<DeconstructedData>(
        `/subjects/${subjectId}/deconstruct?force_refresh=${forceRefresh}`
      ),
    onSuccess: (data) => {
      qc.setQueryData(['deconstruct', subjectId], data);
    },
  });
}

export function useSubjectTopics(subjectId: number, enabled: boolean) {
  return useQuery({
    queryKey: ['topics', subjectId],
    queryFn: () => api.get<{ topics: string[] }>(`/subjects/${subjectId}/topics`),
    enabled: enabled && Number.isFinite(subjectId),
  });
}
