import { useState } from 'react';
import { Modal } from '../../../components/Modal/Modal';
import { Button } from '../../../components/Button/Button';
import { useCreateFolder } from '../../../api/files';
import formStyles from '../../../components/Form/Form.module.css';

interface CreateFolderModalProps {
  subjectId: number;
  parentId: number | null;
  onClose: () => void;
}

export function CreateFolderModal({ subjectId, parentId, onClose }: CreateFolderModalProps) {
  const [name, setName] = useState('');
  const createFolder = useCreateFolder(subjectId);

  const handleCreate = async () => {
    if (!name.trim()) return;
    await createFolder.mutateAsync({ name: name.trim(), parentId });
    onClose();
  };

  return (
    <Modal
      title="Nuova Cartella"
      onClose={onClose}
      actions={
        <>
          <Button variant="secondary" onClick={onClose}>
            Annulla
          </Button>
          <Button onClick={handleCreate} disabled={!name.trim() || createFolder.isPending}>
            Crea
          </Button>
        </>
      }
    >
      <div className={formStyles.group}>
        <label className={formStyles.label}>Nome cartella</label>
        <input
          className={formStyles.input}
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
          autoFocus
        />
      </div>
    </Modal>
  );
}
