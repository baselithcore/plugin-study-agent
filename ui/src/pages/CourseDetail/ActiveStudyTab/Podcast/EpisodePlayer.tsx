import { useState } from 'react';
import { podcastAudioUrl } from '../../../../api/client';
import type { Podcast } from '../../../../api/types';
import styles from './Podcast.module.css';

export function EpisodePlayer({ podcast }: { podcast: Podcast }) {
  const [activeEpisode, setActiveEpisode] = useState(podcast.episodes[0] ?? null);

  return (
    <div className={styles.player}>
      <h4 style={{ margin: 0, fontSize: '1.15rem', color: '#f1f5f9' }}>{podcast.title}</h4>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
        {podcast.professor_name} &middot; {podcast.topic}
      </p>

      {activeEpisode && (
        <audio
          className={styles.audio}
          controls
          src={podcastAudioUrl(activeEpisode.audio_filename)}
        />
      )}

      <div className={styles.episodeList}>
        {podcast.episodes.map((ep) => (
          <div
            key={ep.episode_number}
            className={`${styles.episodeItem} ${activeEpisode?.episode_number === ep.episode_number ? styles.active : ''}`}
            onClick={() => setActiveEpisode(ep)}
          >
            Episodio {ep.episode_number} — {ep.title}
          </div>
        ))}
      </div>
    </div>
  );
}
