import { useState } from 'react';
import { Button } from '../../../../components/Button/Button';
import {
  useFeynmanConcept,
  useFeynmanRespond,
  type FeynmanHistoryItem,
} from '../../../../api/activeStudy';
import type { FeynmanEvaluation } from '../../../../api/types';
import styles from './Feynman.module.css';

interface FeynmanMessage {
  role: 'assistant' | 'student';
  text: string;
  evaluation?: FeynmanEvaluation;
}

export function FeynmanPanel({ subjectId }: { subjectId: number }) {
  const [started, setStarted] = useState(false);
  const [customConcept, setCustomConcept] = useState('');
  const { data: conceptData, isFetching: loadingConcept } = useFeynmanConcept(subjectId, started);
  const [concept, setConcept] = useState<string | null>(null);
  const [messages, setMessages] = useState<FeynmanMessage[]>([]);
  const [input, setInput] = useState('');
  const respond = useFeynmanRespond();

  const handleStart = () => {
    setStarted(true);
    setConcept(customConcept.trim() || null);
  };

  const activeConcept = concept ?? conceptData?.concept ?? '';

  const handleSend = async () => {
    if (!input.trim() || !activeConcept) return;
    const explanation = input.trim();
    setMessages((prev) => [...prev, { role: 'student', text: explanation }]);
    setInput('');

    const history: FeynmanHistoryItem[] = messages.map((m) => ({ role: m.role, text: m.text }));
    const evaluation = await respond.mutateAsync({
      subjectId,
      conceptName: activeConcept,
      explanation,
      history,
    });
    setMessages((prev) => [
      ...prev,
      { role: 'assistant', text: evaluation.domanda_followup, evaluation },
    ]);
  };

  if (!started || (loadingConcept && !concept)) {
    return (
      <div className={styles.startPanel}>
        <p>
          Il metodo Feynman ti aiuta a capire davvero un concetto spiegandolo con parole semplici,
          come lo spiegheresti a un bambino di 10 anni.
        </p>
        <input
          className={styles.textInput}
          style={{ flex: 'none', width: '100%', maxWidth: 360, marginBottom: '1rem' }}
          placeholder="Concetto specifico (opzionale, altrimenti lo sceglie l'AI)"
          value={customConcept}
          onChange={(e) => setCustomConcept(e.target.value)}
        />
        <Button onClick={handleStart} disabled={loadingConcept}>
          {loadingConcept ? 'Scelta del concetto...' : 'Inizia'}
        </Button>
      </div>
    );
  }

  return (
    <div className={styles.workspace}>
      <div className={styles.conceptBadge}>Concetto: {activeConcept}</div>
      <div className={styles.feed}>
        <div className={styles.msgRow}>
          <div className={`${styles.bubble} ${styles.assistantBubble}`}>
            <div className={styles.assistantLabel}>Tutor</div>
            Prova a spiegarmi "{activeConcept}" come se parlassi a un amico che non conosce
            l'argomento.
          </div>
        </div>
        {messages.map((m, idx) =>
          m.role === 'student' ? (
            <div key={idx} className={`${styles.msgRow} ${styles.student}`}>
              <div className={`${styles.bubble} ${styles.studentBubble}`}>
                <div className={styles.studentLabel}>Tu</div>
                {m.text}
              </div>
            </div>
          ) : (
            <div key={idx} className={styles.msgRow}>
              <div className={`${styles.bubble} ${styles.assistantBubble}`}>
                <div className={styles.assistantLabel}>Tutor</div>
                {m.evaluation && (
                  <div className={styles.evalCards}>
                    {m.evaluation.punti_di_forza.length > 0 && (
                      <div className={`${styles.evalCard} ${styles.strengths}`}>
                        <strong>Punti di forza</strong>
                        <ul>
                          {m.evaluation.punti_di_forza.map((p, i) => (
                            <li key={i}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {m.evaluation.lacune.length > 0 && (
                      <div className={`${styles.evalCard} ${styles.gaps}`}>
                        <strong>Lacune</strong>
                        <ul>
                          {m.evaluation.lacune.map((p, i) => (
                            <li key={i}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {m.evaluation.inesattezze.length > 0 && (
                      <div className={`${styles.evalCard} ${styles.errors}`}>
                        <strong>Inesattezze</strong>
                        <ul>
                          {m.evaluation.inesattezze.map((p, i) => (
                            <li key={i}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <div className={`${styles.evalCard} ${styles.analogy}`}>
                      <strong>Analogia</strong>
                      <p>{m.evaluation.analogia}</p>
                    </div>
                  </div>
                )}
                <p style={{ marginTop: '0.6rem' }}>{m.text}</p>
              </div>
            </div>
          )
        )}
        {respond.isPending && (
          <div className={styles.loading}>Il tutor sta valutando la tua spiegazione...</div>
        )}
      </div>
      <div className={styles.inputRow}>
        <input
          className={styles.textInput}
          value={input}
          placeholder="Spiega il concetto con parole tue..."
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          disabled={respond.isPending}
        />
        <Button onClick={handleSend} disabled={respond.isPending || !input.trim()}>
          Invia
        </Button>
      </div>
    </div>
  );
}
