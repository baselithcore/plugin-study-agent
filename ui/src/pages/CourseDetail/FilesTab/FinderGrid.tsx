import { useState } from 'react';
import type { Folder, StudyDocument } from '../../../api/types';
import { FolderIcon, DocumentIcon, PencilIcon, CloseIcon } from '../../../components/Icons';
import {
  useDeleteDocument,
  useDeleteFolder,
  useMoveDocument,
  useMoveFolder,
  useRenameDocument,
  useRenameFolder,
} from '../../../api/files';
import styles from './FilesTab.module.css';

interface FinderGridProps {
  subjectId: number;
  folders: Folder[];
  documents: StudyDocument[];
  selectedFolderIds: number[];
  selectedFileIds: number[];
  onToggleFolder: (id: number) => void;
  onToggleFile: (id: number) => void;
  onOpenFolder: (folder: Folder) => void;
}

type DragPayload = { kind: 'folder' | 'document'; id: number };

export function FinderGrid({
  subjectId,
  folders,
  documents,
  selectedFolderIds,
  selectedFileIds,
  onToggleFolder,
  onToggleFile,
  onOpenFolder,
}: FinderGridProps) {
  const [renamingFolderId, setRenamingFolderId] = useState<number | null>(null);
  const [renamingDocId, setRenamingDocId] = useState<number | null>(null);
  const [draftName, setDraftName] = useState('');

  const deleteFolder = useDeleteFolder(subjectId);
  const deleteDocument = useDeleteDocument(subjectId);
  const renameFolder = useRenameFolder(subjectId);
  const renameDocument = useRenameDocument(subjectId);
  const moveFolder = useMoveFolder(subjectId);
  const moveDocument = useMoveDocument(subjectId);

  const commitRenameFolder = (id: number) => {
    if (draftName.trim()) renameFolder.mutate({ folderId: id, name: draftName.trim() });
    setRenamingFolderId(null);
  };
  const commitRenameDoc = (id: number) => {
    if (draftName.trim()) renameDocument.mutate({ docId: id, name: draftName.trim() });
    setRenamingDocId(null);
  };

  const handleDropOnFolder = (targetFolderId: number, e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const raw = e.dataTransfer.getData('application/json');
    if (!raw) return;
    const payload = JSON.parse(raw) as DragPayload;
    if (payload.kind === 'folder' && payload.id !== targetFolderId) {
      moveFolder.mutate({ folderId: payload.id, parentId: targetFolderId });
    } else if (payload.kind === 'document') {
      moveDocument.mutate({ docId: payload.id, folderId: targetFolderId });
    }
  };

  return (
    <div className={styles.grid}>
      {folders.map((folder) => (
        <div
          key={`folder-${folder.id}`}
          className={`${styles.item} ${selectedFolderIds.includes(folder.id) ? styles.selected : ''}`}
          draggable
          onDragStart={(e) =>
            e.dataTransfer.setData(
              'application/json',
              JSON.stringify({ kind: 'folder', id: folder.id })
            )
          }
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => handleDropOnFolder(folder.id, e)}
          onClick={() => renamingFolderId !== folder.id && onOpenFolder(folder)}
        >
          <input
            type="checkbox"
            className={styles.itemCheckbox}
            checked={selectedFolderIds.includes(folder.id)}
            onClick={(e) => e.stopPropagation()}
            onChange={() => onToggleFolder(folder.id)}
          />
          <FolderIcon className={styles.itemIcon} />
          {renamingFolderId === folder.id ? (
            <input
              className={styles.renameInput}
              value={draftName}
              autoFocus
              onClick={(e) => e.stopPropagation()}
              onChange={(e) => setDraftName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && commitRenameFolder(folder.id)}
              onBlur={() => commitRenameFolder(folder.id)}
            />
          ) : (
            <span className={styles.itemName}>{folder.name}</span>
          )}
          <div className={styles.itemActions}>
            <button
              className={styles.actionBtn}
              title="Rinomina"
              onClick={(e) => {
                e.stopPropagation();
                setRenamingFolderId(folder.id);
                setDraftName(folder.name);
              }}
            >
              <PencilIcon />
            </button>
            <button
              className={styles.actionBtn}
              title="Elimina"
              onClick={(e) => {
                e.stopPropagation();
                deleteFolder.mutate(folder.id);
              }}
            >
              <CloseIcon />
            </button>
          </div>
        </div>
      ))}

      {documents.map((doc) => (
        <div
          key={`doc-${doc.id}`}
          className={`${styles.item} ${selectedFileIds.includes(doc.id) ? styles.selected : ''}`}
          draggable
          onDragStart={(e) =>
            e.dataTransfer.setData(
              'application/json',
              JSON.stringify({ kind: 'document', id: doc.id })
            )
          }
        >
          <input
            type="checkbox"
            className={styles.itemCheckbox}
            checked={selectedFileIds.includes(doc.id)}
            onClick={(e) => e.stopPropagation()}
            onChange={() => onToggleFile(doc.id)}
          />
          <DocumentIcon className={styles.itemIcon} />
          {renamingDocId === doc.id ? (
            <input
              className={styles.renameInput}
              value={draftName}
              autoFocus
              onChange={(e) => setDraftName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && commitRenameDoc(doc.id)}
              onBlur={() => commitRenameDoc(doc.id)}
            />
          ) : (
            <span className={styles.itemName} title={doc.name}>
              {doc.name}
            </span>
          )}
          <div className={styles.itemActions}>
            <button
              className={styles.actionBtn}
              title="Rinomina"
              onClick={() => {
                setRenamingDocId(doc.id);
                setDraftName(doc.name);
              }}
            >
              <PencilIcon />
            </button>
            <button
              className={styles.actionBtn}
              title="Elimina"
              onClick={() => deleteDocument.mutate(doc.id)}
            >
              <CloseIcon />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
