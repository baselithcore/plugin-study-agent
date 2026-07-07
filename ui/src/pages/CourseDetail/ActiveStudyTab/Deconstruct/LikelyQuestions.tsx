import { useState } from 'react';
import type { LikelyQuestion } from '../../../../api/types';
import styles from './Deconstruct.module.css';

export function LikelyQuestions({ items }: { items: LikelyQuestion[] }) {
  const [expanded, setExpanded] = useState<number[]>([]);

  if (!items.length)
    return <p style={{ color: 'var(--text-secondary)' }}>Nessuna domanda disponibile.</p>;

  const toggle = (idx: number) =>
    setExpanded((prev) => (prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]));

  return (
    <div className={styles.pane}>
      {items.map((item, idx) => (
        <div key={idx} className={styles.itemCard} onClick={() => toggle(idx)}>
          <strong>
            {item.question}
            <span className={styles.expandArrow}>{expanded.includes(idx) ? '▲' : '▼'}</span>
          </strong>
          {expanded.includes(idx) && (
            <div className={styles.answerBox}>
              <p>{item.focus_answer}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
