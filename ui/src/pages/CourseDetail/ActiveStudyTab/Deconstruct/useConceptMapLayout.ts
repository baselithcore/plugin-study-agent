import { useMemo } from 'react';
import type { ConceptMapNode } from '../../../../api/types';

export interface LayoutNode extends ConceptMapNode {
  x: number;
  y: number;
}

/** Deterministic layout: clusters arranged in a ring, nodes arranged in a ring within each cluster. */
export function useConceptMapLayout(nodes: ConceptMapNode[], width: number, height: number) {
  return useMemo(() => {
    const clusters = Array.from(new Set(nodes.map((n) => n.cluster)));
    const clusterRadius = Math.min(width, height) * 0.32;
    const centerX = width / 2;
    const centerY = height / 2;

    const positions = new Map<string, LayoutNode>();

    clusters.forEach((cluster, ci) => {
      const clusterAngle = (2 * Math.PI * ci) / clusters.length;
      const clusterCx = centerX + clusterRadius * Math.cos(clusterAngle);
      const clusterCy = centerY + clusterRadius * Math.sin(clusterAngle);

      const clusterNodes = nodes.filter((n) => n.cluster === cluster);
      const nodeRadius = 60 + clusterNodes.length * 6;

      clusterNodes.forEach((node, ni) => {
        const angle = (2 * Math.PI * ni) / Math.max(clusterNodes.length, 1);
        const x = clusterCx + nodeRadius * Math.cos(angle);
        const y = clusterCy + nodeRadius * Math.sin(angle);
        positions.set(node.name, { ...node, x, y });
      });
    });

    return positions;
  }, [nodes, width, height]);
}
