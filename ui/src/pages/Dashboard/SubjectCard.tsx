import { useNavigate } from 'react-router-dom';
import type { Subject } from '../../api/types';
import styles from './Dashboard.module.css';

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export function SubjectCard({ subject }: { subject: Subject }) {
  const navigate = useNavigate();
  return (
    <div className={styles.card} onClick={() => navigate(`/subjects/${subject.id}`)}>
      <h3>{subject.name}</h3>
      <p>{subject.description || 'Nessuna descrizione fornita.'}</p>
      <div className={styles.cardStats}>
        <span>Aggiunto il: {formatDate(subject.created_at)}</span>
        <span>Apri dettagli &rarr;</span>
      </div>
    </div>
  );
}
