import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Modal } from '../../components/Modal/Modal';
import { Button } from '../../components/Button/Button';
import { useStartOralSession } from '../../api/sessions';
import formStyles from '../../components/Form/Form.module.css';

interface StartSessionModalProps {
  subjectId: number;
  onClose: () => void;
}

export function StartSessionModal({ subjectId, onClose }: StartSessionModalProps) {
  const [professorName, setProfessorName] = useState('Prof. Rossi');
  const [strictness, setStrictness] = useState<'amichevole' | 'equo' | 'scrupoloso'>('equo');
  const [difficulty, setDifficulty] = useState(3);
  const startSession = useStartOralSession();
  const navigate = useNavigate();

  const handleStart = async () => {
    const result = await startSession.mutateAsync({
      subject_id: subjectId,
      professor_name: professorName,
      strictness,
      difficulty_level: difficulty,
    });
    navigate(`/subjects/${subjectId}/oral-live?session=${result.session_id}`);
  };

  return (
    <Modal
      title="Avvia Interrogazione Orale"
      onClose={onClose}
      actions={
        <>
          <Button variant="secondary" onClick={onClose}>
            Annulla
          </Button>
          <Button onClick={handleStart} disabled={startSession.isPending}>
            {startSession.isPending ? 'Avvio...' : 'Inizia Esame'}
          </Button>
        </>
      }
    >
      <div className={formStyles.group}>
        <label className={formStyles.label}>Nome del Professore</label>
        <input
          className={formStyles.input}
          value={professorName}
          onChange={(e) => setProfessorName(e.target.value)}
        />
      </div>
      <div className={formStyles.group}>
        <label className={formStyles.label}>Carattere del Professore</label>
        <select
          className={formStyles.select}
          value={strictness}
          onChange={(e) => setStrictness(e.target.value as typeof strictness)}
        >
          <option value="amichevole">Amichevole</option>
          <option value="equo">Equo</option>
          <option value="scrupoloso">Scrupoloso</option>
        </select>
      </div>
      <div className={formStyles.group}>
        <label className={formStyles.label}>Difficoltà</label>
        <div className={formStyles.rangeRow}>
          <input
            type="range"
            min={1}
            max={5}
            value={difficulty}
            onChange={(e) => setDifficulty(Number(e.target.value))}
            style={{ flex: 1 }}
          />
          <span className={formStyles.rangeValue}>{difficulty}</span>
        </div>
      </div>
    </Modal>
  );
}
