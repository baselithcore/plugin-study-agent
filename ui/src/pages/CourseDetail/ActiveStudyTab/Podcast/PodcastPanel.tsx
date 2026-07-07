import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  podcastKeys,
  usePodcasts,
  useDeletePodcast,
  generatePodcastStream,
} from '../../../../api/podcasts';
import type { Podcast, PodcastStreamEvent } from '../../../../api/types';
import { GenerateForm } from './GenerateForm';
import { StreamProgress } from './StreamProgress';
import { EpisodePlayer } from './EpisodePlayer';
import { PodcastList } from './PodcastList';
import styles from './Podcast.module.css';

export function PodcastPanel({ subjectId }: { subjectId: number }) {
  const { data: podcasts = [] } = usePodcasts(subjectId);
  const deletePodcast = useDeletePodcast(subjectId);
  const qc = useQueryClient();

  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState<PodcastStreamEvent | null>(null);
  const [selectedPodcast, setSelectedPodcast] = useState<Podcast | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async (topic: string, depth: 'breve' | 'normale' | 'approfondito') => {
    setIsGenerating(true);
    setError(null);
    setProgress({ status: 'analyzing', message: 'Analisi dei materiali del corso...' });
    try {
      await generatePodcastStream(subjectId, { topic, depth_level: depth }, (event) => {
        setProgress(event);
        if (event.status === 'completed' || event.status === 'completed_with_errors') {
          setSelectedPodcast(event.podcast);
          qc.invalidateQueries({ queryKey: podcastKeys.list(subjectId) });
        }
        if (event.status === 'error') {
          setError(event.message);
        }
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className={styles.layout}>
      <GenerateForm onGenerate={handleGenerate} isGenerating={isGenerating} />

      {isGenerating && progress && (
        <StreamProgress
          message={progress.status === 'error' ? progress.message : progress.message}
          totalEpisodes={'total_episodes' in progress ? (progress.total_episodes ?? 0) : 0}
          completedEpisodes={
            'completed_episodes' in progress ? (progress.completed_episodes ?? 0) : 0
          }
        />
      )}

      {error && <p style={{ color: 'var(--danger-light)' }}>{error}</p>}

      {selectedPodcast && <EpisodePlayer podcast={selectedPodcast} />}

      <div>
        <h4 style={{ margin: '0 0 0.75rem 0' }}>I Tuoi Podcast</h4>
        <PodcastList
          podcasts={podcasts}
          onSelect={setSelectedPodcast}
          onDelete={(id) => {
            deletePodcast.mutate(id);
            if (selectedPodcast?.id === id) setSelectedPodcast(null);
          }}
        />
      </div>
    </div>
  );
}
