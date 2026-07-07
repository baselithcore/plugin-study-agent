import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type { OralSession } from './types';

export const sessionKeys = {
  list: (subjectId: number) => ['oral-sessions', subjectId] as const,
  detail: (sessionId: number) => ['oral-session', sessionId] as const,
};

export function useOralSessions(subjectId: number) {
  return useQuery({
    queryKey: sessionKeys.list(subjectId),
    queryFn: () => api.get<OralSession[]>(`/subjects/${subjectId}/sessions`),
    enabled: Number.isFinite(subjectId),
  });
}

export function useOralSession(sessionId: number | null) {
  return useQuery({
    queryKey: sessionKeys.detail(sessionId ?? -1),
    queryFn: () => api.get<OralSession>(`/sessions/oral/${sessionId}`),
    enabled: sessionId != null,
  });
}

export interface StartSessionPayload {
  subject_id: number;
  professor_name: string;
  strictness: 'amichevole' | 'equo' | 'scrupoloso';
  difficulty_level: number;
}

export interface StartSessionResult {
  session_id: number;
  professor_name: string;
  strictness: string;
  difficulty_level: number;
  topics: string[];
}

export function useStartOralSession() {
  return useMutation({
    mutationFn: (payload: StartSessionPayload) =>
      api.post<StartSessionResult>('/sessions/oral/start', payload),
  });
}

export interface NextQuestionResult {
  status: 'active' | 'completed';
  topic?: string;
  style?: string;
  text?: string;
  audio?: string | null;
  avg_score?: number;
  final_grade?: string;
  transcript?: unknown[];
}

export function useNextOralQuestion() {
  return useMutation({
    mutationFn: (sessionId: number) => {
      const form = new FormData();
      form.append('session_id', String(sessionId));
      return api.postForm<NextQuestionResult>('/sessions/oral/next', form);
    },
  });
}

export interface AnswerResult {
  score: number;
  feedback: string;
  is_correct: boolean;
}

export function useAnswerOralQuestion() {
  return useMutation({
    mutationFn: (payload: { session_id: number; answer_text: string }) =>
      api.post<AnswerResult>('/sessions/oral/answer', payload),
  });
}

export function useTranscribeAudio() {
  return useMutation({
    mutationFn: (blob: Blob) => {
      const form = new FormData();
      form.append('file', blob, 'answer.webm');
      return api.postForm<{ text: string }>('/sessions/oral/transcribe', form);
    },
  });
}

export function useSpeakText() {
  return useMutation({
    mutationFn: ({ text, strictness }: { text: string; strictness?: string }) => {
      const form = new FormData();
      form.append('text', text);
      if (strictness) form.append('strictness', strictness);
      return api.postForm<{ audio: string }>('/sessions/oral/speak', form);
    },
  });
}

export function invalidateSessionQueries(qc: ReturnType<typeof useQueryClient>, subjectId: number) {
  qc.invalidateQueries({ queryKey: sessionKeys.list(subjectId) });
}
