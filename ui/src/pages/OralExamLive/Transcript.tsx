import { useEffect, useRef } from 'react';
import type { TranscriptBlock } from '../../api/types';
import styles from './Transcript.module.css';

interface TranscriptProps {
  blocks: TranscriptBlock[];
  isThinking: boolean;
}

export function Transcript({ blocks, isThinking }: TranscriptProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [blocks, isThinking]);

  return (
    <>
      {blocks.map((block, idx) => {
        if (block.type === 'system') {
          return (
            <div key={idx} className={styles.systemMsg}>
              {block.message}
            </div>
          );
        }
        if (block.type === 'question') {
          return (
            <div key={idx} className={styles.msgProf}>
              <div className={`${styles.bubble} ${styles.profBubble}`}>{block.text}</div>
            </div>
          );
        }
        if (block.type === 'answer') {
          return (
            <div key={idx} className={styles.msgStudent}>
              <div className={`${styles.bubble} ${styles.studentBubble}`}>{block.text}</div>
            </div>
          );
        }
        if (block.type === 'evaluation') {
          return (
            <div key={idx} className={styles.evalCard}>
              <span
                className={`${styles.scoreBadge} ${block.is_correct ? styles.ok : styles.fail}`}
              >
                {block.score.toFixed(1)}
              </span>
              <span className={styles.evalText}>{block.feedback}</span>
            </div>
          );
        }
        if (block.type === 'system_finish') {
          return (
            <div key={idx} className={styles.finishCard}>
              <div className={styles.finishGrade}>{block.final_grade}</div>
              <div className={styles.finishLabel}>Voto Finale</div>
              <div className={styles.finishAvg}>
                Media argomenti: {block.avg_score.toFixed(1)}/10
              </div>
            </div>
          );
        }
        return null;
      })}

      {isThinking && (
        <div className={styles.typingDots}>
          <span />
          <span />
          <span />
        </div>
      )}

      <div ref={endRef} />
    </>
  );
}
