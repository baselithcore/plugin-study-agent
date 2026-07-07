import type { LiveMode } from './useLiveExam';
import styles from './ProfSidebar.module.css';

interface ProfSidebarProps {
  professorName: string;
  strictness: string;
  liveMode: LiveMode;
  topics: string[];
  doneTopics: Set<string>;
  currentTopic: string | null;
}

export function ProfSidebar({
  professorName,
  strictness,
  liveMode,
  topics,
  doneTopics,
  currentTopic,
}: ProfSidebarProps) {
  const isActive = liveMode === 'speaking' || liveMode === 'thinking';
  return (
    <div className={styles.profArea}>
      <div className={styles.avatarWrap}>
        <div className={`${styles.ring} ${isActive ? styles.active : ''}`} />
        <div className={`${styles.ring} ${styles.ring2} ${isActive ? styles.active : ''}`} />
        <div className={`${styles.avatar} ${styles[strictness] ?? ''}`}>🎓</div>
      </div>
      <div className={styles.name}>{professorName}</div>
      <span className={`${styles.tag} ${styles[strictness] ?? ''}`}>{strictness}</span>

      {topics.length > 0 && (
        <div className={styles.pills}>
          {topics.map((topic) => (
            <div
              key={topic}
              className={`${styles.pill} ${
                topic === currentTopic ? styles.current : doneTopics.has(topic) ? styles.done : ''
              }`}
            >
              {topic}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
