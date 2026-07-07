import { Navigate, Route, Routes } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { CourseDetail } from './pages/CourseDetail';
import { FilesTab } from './pages/CourseDetail/FilesTab';
import { FlashcardsTab } from './pages/CourseDetail/FlashcardsTab';
import { OralHistoryTab } from './pages/CourseDetail/OralHistoryTab';
import { ActiveStudyTab } from './pages/CourseDetail/ActiveStudyTab';
import { FlashcardStudy } from './pages/FlashcardStudy';
import { OralExamLive } from './pages/OralExamLive';
import { TutoringChat } from './pages/TutoringChat';
import { DebugPanel } from './pages/DebugPanel';

export function App() {
  return (
    <div className="study-agent-app">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/subjects/:subjectId" element={<CourseDetail />}>
          <Route index element={<Navigate to="files" replace />} />
          <Route path="files" element={<FilesTab />} />
          <Route path="flashcards" element={<FlashcardsTab />} />
          <Route path="oral-history" element={<OralHistoryTab />} />
          <Route path="active-study" element={<Navigate to="feynman" replace />} />
          <Route path="active-study/:tool" element={<ActiveStudyTab />} />
        </Route>
        <Route path="/subjects/:subjectId/study" element={<FlashcardStudy />} />
        <Route path="/subjects/:subjectId/oral-live" element={<OralExamLive />} />
        <Route path="/subjects/:subjectId/chat" element={<TutoringChat />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <DebugPanel />
    </div>
  );
}
