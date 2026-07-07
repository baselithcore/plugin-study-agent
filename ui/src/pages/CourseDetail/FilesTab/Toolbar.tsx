import { Button } from '../../../components/Button/Button';
import type { PathCrumb } from './useFileManager';
import styles from './FilesTab.module.css';

interface ToolbarProps {
  pathStack: PathCrumb[];
  onNavigateUp: () => void;
  onNavigateToBreadcrumb: (index: number) => void;
  onSelectAll: () => void;
  allSelected: boolean;
  hasItems: boolean;
  onCreateFolder: () => void;
  onUploadFile: () => void;
  onUploadFolder: () => void;
}

export function Toolbar({
  pathStack,
  onNavigateUp,
  onNavigateToBreadcrumb,
  onSelectAll,
  allSelected,
  hasItems,
  onCreateFolder,
  onUploadFile,
  onUploadFolder,
}: ToolbarProps) {
  return (
    <div className={styles.toolbar}>
      <div className={styles.navigation}>
        <Button
          variant="secondary"
          size="sm"
          disabled={pathStack.length === 0}
          onClick={onNavigateUp}
        >
          &larr; Indietro
        </Button>
        <div className={styles.breadcrumbs}>
          <span className={styles.crumb} onClick={() => onNavigateToBreadcrumb(-1)}>
            Root
          </span>
          {pathStack.map((crumb, idx) => (
            <span key={crumb.id}>
              <span className={styles.separator}>/</span>
              <span
                className={`${styles.crumb} ${idx === pathStack.length - 1 ? styles.current : ''}`}
                onClick={() => onNavigateToBreadcrumb(idx)}
              >
                {crumb.name}
              </span>
            </span>
          ))}
        </div>
      </div>

      <div className={styles.actions}>
        {hasItems && (
          <Button variant="secondary" size="sm" onClick={onSelectAll}>
            {allSelected ? 'Deseleziona' : 'Seleziona Tutto'}
          </Button>
        )}
        <Button variant="secondary" size="sm" onClick={onCreateFolder}>
          Nuova Cartella
        </Button>
        <Button variant="secondary" size="sm" onClick={onUploadFolder}>
          Carica Cartella
        </Button>
        <Button size="sm" onClick={onUploadFile}>
          Carica File
        </Button>
      </div>
    </div>
  );
}
