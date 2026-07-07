import { useRef, useState } from 'react';
import { EmptyState } from '../../../components/EmptyState/EmptyState';
import { Button } from '../../../components/Button/Button';
import { UploadIcon } from '../../../components/Icons';
import { useDocuments, useFolders, useBulkDelete } from '../../../api/files';
import { useCourseSubject } from '../useCourseSubject';
import { useFileManager } from './useFileManager';
import { useUploadQueue } from './useUploadQueue';
import { Toolbar } from './Toolbar';
import { FinderGrid } from './FinderGrid';
import { UploadQueue } from './UploadQueue';
import { CreateFolderModal } from './CreateFolderModal';
import { BulkMoveModal } from './BulkMoveModal';
import styles from './FilesTab.module.css';

export function FilesTab() {
  const { subjectId } = useCourseSubject();
  const { data: folders = [] } = useFolders(subjectId);
  const { data: documents = [] } = useDocuments(subjectId);
  const fm = useFileManager(folders, documents);
  const { queue, uploadFiles } = useUploadQueue(subjectId);
  const bulkDelete = useBulkDelete(subjectId);

  const [isDragging, setIsDragging] = useState(false);
  const dragCounter = useRef(0);
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [showBulkMove, setShowBulkMove] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const allSelected =
    fm.currentLevelFolders.length + fm.currentLevelDocuments.length > 0 &&
    fm.currentLevelFolders.every((f) => fm.selectedFolderIds.includes(f.id)) &&
    fm.currentLevelDocuments.every((d) => fm.selectedFileIds.includes(d.id));

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) uploadFiles(Array.from(e.target.files), fm.currentFolderId);
    e.target.value = '';
  };

  const handleFolderInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files?.length) return;
    const relativePaths: Record<string, string> = {};
    Array.from(files).forEach((f) => {
      const anyFile = f as File & { webkitRelativePath?: string };
      if (anyFile.webkitRelativePath) relativePaths[f.name] = anyFile.webkitRelativePath;
    });
    uploadFiles(Array.from(files), fm.currentFolderId, relativePaths);
    e.target.value = '';
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    dragCounter.current = 0;
    if (e.dataTransfer.files?.length) {
      uploadFiles(Array.from(e.dataTransfer.files), fm.currentFolderId);
    }
  };

  const handleBulkDelete = async () => {
    await bulkDelete.mutateAsync({
      document_ids: fm.selectedFileIds,
      folder_ids: fm.selectedFolderIds,
    });
    fm.clearSelection();
  };

  const hasContent = fm.currentLevelFolders.length > 0 || fm.currentLevelDocuments.length > 0;
  const hasSelection = fm.selectedFileIds.length + fm.selectedFolderIds.length > 0;

  return (
    <div
      className={`${styles.dropzoneWrapper} ${isDragging ? styles.active : ''}`}
      onDragEnter={(e) => {
        e.preventDefault();
        dragCounter.current += 1;
        setIsDragging(true);
      }}
      onDragOver={(e) => e.preventDefault()}
      onDragLeave={(e) => {
        e.preventDefault();
        dragCounter.current -= 1;
        if (dragCounter.current <= 0) setIsDragging(false);
      }}
      onDrop={handleDrop}
    >
      <Toolbar
        pathStack={fm.pathStack}
        onNavigateUp={fm.navigateUp}
        onNavigateToBreadcrumb={fm.navigateToBreadcrumb}
        onSelectAll={fm.toggleSelectAll}
        allSelected={allSelected}
        hasItems={hasContent}
        onCreateFolder={() => setShowCreateFolder(true)}
        onUploadFile={() => fileInputRef.current?.click()}
        onUploadFolder={() => folderInputRef.current?.click()}
      />

      <input
        ref={fileInputRef}
        type="file"
        style={{ display: 'none' }}
        multiple
        accept=".pdf,.docx,.pptx,.txt,.md,.png,.jpg,.jpeg,.webp"
        onChange={handleFileInputChange}
      />
      <input
        ref={folderInputRef}
        type="file"
        style={{ display: 'none' }}
        // @ts-expect-error non-standard directory-upload attributes
        webkitdirectory=""
        directory=""
        multiple
        onChange={handleFolderInputChange}
      />

      {isDragging && (
        <div className={styles.dragOverlay}>
          <div className={styles.dragMessage}>
            <UploadIcon />
            <p>Rilascia per caricare i file e le cartelle qui!</p>
          </div>
        </div>
      )}

      {hasSelection && (
        <div className={styles.bulkBar}>
          <span>
            {fm.selectedFileIds.length + fm.selectedFolderIds.length} elemento/i selezionato/i
          </span>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Button size="sm" variant="secondary" onClick={() => setShowBulkMove(true)}>
              Sposta
            </Button>
            <Button size="sm" variant="danger" onClick={handleBulkDelete}>
              Elimina
            </Button>
          </div>
        </div>
      )}

      <UploadQueue items={queue} />

      {hasContent ? (
        <FinderGrid
          subjectId={subjectId}
          folders={fm.currentLevelFolders}
          documents={fm.currentLevelDocuments}
          selectedFolderIds={fm.selectedFolderIds}
          selectedFileIds={fm.selectedFileIds}
          onToggleFolder={fm.toggleFolderSelection}
          onToggleFile={fm.toggleFileSelection}
          onOpenFolder={fm.navigateToFolder}
        />
      ) : (
        <EmptyState
          title="Questa cartella è vuota"
          description="Trascina qui i file o usa i pulsanti di caricamento in alto."
        />
      )}

      {showCreateFolder && (
        <CreateFolderModal
          subjectId={subjectId}
          parentId={fm.currentFolderId}
          onClose={() => setShowCreateFolder(false)}
        />
      )}
      {showBulkMove && (
        <BulkMoveModal
          subjectId={subjectId}
          documentIds={fm.selectedFileIds}
          folderIds={fm.selectedFolderIds}
          onDone={() => {
            setShowBulkMove(false);
            fm.clearSelection();
          }}
          onClose={() => setShowBulkMove(false)}
        />
      )}
    </div>
  );
}
