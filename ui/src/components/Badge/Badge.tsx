import type { ReactNode } from 'react';
import styles from './Badge.module.css';

type Tone = 'gold' | 'success' | 'warning' | 'danger' | 'neutral';

export function Badge({ tone = 'neutral', children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`${styles.badge} ${styles[tone]}`}>{children}</span>;
}
