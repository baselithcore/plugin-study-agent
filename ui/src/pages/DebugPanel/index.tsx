import { useState } from 'react';
import { Button } from '../../components/Button/Button';
import { useClearDebugEvents, useDebugEvents } from '../../api/debug';
import styles from './DebugPanel.module.css';

export function DebugPanel() {
  const [open, setOpen] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const { data: events = [] } = useDebugEvents(open);
  const clearEvents = useClearDebugEvents();

  if (!open) {
    return (
      <button className={styles.trigger} onClick={() => setOpen(true)}>
        🐞 Baselith Telemetry &amp; Trace
      </button>
    );
  }

  return (
    <div className={styles.sidebar}>
      <div className={styles.header}>
        <h3>Baselith Telemetry &amp; Trace</h3>
        <button className={styles.closeBtn} onClick={() => setOpen(false)}>
          &times;
        </button>
      </div>
      <Button
        size="sm"
        variant="secondary"
        onClick={() => clearEvents.mutate()}
        style={{ marginBottom: '1rem' }}
      >
        Pulisci eventi
      </Button>
      {events.length === 0 && (
        <p style={{ color: 'var(--text-secondary)' }}>Nessun evento tracciato.</p>
      )}
      {events.map((event, idx) => (
        <div
          key={idx}
          className={styles.eventItem}
          onClick={() => setExpandedId(expandedId === idx ? null : idx)}
        >
          <div className={styles.eventHeader}>
            <span className={`${styles.badge} ${styles[event.event_type] ?? ''}`}>
              {event.event_type}
            </span>
            <span style={{ color: 'var(--text-muted)' }}>{event.timestamp}</span>
          </div>
          {expandedId === idx && (
            <pre className={styles.details}>{JSON.stringify(event.details, null, 2)}</pre>
          )}
        </div>
      ))}
    </div>
  );
}
