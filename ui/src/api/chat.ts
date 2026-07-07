import { useMutation } from '@tanstack/react-query';
import { api } from './client';

export interface ChatResult {
  answer: string;
  sources_used: string[];
}

export function useAskTutor(subjectId: number) {
  return useMutation({
    mutationFn: (query: string) => {
      const form = new FormData();
      form.append('query', query);
      return api.postForm<ChatResult>(`/subjects/${subjectId}/chat`, form);
    },
  });
}
