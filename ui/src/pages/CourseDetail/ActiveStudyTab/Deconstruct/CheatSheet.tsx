import type { CheatSheetItem } from '../../../../api/types';
import styles from './Deconstruct.module.css';

export function CheatSheet({ items }: { items: CheatSheetItem[] }) {
  if (!items.length)
    return <p style={{ color: 'var(--text-secondary)' }}>Nessun elemento disponibile.</p>;
  return (
    <div className={styles.pane}>
      {items.map((item, idx) => (
        <div key={idx} className={styles.itemCard}>
          <strong>{item.term}</strong>
          <p>{item.definition}</p>
        </div>
      ))}
    </div>
  );
}
