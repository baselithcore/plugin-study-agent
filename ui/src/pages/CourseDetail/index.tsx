import { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { PageHeader } from '../../components/PageHeader/PageHeader';
import { Button } from '../../components/Button/Button';
import { Tabs, type TabDef } from '../../components/Tabs/Tabs';
import { ConfirmDialog } from '../../components/ConfirmDialog/ConfirmDialog';
import {
  ChatIcon,
  MicIcon,
  FolderIcon,
  FlashcardsIcon,
  BookIcon,
  LightbulbIcon,
} from '../../components/Icons';
import { useDeleteSubject } from '../../api/subjects';
import { useCourseSubject } from './useCourseSubject';
import { StartSessionModal } from './StartSessionModal';
import styles from './CourseDetail.module.css';

type TabId = 'files' | 'flashcards' | 'oral-history' | 'active-study';

const TABS: TabDef<TabId>[] = [
  {
    id: 'files',
    label: (
      <span className={styles.actionIcon}>
        <FolderIcon className={styles.icon} /> Materiali Didattici
      </span>
    ),
  },
  {
    id: 'flashcards',
    label: (
      <span className={styles.actionIcon}>
        <FlashcardsIcon className={styles.icon} /> Flashcards
      </span>
    ),
  },
  {
    id: 'oral-history',
    label: (
      <span className={styles.actionIcon}>
        <BookIcon className={styles.icon} /> Storico Interrogazioni
      </span>
    ),
  },
  {
    id: 'active-study',
    label: (
      <span className={styles.actionIcon}>
        <LightbulbIcon className={styles.icon} /> Studio Attivo (Feynman, Decostruttore &amp;
        Podcast)
      </span>
    ),
  },
];

export function CourseDetail() {
  const { subjectId, subject, isLoading } = useCourseSubject();
  const navigate = useNavigate();
  const location = useLocation();
  const deleteSubject = useDeleteSubject();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [showStartSession, setShowStartSession] = useState(false);

  const activeTab: TabId = (TABS.find((t) => location.pathname.includes(`/${t.id}`))?.id ??
    'files') as TabId;

  if (isLoading) return null;
  if (!subject) {
    return (
      <div className={styles.container}>
        <p>Materia non trovata.</p>
        <Button variant="secondary" onClick={() => navigate('/')}>
          Torna alle materie
        </Button>
      </div>
    );
  }

  const handleDelete = async () => {
    await deleteSubject.mutateAsync(subjectId);
    navigate('/');
  };

  return (
    <div className={styles.container}>
      <PageHeader
        title={subject.name}
        description={subject.description || 'Dettagli e strumenti di studio'}
        backLabel="Torna alle materie"
        onBack={() => navigate('/')}
        actions={
          <>
            <Button variant="secondary" onClick={() => navigate(`/subjects/${subjectId}/chat`)}>
              <ChatIcon className={styles.icon} /> Chiedi all'Assistente
            </Button>
            <Button onClick={() => setShowStartSession(true)}>
              <MicIcon className={styles.icon} /> Avvia Interrogazione
            </Button>
            <Button variant="danger" onClick={() => setConfirmDelete(true)}>
              Elimina Materia
            </Button>
          </>
        }
      />

      <div className={styles.detailsContainer}>
        <Tabs
          tabs={TABS}
          active={activeTab}
          onChange={(id) => navigate(`/subjects/${subjectId}/${id}`)}
        />
        <Outlet context={{ subjectId, subject }} />
      </div>

      {confirmDelete && (
        <ConfirmDialog
          title="Elimina Materia"
          message={`Sei sicuro di voler eliminare "${subject.name}"? Tutti i materiali, flashcard e sessioni collegate verranno eliminati permanentemente.`}
          confirmLabel="Elimina"
          onConfirm={handleDelete}
          onCancel={() => setConfirmDelete(false)}
        />
      )}

      {showStartSession && (
        <StartSessionModal subjectId={subjectId} onClose={() => setShowStartSession(false)} />
      )}
    </div>
  );
}
