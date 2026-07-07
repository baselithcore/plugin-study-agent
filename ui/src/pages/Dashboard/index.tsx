import { useState } from 'react';
import { PageHeader } from '../../components/PageHeader/PageHeader';
import { Button } from '../../components/Button/Button';
import { EmptyState } from '../../components/EmptyState/EmptyState';
import { useSubjects } from '../../api/subjects';
import { SubjectCard } from './SubjectCard';
import { AddSubjectModal } from './AddSubjectModal';
import styles from './Dashboard.module.css';

export function Dashboard() {
  const { data: subjects, isLoading } = useSubjects();
  const [showAddModal, setShowAddModal] = useState(false);

  return (
    <div className={styles.container}>
      <PageHeader
        title="Assistente Studio &amp; Esami"
        description="Crea agenti per ogni materia, carica appunti, studia con flashcards e simula interrogazioni orali."
        actions={<Button onClick={() => setShowAddModal(true)}>+ Aggiungi Materia</Button>}
      />

      {!isLoading && subjects && subjects.length > 0 && (
        <div className={styles.grid}>
          {subjects.map((subject) => (
            <SubjectCard key={subject.id} subject={subject} />
          ))}
        </div>
      )}

      {!isLoading && (!subjects || subjects.length === 0) && (
        <EmptyState
          title="Nessuna materia registrata"
          description="Inizia creando una materia d'esame e caricando appunti, dispense o foto di esami."
          action={<Button onClick={() => setShowAddModal(true)}>Crea la tua prima materia</Button>}
        />
      )}

      {showAddModal && <AddSubjectModal onClose={() => setShowAddModal(false)} />}
    </div>
  );
}
