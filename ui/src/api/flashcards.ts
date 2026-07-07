import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type { Flashcard, FlashcardStats } from './types';

export const flashcardKeys = {
  deck: (subjectId: number, dueOnly: boolean) => ['flashcards', subjectId, dueOnly] as const,
};

interface FlashcardDeckResponse {
  flashcards: Flashcard[];
  stats: FlashcardStats;
}

export function useFlashcards(subjectId: number, dueOnly = false) {
  return useQuery({
    queryKey: flashcardKeys.deck(subjectId, dueOnly),
    queryFn: () =>
      api.get<FlashcardDeckResponse>(
        `/subjects/${subjectId}/flashcards${dueOnly ? '?due_only=true' : ''}`
      ),
    enabled: Number.isFinite(subjectId),
  });
}

export function useGenerateFlashcards(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (numFlashcards: number) =>
      api.post<{ success: boolean; count: number }>(`/subjects/${subjectId}/flashcards/generate`, {
        num_flashcards: numFlashcards,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['flashcards', subjectId] }),
  });
}

export interface FlashcardReviewResult {
  id: number;
  ease_factor: number;
  interval_days: number;
  repetitions: number;
  next_review: string;
}

export function useReviewFlashcard(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { flashcard_id: number; rating: number }) =>
      api.post<FlashcardReviewResult>('/flashcards/review', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['flashcards', subjectId] }),
  });
}
