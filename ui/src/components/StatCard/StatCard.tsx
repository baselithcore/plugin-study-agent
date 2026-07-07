import type { ReactNode } from 'react';
import styles from './StatCard.module.css';

interface StatCardProps {
  value: ReactNode;
  label: string;
  color?: string;
}

export function StatCard({ value, label, color }: StatCardProps) {
  return (
    <div className={styles.card}>
      <div className={styles.num} style={color ? { color } : undefined}>
        {value}
      </div>
      <div className={styles.label}>{label}</div>
    </div>
  );
}

export function StatCardBanner({ children }: { children: ReactNode }) {
  return <div className={styles.banner}>{children}</div>;
}
