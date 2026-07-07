import { useState } from 'react';
import { Button } from '../../../../components/Button/Button';
import formStyles from '../../../../components/Form/Form.module.css';
import styles from './Podcast.module.css';

interface GenerateFormProps {
  onGenerate: (topic: string, depth: 'breve' | 'normale' | 'approfondito') => void;
  isGenerating: boolean;
}

export function GenerateForm({ onGenerate, isGenerating }: GenerateFormProps) {
  const [topic, setTopic] = useState('');
  const [depth, setDepth] = useState<'breve' | 'normale' | 'approfondito'>('normale');

  return (
    <div className={styles.generateForm}>
      <h4 style={{ margin: 0 }}>Genera un Nuovo Podcast Didattico</h4>
      <div className={styles.formRow}>
        <input
          className={formStyles.input}
          style={{ flex: 1, minWidth: 200 }}
          placeholder="Argomento del podcast"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        />
        <select
          className={formStyles.select}
          style={{ maxWidth: 180 }}
          value={depth}
          onChange={(e) => setDepth(e.target.value as typeof depth)}
        >
          <option value="breve">Breve (1 puntata)</option>
          <option value="normale">Normale (2 puntate)</option>
          <option value="approfondito">Approfondito (3-4 puntate)</option>
        </select>
        <Button onClick={() => onGenerate(topic, depth)} disabled={!topic.trim() || isGenerating}>
          {isGenerating ? 'Generazione...' : 'Genera'}
        </Button>
      </div>
    </div>
  );
}
