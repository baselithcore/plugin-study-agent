import { useState } from 'react';
import { Modal } from '../../../components/Modal/Modal';
import { Button } from '../../../components/Button/Button';
import { useBulkMove, useFolders } from '../../../api/files';
import formStyles from '../../../components/Form/Form.module.css';

interface BulkMoveModalProps {
  subjectId: number;
  documentIds: number[];
  folderIds: number[];
  onDone: () => void;
  onClose: () => void;
}

export function BulkMoveModal({
  subjectId,
  documentIds,
  folderIds,
  onDone,
  onClose,
}: BulkMoveModalProps) {
  const { data: folders } = useFolders(subjectId);
  const [target, setTarget] = useState<string>('');
  const bulkMove = useBulkMove(subjectId);
  const [error, setError] = useState<string | null>(null);

  const handleMove = async () => {
    setError(null);
    try {
      const result = await bulkMove.mutateAsync({
        document_ids: documentIds,
        folder_ids: folderIds,
        target_folder_id: target ? Number(target) : null,
      });
      if (result.failed_folders?.length) {
        setError(result.message ?? 'Alcune cartelle non sono state spostate (possibile ciclo).');
      } else {
        onDone();
      }
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <Modal
      title="Sposta elementi"
      onClose={onClose}
      actions={
        <>
          <Button variant="secondary" onClick={onClose}>
            Annulla
          </Button>
          <Button onClick={handleMove} disabled={bulkMove.isPending}>
            Sposta
          </Button>
        </>
      }
    >
      <div className={formStyles.group}>
        <label className={formStyles.label}>Cartella di destinazione</label>
        <select
          className={formStyles.select}
          value={target}
          onChange={(e) => setTarget(e.target.value)}
        >
          <option value="">Root</option>
          {(folders ?? [])
            .filter((f) => !folderIds.includes(f.id))
            .map((f) => (
              <option key={f.id} value={f.id}>
                {f.name}
              </option>
            ))}
        </select>
      </div>
      {error && <p style={{ color: 'var(--danger-light)', fontSize: '0.85rem' }}>{error}</p>}
    </Modal>
  );
}
