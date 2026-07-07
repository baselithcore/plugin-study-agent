import { useState } from 'react';
import { Modal } from '../../components/Modal/Modal';
import { Button } from '../../components/Button/Button';
import { useCreateSubject } from '../../api/subjects';
import formStyles from '../../components/Form/Form.module.css';

export function AddSubjectModal({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const createSubject = useCreateSubject();

  const handleCreate = async () => {
    if (!name.trim()) return;
    await createSubject.mutateAsync({
      name: name.trim(),
      description: description.trim() || undefined,
    });
    onClose();
  };

  return (
    <Modal
      title="Aggiungi Nuova Materia"
      onClose={onClose}
      actions={
        <>
          <Button variant="secondary" onClick={onClose}>
            Annulla
          </Button>
          <Button onClick={handleCreate} disabled={!name.trim() || createSubject.isPending}>
            {createSubject.isPending ? 'Creazione...' : 'Crea Materia'}
          </Button>
        </>
      }
    >
      <div className={formStyles.group}>
        <label className={formStyles.label}>Nome della Materia d'Esame</label>
        <input
          className={formStyles.input}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Es. Analisi Matematica 1, Fisica 2, Programmazione"
          autoFocus
        />
      </div>
      <div className={formStyles.group}>
        <label className={formStyles.label}>Descrizione / Dettagli Corso (opzionale)</label>
        <textarea
          className={formStyles.textarea}
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Es. Limiti, derivate, integrali e serie numeriche. Prof. Neri."
        />
      </div>
    </Modal>
  );
}
