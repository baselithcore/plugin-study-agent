import { useEffect, useState } from 'react';
import { Button } from '../../../../components/Button/Button';
import { Tabs, type TabDef } from '../../../../components/Tabs/Tabs';
import { useDeconstructSubject } from '../../../../api/activeStudy';
import type { DeconstructedData } from '../../../../api/types';
import { CheatSheet } from './CheatSheet';
import { LikelyQuestions } from './LikelyQuestions';
import { MentalHooks } from './MentalHooks';
import { ConceptMapPreview } from './ConceptMapPreview';
import styles from './Deconstruct.module.css';

type SubTab = 'cheat' | 'questions' | 'hooks' | 'map';

const TABS: TabDef<SubTab>[] = [
  { id: 'cheat', label: 'Cheat Sheet' },
  { id: 'questions', label: 'Domande' },
  { id: 'hooks', label: 'Agganci' },
  { id: 'map', label: 'Mappa' },
];

export function DeconstructPanel({ subjectId }: { subjectId: number }) {
  const [tab, setTab] = useState<SubTab>('cheat');
  const [data, setData] = useState<DeconstructedData | null>(null);
  const deconstruct = useDeconstructSubject(subjectId);

  useEffect(() => {
    deconstruct.mutateAsync(false).then(setData);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subjectId]);

  const handleRefresh = async () => {
    const result = await deconstruct.mutateAsync(true);
    setData(result);
  };

  if (deconstruct.isPending && !data) {
    return <p style={{ color: 'var(--text-secondary)' }}>Analisi dei materiali in corso...</p>;
  }

  if (!data) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flexGrow: 1, minHeight: 0 }}>
      <div className={styles.toolbar}>
        <Tabs tabs={TABS} active={tab} onChange={setTab} variant="sub" />
        <Button
          size="sm"
          variant="secondary"
          onClick={handleRefresh}
          disabled={deconstruct.isPending}
        >
          {deconstruct.isPending ? 'Rigenerazione...' : 'Rigenera'}
        </Button>
      </div>
      <div className={styles.content}>
        {tab === 'cheat' && <CheatSheet items={data.cheat_sheet} />}
        {tab === 'questions' && <LikelyQuestions items={data.likely_questions} />}
        {tab === 'hooks' && <MentalHooks items={data.mental_hooks} />}
        {tab === 'map' && <ConceptMapPreview data={data.concept_map} />}
      </div>
    </div>
  );
}
