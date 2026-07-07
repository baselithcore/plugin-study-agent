import { useState } from 'react';
import { Modal } from '../../../../components/Modal/Modal';
import { Button } from '../../../../components/Button/Button';
import type { ConceptMapData } from '../../../../api/types';
import { useConceptMapLayout } from './useConceptMapLayout';
import { usePanZoom } from './usePanZoom';
import styles from './ConceptMap.module.css';

const WIDTH = 900;
const HEIGHT = 560;

export function ConceptMapModal({ data, onClose }: { data: ConceptMapData; onClose: () => void }) {
  const positions = useConceptMapLayout(data.nodes, WIDTH, HEIGHT);
  const panZoom = usePanZoom();
  const [selected, setSelected] = useState<string | null>(null);

  const selectedNode = selected ? positions.get(selected) : null;

  return (
    <Modal title="Mappa Relazionale Completa" onClose={onClose} wide>
      <div className={styles.toolbar}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
          Trascina per spostare la vista, rotellina per zoomare, clicca un nodo per i dettagli.
        </span>
        <Button size="sm" variant="secondary" onClick={panZoom.reset}>
          Reimposta vista
        </Button>
      </div>

      <div className={styles.workspace}>
        <div className={styles.sidebar}>
          <h4>Concetti ({data.nodes.length})</h4>
          {data.nodes.map((node) => (
            <div
              key={node.name}
              className={`${styles.nodeListItem} ${selected === node.name ? styles.active : ''}`}
              onClick={() => setSelected(node.name)}
            >
              {node.name}
            </div>
          ))}
          {selectedNode && (
            <div className={styles.infoPanel}>
              <div className={styles.title}>{selectedNode.name}</div>
              <p style={{ margin: 0, color: '#cbd5e1' }}>{selectedNode.definition}</p>
            </div>
          )}
        </div>

        <div
          className={styles.svgWrap}
          onWheel={panZoom.onWheel}
          onMouseDown={panZoom.onMouseDown}
          onMouseMove={panZoom.onMouseMove}
          onMouseUp={panZoom.onMouseUp}
          onMouseLeave={panZoom.onMouseUp}
        >
          <svg width="100%" height="500" viewBox={`0 0 ${WIDTH} ${HEIGHT}`}>
            <g transform={`translate(${panZoom.panX}, ${panZoom.panY}) scale(${panZoom.scale})`}>
              {data.edges.map((edge, idx) => {
                const source = positions.get(edge.source);
                const target = positions.get(edge.target);
                if (!source || !target) return null;
                return (
                  <line
                    key={idx}
                    className={styles.edge}
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                  />
                );
              })}
              {Array.from(positions.values()).map((node) => (
                <g
                  key={node.name}
                  className={styles.node}
                  transform={`translate(${node.x}, ${node.y})`}
                  onClick={() => setSelected(node.name)}
                >
                  <rect
                    x={-62}
                    y={-20}
                    width={124}
                    height={40}
                    rx={10}
                    className={`${styles.nodeRect} ${selected === node.name ? styles.active : ''}`}
                  />
                  <text
                    y={6}
                    className={`${styles.nodeText} ${selected === node.name ? styles.active : ''}`}
                  >
                    {node.name.length > 17 ? `${node.name.slice(0, 16)}…` : node.name}
                  </text>
                </g>
              ))}
            </g>
          </svg>
        </div>
      </div>
    </Modal>
  );
}
