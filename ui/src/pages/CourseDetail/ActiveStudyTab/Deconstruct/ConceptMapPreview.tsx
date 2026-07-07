import { useState } from 'react';
import { Button } from '../../../../components/Button/Button';
import type { ConceptMapData, ConceptMapEdge } from '../../../../api/types';
import { ConceptMapModal } from './ConceptMapModal';
import styles from './Deconstruct.module.css';

const RELATION_COLORS: Record<string, string> = {
  gerarchia: '#3b82f6',
  dipendenza: 'var(--purple)',
  contrasto: 'var(--danger)',
  implementa: 'var(--success)',
  esempio_di: 'var(--warning)',
  precede: '#14b8a6',
  causa: '#f97316',
  collegamento: 'var(--text-muted)',
};

function EdgeChip({ edge }: { edge: ConceptMapEdge }) {
  const color = RELATION_COLORS[edge.relation_type] ?? RELATION_COLORS.collegamento;
  return (
    <div className={styles.itemCard} style={{ cursor: 'default' }}>
      <span
        style={{
          background: color,
          color: '#fff',
          fontSize: '0.65rem',
          padding: '0.1rem 0.4rem',
          borderRadius: 4,
          fontWeight: 700,
          marginRight: '0.4rem',
        }}
      >
        {edge.relation_type}
      </span>
      {edge.source} &rarr; {edge.target}
      <p style={{ marginTop: '0.3rem' }}>{edge.relationship}</p>
    </div>
  );
}

export function ConceptMapPreview({ data }: { data: ConceptMapData | ConceptMapEdge[] }) {
  const [showModal, setShowModal] = useState(false);
  const normalized: ConceptMapData = Array.isArray(data) ? { nodes: [], edges: data } : data;

  if (!normalized.edges.length) {
    return <p style={{ color: 'var(--text-secondary)' }}>Nessuna mappa concettuale disponibile.</p>;
  }

  return (
    <div>
      {normalized.nodes.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <Button onClick={() => setShowModal(true)}>Apri Mappa Interattiva</Button>
        </div>
      )}
      <div className={styles.pane}>
        {normalized.edges.slice(0, 30).map((edge, idx) => (
          <EdgeChip key={idx} edge={edge} />
        ))}
      </div>
      {showModal && <ConceptMapModal data={normalized} onClose={() => setShowModal(false)} />}
    </div>
  );
}
