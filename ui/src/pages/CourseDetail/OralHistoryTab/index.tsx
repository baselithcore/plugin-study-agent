import { useNavigate } from 'react-router-dom';
import { EmptyState } from '../../../components/EmptyState/EmptyState';
import { Badge } from '../../../components/Badge/Badge';
import { BookIcon } from '../../../components/Icons';
import { useOralSessions } from '../../../api/sessions';
import { useCourseSubject } from '../useCourseSubject';
import styles from './OralHistoryTab.module.css';

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export function OralHistoryTab() {
  const { subjectId } = useCourseSubject();
  const navigate = useNavigate();
  const { data: sessions = [] } = useOralSessions(subjectId);

  return (
    <div>
      <h3 className="section-heading" style={{ marginBottom: '1.25rem' }}>
        Storico Sessioni d'Esame
      </h3>

      {!sessions.length ? (
        <EmptyState
          icon={<BookIcon />}
          title="Nessuna sessione d'esame completata per questa materia."
          description='Vai alla scheda "Interrogazione Orale" per iniziare una simulazione.'
        />
      ) : (
        <div className={styles.list}>
          {sessions.map((s) => (
            <div
              key={s.id}
              className={styles.card}
              onClick={() => navigate(`/subjects/${subjectId}/oral-live?session=${s.id}`)}
            >
              <div className={styles.cardTop}>
                <span className={styles.profName}>{s.professor_name}</span>
                <div className={styles.meta}>
                  <span className={styles.date}>{formatDate(s.created_at)}</span>
                  <Badge tone={s.status === 'completed' ? 'success' : 'warning'}>
                    {s.status === 'completed' ? 'Completato' : 'In corso'}
                  </Badge>
                </div>
              </div>
              <div className={styles.details}>
                <span>Difficoltà: {s.difficulty_level}/5</span>
                <span>Stile: {s.strictness}</span>
                {s.score != null && (
                  <span className={styles.score}>Voto: {Math.round((s.score / 10) * 30)}/30</span>
                )}
                {s.current_topic && <span>Tema: {s.current_topic}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
