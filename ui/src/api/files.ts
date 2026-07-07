import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type { Folder, StudyDocument } from './types';

export const fileKeys = {
  folders: (subjectId: number) => ['folders', subjectId] as const,
  documents: (subjectId: number) => ['documents', subjectId] as const,
};

export function useFolders(subjectId: number) {
  return useQuery({
    queryKey: fileKeys.folders(subjectId),
    queryFn: () => api.get<Folder[]>(`/subjects/${subjectId}/folders`),
    enabled: Number.isFinite(subjectId),
  });
}

export function useDocuments(subjectId: number) {
  return useQuery({
    queryKey: fileKeys.documents(subjectId),
    queryFn: () => api.get<StudyDocument[]>(`/subjects/${subjectId}/documents`),
    enabled: Number.isFinite(subjectId),
  });
}

function invalidateSubjectFiles(qc: ReturnType<typeof useQueryClient>, subjectId: number) {
  qc.invalidateQueries({ queryKey: fileKeys.folders(subjectId) });
  qc.invalidateQueries({ queryKey: fileKeys.documents(subjectId) });
}

export interface UploadResult {
  id: number;
  name: string;
  character_count: number;
  folder_id: number | null;
}

export function useUploadDocument(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      file,
      relativePath,
      parentFolderId,
    }: {
      file: File;
      relativePath?: string;
      parentFolderId?: number | null;
    }) => {
      const form = new FormData();
      form.append('file', file);
      if (relativePath) form.append('relative_path', relativePath);
      if (parentFolderId != null) form.append('parent_folder_id', String(parentFolderId));
      return api.postForm<UploadResult>(`/subjects/${subjectId}/upload`, form);
    },
    onSuccess: () => invalidateSubjectFiles(qc, subjectId),
  });
}

export function useDeleteDocument(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (docId: number) => api.delete(`/documents/${docId}`),
    onSuccess: () => invalidateSubjectFiles(qc, subjectId),
  });
}

export function useCreateFolder(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ name, parentId }: { name: string; parentId: number | null }) => {
      const form = new FormData();
      form.append('name', name);
      if (parentId != null) form.append('parent_id', String(parentId));
      return api.postForm<Folder>(`/subjects/${subjectId}/folders`, form);
    },
    onSuccess: () => invalidateSubjectFiles(qc, subjectId),
  });
}

export function useDeleteFolder(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (folderId: number) => api.delete(`/folders/${folderId}`),
    onSuccess: () => invalidateSubjectFiles(qc, subjectId),
  });
}

export function useRenameFolder(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ folderId, name }: { folderId: number; name: string }) =>
      api.put(`/folders/${folderId}`, { name }),
    onSuccess: () => invalidateSubjectFiles(qc, subjectId),
  });
}

export function useRenameDocument(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ docId, name }: { docId: number; name: string }) =>
      api.put(`/documents/${docId}`, { name }),
    onSuccess: () => invalidateSubjectFiles(qc, subjectId),
  });
}

export function useMoveDocument(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ docId, folderId }: { docId: number; folderId: number | null }) =>
      api.put(`/documents/${docId}`, { folder_id: folderId }),
    onSuccess: () => invalidateSubjectFiles(qc, subjectId),
  });
}

export function useMoveFolder(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ folderId, parentId }: { folderId: number; parentId: number | null }) =>
      api.put(`/folders/${folderId}/move`, { parent_id: parentId }),
    onSuccess: () => invalidateSubjectFiles(qc, subjectId),
  });
}

export interface BulkResult {
  success: boolean;
  deleted_documents?: number;
  deleted_folders?: number;
  moved_documents?: number;
  moved_folders?: number;
  failed_folders?: number[];
  message?: string;
}

export function useBulkDelete(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { document_ids: number[]; folder_ids: number[] }) =>
      api.post<BulkResult>(`/subjects/${subjectId}/bulk-delete`, payload),
    onSuccess: () => invalidateSubjectFiles(qc, subjectId),
  });
}

export function useBulkMove(subjectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      document_ids: number[];
      folder_ids: number[];
      target_folder_id: number | null;
    }) => api.post<BulkResult>(`/subjects/${subjectId}/bulk-move`, payload),
    onSuccess: () => invalidateSubjectFiles(qc, subjectId),
  });
}
