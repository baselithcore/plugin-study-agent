import { useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { PageHeader } from '../../components/PageHeader/PageHeader';
import { Button } from '../../components/Button/Button';
import { useFlashcards, useReviewFlashcard } from '../../api/flashcards';
import styles from './FlashcardStudy.module.css';

const RATINGS = [
  { value: 0, label: 'Buio totale (0)', color: 'var(--danger)' },
  { value: 1, label: 'Quasi dimenticato (1)', color: '#f97316' },
  { value: 2, label: 'Molta fatica (2)', color: '#eab308' },
  { value: 3, label: 'Ricordato con sforzo (3)', color: '#84cc16' },
  { value: 4, label: 'Buon ricordo (4)', color: 'var(--success)' },
  { value: 5, label: 'Immediato e perfetto (5)', color: '#06b6d4' },
];

export function FlashcardStudy() {
  const { subjectId: subjectIdParam } = useParams<{ subjectId: string }>();
  const subjectId = Number(subjectIdParam);
  const [searchParams] = useSearchParams();
  const dueOnly = searchParams.get('due') === 'true';
  const navigate = useNavigate();

  const { data: deck } = useFlashcards(subjectId, dueOnly);
  const review = useReviewFlashcard(subjectId);

  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [reviewedIds, setReviewedIds] = useState<number[]>([]);

  const studyDeck = useMemo(
    () => (deck?.flashcards ?? []).filter((c) => !reviewedIds.includes(c.id)),
    [deck, reviewedIds]
  );
  const card = studyDeck[currentIndex];

  const handleReview = async (rating: number) => {
    if (!card) return;
    await review.mutateAsync({ flashcard_id: card.id, rating });
    setReviewedIds((prev) => [...prev, card.id]);
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev >= studyDeck.length - 1 ? 0 : prev));
  };

  return (
    <div className={styles.container}>
      <PageHeader
        title={`Ripasso Flashcard`}
        description="Studio attivo con ripetizione spaziata. Clicca sulla carta per rivelare la risposta."
        backLabel="Chiudi Arena"
        onBack={() => navigate(`/subjects/${subjectId}/flashcards`)}
        actions={
          <span className={styles.counter}>
            Carta {studyDeck.length ? currentIndex + 1 : 0} di {studyDeck.length}
          </span>
        }
      />

      {card ? (
        <div className={styles.arena}>
          <div className={styles.card} onClick={() => setIsFlipped((f) => !f)}>
            <div className={`${styles.cardInner} ${isFlipped ? styles.flipped : ''}`}>
              <div className={`${styles.face} ${styles.front}`}>
                <div className={styles.cardText}>{card.question}</div>
                <div className={styles.cardHint}>Tocca la carta per rivelare la risposta</div>
              </div>
              <div className={`${styles.face} ${styles.back}`}>
                <div className={styles.cardText}>{card.answer}</div>
                <div className={styles.cardHint}>Quanto ricordavi bene questo concetto?</div>
              </div>
            </div>
          </div>

          {isFlipped && (
            <div className={styles.reviewButtons}>
              {RATINGS.map((r) => (
                <button
                  key={r.value}
                  className={styles.reviewBtn}
                  style={{ background: r.color }}
                  onClick={() => handleReview(r.value)}
                >
                  {r.label}
                </button>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <h2>Nessuna carta in questo deck per oggi!</h2>
          <Button onClick={() => navigate(`/subjects/${subjectId}/flashcards`)}>
            Torna alla materia
          </Button>
        </div>
      )}
    </div>
  );
}
