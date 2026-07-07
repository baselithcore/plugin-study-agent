import { Badge } from '../../../components/Badge/Badge';
import type { QueueItem } from './useUploadQueue';
import styles from './UploadQueue.module.css';

export function UploadQueue({ items }: { items: QueueItem[] }) {
  if (!items.length) return null;
  return (
    <div className={styles.queue}>
      {items.map((item) => (
        <div key={item.id} className={`${styles.item} ${styles[item.status]}`}>
          <div className={styles.header}>
            <span className={styles.name}>{item.name}</span>
            <Badge
              tone={
                item.status === 'done' ? 'success' : item.status === 'error' ? 'danger' : 'gold'
              }
            >
              {item.status === 'uploading'
                ? 'Caricamento'
                : item.status === 'done'
                  ? 'Completato'
                  : 'Errore'}
            </Badge>
          </div>
          <div className={styles.bar}>
            <div
              className={`${styles.fill} ${styles[item.status]}`}
              style={{ width: `${item.progress}%` }}
            />
          </div>
          {item.error && <div className={styles.errorMsg}>{item.error}</div>}
        </div>
      ))}
    </div>
  );
}
