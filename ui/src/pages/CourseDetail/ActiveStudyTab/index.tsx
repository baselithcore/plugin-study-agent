import { useNavigate, useParams } from 'react-router-dom';
import { Tabs, type TabDef } from '../../../components/Tabs/Tabs';
import { useCourseSubject } from '../useCourseSubject';
import { FeynmanPanel } from './Feynman/FeynmanPanel';
import { DeconstructPanel } from './Deconstruct/DeconstructPanel';
import { PodcastPanel } from './Podcast/PodcastPanel';
import styles from './ActiveStudyTab.module.css';

type Tool = 'feynman' | 'deconstruct' | 'podcast';

const TOOLS: TabDef<Tool>[] = [
  { id: 'feynman', label: 'Metodo Feynman' },
  { id: 'deconstruct', label: 'Decostruttore' },
  { id: 'podcast', label: 'Podcast Didattico' },
];

const TITLES: Record<Tool, { title: string; description: string }> = {
  feynman: {
    title: 'Metodo di Feynman (Spiegazione Attiva)',
    description:
      'Spiega un concetto con parole semplici, come lo spiegheresti a un bambino di 10 anni.',
  },
  deconstruct: {
    title: 'Decostruttore di Concetti (Studio Rapido)',
    description:
      'Cheat sheet, domande probabili, agganci mnemonici e mappa concettuale generati dai materiali.',
  },
  podcast: {
    title: 'Podcast Didattico (Lezioni Audio a Puntate)',
    description: "Genera un podcast a puntate sull'argomento che vuoi approfondire.",
  },
};

export function ActiveStudyTab() {
  const { subjectId } = useCourseSubject();
  const { tool } = useParams<{ tool: string }>();
  const navigate = useNavigate();
  const activeTool = (tool as Tool) ?? 'feynman';

  return (
    <div>
      <Tabs
        tabs={TOOLS}
        active={activeTool}
        onChange={(id) => navigate(`/subjects/${subjectId}/active-study/${id}`)}
        variant="sub"
      />

      <div className={styles.layout}>
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <h3>{TITLES[activeTool].title}</h3>
            <p>{TITLES[activeTool].description}</p>
          </div>
          {activeTool === 'feynman' && <FeynmanPanel subjectId={subjectId} />}
          {activeTool === 'deconstruct' && <DeconstructPanel subjectId={subjectId} />}
          {activeTool === 'podcast' && <PodcastPanel subjectId={subjectId} />}
        </div>
      </div>
    </div>
  );
}
