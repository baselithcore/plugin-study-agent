import { useNavigate } from 'react-router-dom';
import { StatCard, StatCardBanner } from '../../../components/StatCard/StatCard';
import { Button } from '../../../components/Button/Button';
import { useDocuments } from '../../../api/files';
import { useFlashcards, useGenerateFlashcards } from '../../../api/flashcards';
import { useCourseSubject } from '../useCourseSubject';
import styles from './FlashcardsTab.module.css';

export function FlashcardsTab() {
  const { subjectId } = useCourseSubject();
  const navigate = useNavigate();
  const { data: deck } = useFlashcards(subjectId);
  const { data: documents = [] } = useDocuments(subjectId);
  const generate = useGenerateFlashcards(subjectId);

  const stats = deck?.stats ?? { total: 0, due: 0, new: 0 };
  const flashcards = deck?.flashcards ?? [];

  return (
    <div>
      <StatCardBanner>
        <StatCard value={stats.total} label="Totale Carte" />
        <StatCard value={stats.due} label="Da Ripassare" color="var(--danger)" />
        <StatCard value={stats.new} label="Nuove" color="var(--success)" />
      </StatCardBanner>

      <div className={styles.actionsRow}>
        {stats.due > 0 && (
          <Button onClick={() => navigate(`/subjects/${subjectId}/study?due=true`)}>
            Avvia Ripasso Reminescenza ({stats.due} dovute)
          </Button>
        )}
        {stats.total > 0 && (
          <Button variant="secondary" onClick={() => navigate(`/subjects/${subjectId}/study`)}>
            Studia Tutto il Deck ({stats.total} carte)
          </Button>
        )}
        <Button
          variant={stats.total > 0 ? 'secondary' : 'primary'}
          onClick={() => generate.mutate(10)}
          disabled={generate.isPending || !documents.length}
        >
          {generate.isPending ? 'Generating...' : 'Genera da Materiale con AI'}
        </Button>
      </div>

      {generate.isPending && (
        <div className={styles.generating}>
          L'intelligenza artificiale sta analizzando i documenti per estrarre formule e
          definizioni...
        </div>
      )}

      <h3 className="section-heading">Anteprima Flashcards</h3>
      {flashcards.length ? (
        <div className={styles.previewList}>
          {flashcards.map((c) => (
            <div key={c.id} className={styles.previewItem}>
              <strong>D:</strong> {c.question}
              <br />
              <span className={styles.previewAnswer}>
                <strong>R:</strong> {c.answer}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p style={{ color: 'var(--text-secondary)' }}>
          Nessuna flashcard disponibile. Carica materiali didattici e clicca su "Genera da
          Materiale" per crearle automaticamente.
        </p>
      )}
    </div>
  );
}
