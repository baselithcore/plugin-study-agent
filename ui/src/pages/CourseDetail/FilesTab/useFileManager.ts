import { useMemo, useState } from 'react';
import type { Folder, StudyDocument } from '../../../api/types';

export interface PathCrumb {
  id: number;
  name: string;
}

/** Local navigation + selection state for the Finder-like file browser. */
export function useFileManager(folders: Folder[], documents: StudyDocument[]) {
  const [currentFolderId, setCurrentFolderId] = useState<number | null>(null);
  const [pathStack, setPathStack] = useState<PathCrumb[]>([]);
  const [selectedFileIds, setSelectedFileIds] = useState<number[]>([]);
  const [selectedFolderIds, setSelectedFolderIds] = useState<number[]>([]);

  const currentLevelFolders = useMemo(
    () => folders.filter((f) => f.parent_id === currentFolderId),
    [folders, currentFolderId]
  );
  const currentLevelDocuments = useMemo(
    () => documents.filter((d) => d.folder_id === currentFolderId),
    [documents, currentFolderId]
  );

  function navigateToFolder(folder: Folder) {
    setPathStack((prev) => [...prev, { id: folder.id, name: folder.name }]);
    setCurrentFolderId(folder.id);
    clearSelection();
  }

  function navigateUp() {
    setPathStack((prev) => {
      const next = prev.slice(0, -1);
      setCurrentFolderId(next.length ? next[next.length - 1].id : null);
      return next;
    });
    clearSelection();
  }

  function navigateToBreadcrumb(index: number) {
    if (index < 0) {
      setPathStack([]);
      setCurrentFolderId(null);
    } else {
      setPathStack((prev) => {
        const next = prev.slice(0, index + 1);
        setCurrentFolderId(next[next.length - 1].id);
        return next;
      });
    }
    clearSelection();
  }

  function clearSelection() {
    setSelectedFileIds([]);
    setSelectedFolderIds([]);
  }

  function toggleFileSelection(id: number) {
    setSelectedFileIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  function toggleFolderSelection(id: number) {
    setSelectedFolderIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  function toggleSelectAll() {
    const allSelected =
      currentLevelFolders.every((f) => selectedFolderIds.includes(f.id)) &&
      currentLevelDocuments.every((d) => selectedFileIds.includes(d.id)) &&
      (currentLevelFolders.length > 0 || currentLevelDocuments.length > 0);
    if (allSelected) {
      clearSelection();
    } else {
      setSelectedFolderIds(currentLevelFolders.map((f) => f.id));
      setSelectedFileIds(currentLevelDocuments.map((d) => d.id));
    }
  }

  return {
    currentFolderId,
    pathStack,
    currentLevelFolders,
    currentLevelDocuments,
    selectedFileIds,
    selectedFolderIds,
    navigateToFolder,
    navigateUp,
    navigateToBreadcrumb,
    clearSelection,
    toggleFileSelection,
    toggleFolderSelection,
    toggleSelectAll,
  };
}
