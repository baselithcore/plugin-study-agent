import styles from './Podcast.module.css';

interface StreamProgressProps {
  message: string;
  totalEpisodes: number;
  completedEpisodes: number;
}

export function StreamProgress({ message, totalEpisodes, completedEpisodes }: StreamProgressProps) {
  const pct = totalEpisodes > 0 ? (completedEpisodes / totalEpisodes) * 100 : 0;
  return (
    <div style={{ textAlign: 'center' }}>
      <div className={styles.progressStatus}>{message}</div>
      {totalEpisodes > 0 && (
        <div
          className={styles.progressBarContainer}
          style={{ marginLeft: 'auto', marginRight: 'auto' }}
        >
          <div className={styles.progressBarFill} style={{ width: `${pct}%` }} />
        </div>
      )}
      {totalEpisodes > 0 && (
        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          {completedEpisodes} / {totalEpisodes} puntate pronte
        </div>
      )}
    </div>
  );
}
