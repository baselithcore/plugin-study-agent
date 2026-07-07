import { CloseIcon } from '../../../../components/Icons';
import type { Podcast } from '../../../../api/types';
import styles from './Podcast.module.css';

interface PodcastListProps {
  podcasts: Podcast[];
  onSelect: (podcast: Podcast) => void;
  onDelete: (podcastId: number) => void;
}

export function PodcastList({ podcasts, onSelect, onDelete }: PodcastListProps) {
  if (!podcasts.length) {
    return (
      <p style={{ color: 'var(--text-secondary)' }}>Nessun podcast generato per questa materia.</p>
    );
  }
  return (
    <div className={styles.list}>
      {podcasts.map((p) => (
        <div key={p.id} className={styles.podcastItem} onClick={() => onSelect(p)}>
          <div>
            <div className={styles.podcastTitle}>{p.title}</div>
            <span className={styles.podcastBadge}>{p.episodes.length} puntate</span>
          </div>
          <button
            className="finder-action-btn"
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
            }}
            onClick={(e) => {
              e.stopPropagation();
              onDelete(p.id);
            }}
            title="Elimina podcast"
          >
            <CloseIcon style={{ width: '1rem', height: '1rem' }} />
          </button>
        </div>
      ))}
    </div>
  );
}
