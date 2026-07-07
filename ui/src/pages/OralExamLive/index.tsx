import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useSubjects } from '../../api/subjects';
import { useLiveExam } from './useLiveExam';
import { ProfSidebar } from './ProfSidebar';
import { Transcript } from './Transcript';
import { InputBar } from './InputBar';
import styles from './OralExamLive.module.css';

const MODE_LABELS: Record<string, string> = {
  idle: 'Pronto',
  thinking: 'Sta pensando...',
  speaking: 'Sta parlando...',
  listening: 'In ascolto',
  evaluating: 'Valutazione in corso...',
};

export function OralExamLive() {
  const { subjectId: subjectIdParam } = useParams<{ subjectId: string }>();
  const subjectId = Number(subjectIdParam);
  const [searchParams] = useSearchParams();
  const sessionId = Number(searchParams.get('session'));
  const navigate = useNavigate();

  const { data: subjects } = useSubjects();
  const subject = subjects?.find((s) => s.id === subjectId);

  const {
    session,
    isLoading,
    transcript,
    liveMode,
    topics,
    doneTopics,
    currentTopic,
    submitAnswer,
    submitAudioAnswer,
    isBusy,
  } = useLiveExam(subjectId, sessionId);

  if (!Number.isFinite(sessionId) || !sessionId) {
    return (
      <div className={styles.shell}>
        <div style={{ margin: 'auto', textAlign: 'center' }}>
          <p>Nessuna sessione attiva.</p>
          <button className={styles.quitBtn} onClick={() => navigate(`/subjects/${subjectId}`)}>
            Torna alla materia
          </button>
        </div>
      </div>
    );
  }

  if (isLoading || !session) return null;

  return (
    <div className={styles.shell}>
      <div className={styles.topbar}>
        <span className={styles.subjectBadge}>{subject?.name ?? ''}</span>
        <div className={styles.centerTitle}>
          <span className={`${styles.dot} ${styles[liveMode]}`} />
          {MODE_LABELS[liveMode]}
        </div>
        <button
          className={styles.quitBtn}
          onClick={() => navigate(`/subjects/${subjectId}/oral-history`)}
        >
          Esci
        </button>
      </div>

      <div className={styles.main}>
        <ProfSidebar
          professorName={session.professor_name}
          strictness={session.strictness}
          liveMode={liveMode}
          topics={topics}
          doneTopics={doneTopics}
          currentTopic={currentTopic}
        />
        <div className={styles.rightCol}>
          <div className={styles.transcript}>
            <Transcript blocks={transcript} isThinking={liveMode === 'thinking'} />
          </div>
          {session.status === 'active' && (
            <InputBar
              liveMode={liveMode}
              disabled={isBusy}
              onSubmitText={submitAnswer}
              onSubmitAudio={submitAudioAnswer}
            />
          )}
        </div>
      </div>
    </div>
  );
}
