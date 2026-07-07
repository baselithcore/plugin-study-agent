import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, postNdjsonStream } from './client';
import type { Podcast, PodcastStreamEvent } from './types';

export const podcastKeys = {
  list: (subjectId: number) => ['podcasts', subjectId] as const,
};

export function usePodcasts(subjectId: number) {
  return useQuery({
    queryKey: podcastKeys.list(subjectId),
    queryFn: () => api.get<Podcast[]>(`/subjects/${subjectId}/podcasts`),
    enabled: Number.isFinite(subjectId),
  });
}

export function useDeletePodcast(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (podcastId: number) => api.delete(`/podcasts/${podcastId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: podcastKeys.list(subjectId) }),
  });
}

export interface GeneratePodcastPayload {
  topic: string;
  depth_level: 'breve' | 'normale' | 'approfondito';
}

/** Drives the streaming podcast generation endpoint, calling onEvent per progress update. */
export async function generatePodcastStream(
  subjectId: number,
  payload: GeneratePodcastPayload,
  onEvent: (event: PodcastStreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  await postNdjsonStream<PodcastStreamEvent>(
    `/subjects/${subjectId}/podcasts/generate-stream`,
    payload,
    onEvent,
    signal
  );
}
