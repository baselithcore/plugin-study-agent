import type { ReactNode } from 'react';
import styles from './PageHeader.module.css';

interface PageHeaderProps {
  title: string;
  description?: string;
  backLabel?: string;
  onBack?: () => void;
  actions?: ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  backLabel,
  onBack,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div className={`${styles.header} ${className ?? ''}`}>
      <div className={styles.titleArea}>
        {onBack && backLabel && (
          <button className={styles.backLink} onClick={onBack}>
            &larr; {backLabel}
          </button>
        )}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className={styles.actions}>{actions}</div>}
    </div>
  );
}
