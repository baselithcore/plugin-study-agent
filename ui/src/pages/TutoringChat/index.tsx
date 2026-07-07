import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { PageHeader } from '../../components/PageHeader/PageHeader';
import { Button } from '../../components/Button/Button';
import { useSubjects } from '../../api/subjects';
import { useAskTutor } from '../../api/chat';
import type { ChatMessage } from '../../api/types';
import { renderMarkdownLite } from '../../lib/markdownLite';
import styles from './TutoringChat.module.css';

export function TutoringChat() {
  const { subjectId: subjectIdParam } = useParams<{ subjectId: string }>();
  const subjectId = Number(subjectIdParam);
  const navigate = useNavigate();
  const { data: subjects } = useSubjects();
  const subject = subjects?.find((s) => s.id === subjectId);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [query, setQuery] = useState('');
  const askTutor = useAskTutor(subjectId);

  const handleSend = async () => {
    if (!query.trim() || askTutor.isPending) return;
    const userMessage: ChatMessage = { role: 'user', text: query.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setQuery('');
    const result = await askTutor.mutateAsync(userMessage.text);
    setMessages((prev) => [
      ...prev,
      { role: 'assistant', text: result.answer, sources: result.sources_used },
    ]);
  };

  return (
    <div className={styles.container}>
      <PageHeader
        title={`Assistente Studio: ${subject?.name ?? ''}`}
        description="Fai domande sugli argomenti dei file caricati o chiedi aiuto nello svolgimento degli esercizi."
        backLabel="Torna alla materia"
        onBack={() => navigate(`/subjects/${subjectId}`)}
      />

      <div className={styles.board}>
        <div className={styles.messages}>
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`${styles.msg} ${msg.role === 'user' ? styles.student : styles.professor}`}
            >
              <strong>{msg.role === 'user' ? 'Tu' : 'Assistente'}:</strong>
              {renderMarkdownLite(msg.text)}
              {msg.sources && msg.sources.length > 0 && (
                <div className={styles.sources}>Fonti utilizzate: {msg.sources.join(', ')}</div>
              )}
            </div>
          ))}
          {askTutor.isPending && (
            <div className={`${styles.msg} ${styles.professor}`}>
              <span>Elaborazione risposta in corso...</span>
            </div>
          )}
        </div>

        <div className={styles.inputBar}>
          <input
            type="text"
            className={styles.input}
            value={query}
            placeholder="Chiedi spiegazioni, formule o come risolvere un problema..."
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <Button onClick={handleSend} disabled={!query.trim() || askTutor.isPending}>
            Invia
          </Button>
        </div>
      </div>
    </div>
  );
}
