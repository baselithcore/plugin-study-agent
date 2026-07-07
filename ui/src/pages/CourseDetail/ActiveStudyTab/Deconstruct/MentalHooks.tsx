import type { MentalHook } from '../../../../api/types';
import styles from './Deconstruct.module.css';

const HOOK_COLORS = ['var(--purple)', 'var(--success)', 'var(--warning)', 'var(--danger)'];

export function MentalHooks({ items }: { items: MentalHook[] }) {
  if (!items.length)
    return <p style={{ color: 'var(--text-secondary)' }}>Nessun aggancio mnemonico disponibile.</p>;
  return (
    <div className={styles.pane}>
      {items.map((item, idx) => (
        <div
          key={idx}
          className={styles.itemCard}
          style={{ borderLeft: `4px solid ${HOOK_COLORS[idx % HOOK_COLORS.length]}` }}
        >
          <strong>{item.concept}</strong>
          <p>{item.mnemonic}</p>
        </div>
      ))}
    </div>
  );
}
