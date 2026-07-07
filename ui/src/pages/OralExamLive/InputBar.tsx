import { useState } from 'react';
import { useAudioRecorder } from './useAudioRecorder';
import type { LiveMode } from './useLiveExam';
import styles from './InputBar.module.css';

interface InputBarProps {
  liveMode: LiveMode;
  disabled: boolean;
  onSubmitText: (text: string) => void;
  onSubmitAudio: (blob: Blob) => void;
}

export function InputBar({ liveMode, disabled, onSubmitText, onSubmitAudio }: InputBarProps) {
  const [text, setText] = useState('');
  const { isRecording, start, stop } = useAudioRecorder();

  const canListen = liveMode === 'listening' && !disabled;

  const handleMicClick = async () => {
    if (isRecording) {
      const blob = await stop();
      onSubmitAudio(blob);
    } else {
      await start();
    }
  };

  const handleSendText = () => {
    if (!text.trim()) return;
    onSubmitText(text.trim());
    setText('');
  };

  return (
    <div className={styles.inputArea}>
      <div className={`${styles.waveform} ${isRecording ? styles.active : ''}`}>
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className={styles.waveBar} />
        ))}
      </div>

      <div className={styles.micArea}>
        <div className={`${styles.micRing} ${isRecording ? styles.active : ''}`} />
        <div className={`${styles.micRing} ${styles.ring2} ${isRecording ? styles.active : ''}`} />
        <button
          className={`${styles.micBtn} ${isRecording ? styles.recording : ''}`}
          disabled={!canListen && !isRecording}
          onClick={handleMicClick}
        >
          {isRecording ? '⏹' : '🎙️'}
        </button>
      </div>

      <div className={styles.textRow}>
        <input
          className={styles.textInput}
          value={text}
          disabled={!canListen}
          placeholder="...oppure scrivi la tua risposta"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSendText()}
        />
        <button
          className={styles.sendBtn}
          disabled={!canListen || !text.trim()}
          onClick={handleSendText}
        >
          Invia
        </button>
      </div>
    </div>
  );
}
