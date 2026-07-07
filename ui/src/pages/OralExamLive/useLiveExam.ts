import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  useAnswerOralQuestion,
  useNextOralQuestion,
  useOralSession,
  useTranscribeAudio,
  sessionKeys,
} from '../../api/sessions';
import type { TranscriptBlock } from '../../api/types';

export type LiveMode = 'idle' | 'thinking' | 'speaking' | 'listening' | 'evaluating';

function playBase64Audio(base64: string): Promise<void> {
  return new Promise((resolve) => {
    const audio = new Audio(`data:audio/mp3;base64,${base64}`);
    audio.onended = () => resolve();
    audio.onerror = () => resolve();
    audio.play().catch(() => resolve());
  });
}

export function useLiveExam(subjectId: number, sessionId: number) {
  const qc = useQueryClient();
  const { data: session, isLoading } = useOralSession(sessionId);
  const nextQuestion = useNextOralQuestion();
  const answerQuestion = useAnswerOralQuestion();
  const transcribe = useTranscribeAudio();

  const [transcript, setTranscript] = useState<TranscriptBlock[]>([]);
  const [liveMode, setLiveMode] = useState<LiveMode>('idle');
  const [finished, setFinished] = useState<{ avgScore: number; finalGrade: string } | null>(null);
  const startedRef = useRef(false);

  useEffect(() => {
    if (session) setTranscript(session.transcript);
    if (session?.status === 'completed') {
      const finish = session.transcript.find((b) => b.type === 'system_finish');
      if (finish && finish.type === 'system_finish') {
        setFinished({ avgScore: finish.avg_score, finalGrade: finish.final_grade });
      }
    }
  }, [session]);

  const askNext = useCallback(async () => {
    setLiveMode('thinking');
    const result = await nextQuestion.mutateAsync(sessionId);
    if (result.status === 'completed') {
      setFinished({ avgScore: result.avg_score ?? 0, finalGrade: result.final_grade ?? '' });
      setTranscript((result.transcript as TranscriptBlock[]) ?? transcript);
      setLiveMode('idle');
      qc.invalidateQueries({ queryKey: sessionKeys.list(subjectId) });
      return;
    }
    setTranscript((prev) => [
      ...prev,
      {
        type: 'question',
        topic: result.topic ?? '',
        style: result.style ?? '',
        text: result.text ?? '',
      },
    ]);
    if (result.audio) {
      setLiveMode('speaking');
      await playBase64Audio(result.audio);
    }
    setLiveMode('listening');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nextQuestion, sessionId, subjectId, qc]);

  useEffect(() => {
    if (!startedRef.current && session && session.status === 'active' && transcript.length <= 1) {
      startedRef.current = true;
      askNext();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session]);

  const submitAnswer = useCallback(
    async (answerText: string) => {
      setLiveMode('evaluating');
      setTranscript((prev) => [...prev, { type: 'answer', text: answerText }]);
      const evalResult = await answerQuestion.mutateAsync({
        session_id: sessionId,
        answer_text: answerText,
      });
      setTranscript((prev) => [
        ...prev,
        {
          type: 'evaluation',
          topic: '',
          score: evalResult.score,
          feedback: evalResult.feedback,
          is_correct: evalResult.is_correct,
        },
      ]);
      await askNext();
    },
    [answerQuestion, askNext, sessionId]
  );

  const submitAudioAnswer = useCallback(
    async (blob: Blob) => {
      setLiveMode('evaluating');
      const { text } = await transcribe.mutateAsync(blob);
      await submitAnswer(text);
    },
    [submitAnswer, transcribe]
  );

  const topics = (() => {
    const systemBlock = transcript.find((b) => b.type === 'system');
    return systemBlock && systemBlock.type === 'system' ? systemBlock.topics : [];
  })();

  const doneTopics = new Set(
    transcript
      .filter((b): b is Extract<TranscriptBlock, { type: 'evaluation' }> => b.type === 'evaluation')
      .map((b) => b.topic)
  );

  const questionBlocks = transcript.filter(
    (b): b is Extract<TranscriptBlock, { type: 'question' }> => b.type === 'question'
  );
  const currentTopic = questionBlocks.length
    ? questionBlocks[questionBlocks.length - 1].topic
    : null;

  return {
    session,
    isLoading,
    transcript,
    liveMode,
    finished,
    topics,
    doneTopics,
    currentTopic,
    submitAnswer,
    submitAudioAnswer,
    isBusy: nextQuestion.isPending || answerQuestion.isPending || transcribe.isPending,
  };
}
