import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { fileKeys } from '../../../api/files';

export interface QueueItem {
  id: string;
  name: string;
  status: 'uploading' | 'done' | 'error';
  progress: number;
  error: string | null;
}

function uploadWithProgress(
  subjectId: number,
  file: File,
  relativePath: string | undefined,
  parentFolderId: number | null,
  onProgress: (pct: number) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const form = new FormData();
    form.append('file', file);
    if (relativePath) form.append('relative_path', relativePath);
    if (parentFolderId != null) form.append('parent_folder_id', String(parentFolderId));

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `/api/study-agent/subjects/${subjectId}/upload`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        try {
          reject(new Error(JSON.parse(xhr.responseText)?.detail ?? xhr.statusText));
        } catch {
          reject(new Error(xhr.statusText || `HTTP ${xhr.status}`));
        }
      }
    };
    xhr.onerror = () => reject(new Error('Errore di rete durante il caricamento'));
    xhr.send(form);
  });
}

/** Manages a parallel upload queue with per-item progress for the Finder view. */
export function useUploadQueue(subjectId: number) {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const qc = useQueryClient();

  function patchItem(id: string, patch: Partial<QueueItem>) {
    setQueue((prev) => prev.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }

  async function uploadFiles(
    files: File[],
    parentFolderId: number | null,
    relativePaths?: Record<string, string>
  ) {
    const items: QueueItem[] = files.map((f) => ({
      id: `${f.name}-${Date.now()}-${Math.random()}`,
      name: f.name,
      status: 'uploading',
      progress: 0,
      error: null,
    }));
    setQueue((prev) => [...prev, ...items]);

    await Promise.all(
      files.map(async (file, idx) => {
        const item = items[idx];
        try {
          await uploadWithProgress(
            subjectId,
            file,
            relativePaths?.[file.name],
            parentFolderId,
            (pct) => patchItem(item.id, { progress: pct })
          );
          patchItem(item.id, { status: 'done', progress: 100 });
        } catch (e) {
          patchItem(item.id, { status: 'error', error: (e as Error).message });
        }
      })
    );

    qc.invalidateQueries({ queryKey: fileKeys.folders(subjectId) });
    qc.invalidateQueries({ queryKey: fileKeys.documents(subjectId) });
  }

  function clearQueue() {
    setQueue([]);
  }

  return { queue, uploadFiles, clearQueue };
}
