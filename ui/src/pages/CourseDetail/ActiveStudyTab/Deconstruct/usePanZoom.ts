import { useCallback, useRef, useState } from 'react';

/** Drag-to-pan + wheel-to-zoom state for an SVG viewport. */
export function usePanZoom() {
  const [scale, setScale] = useState(1);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);
  const isPanning = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    setScale((s) => Math.min(2.5, Math.max(0.4, s - e.deltaY * 0.001)));
  }, []);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    isPanning.current = true;
    lastPos.current = { x: e.clientX, y: e.clientY };
  }, []);

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isPanning.current) return;
    const dx = e.clientX - lastPos.current.x;
    const dy = e.clientY - lastPos.current.y;
    lastPos.current = { x: e.clientX, y: e.clientY };
    setPanX((x) => x + dx);
    setPanY((y) => y + dy);
  }, []);

  const onMouseUp = useCallback(() => {
    isPanning.current = false;
  }, []);

  const reset = useCallback(() => {
    setScale(1);
    setPanX(0);
    setPanY(0);
  }, []);

  return { scale, panX, panY, onWheel, onMouseDown, onMouseMove, onMouseUp, reset };
}
