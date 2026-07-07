import { useParams } from 'react-router-dom';
import { useSubjects } from '../../api/subjects';

/** Resolves the current :subjectId route param against the subjects list. */
export function useCourseSubject() {
  const { subjectId } = useParams<{ subjectId: string }>();
  const id = Number(subjectId);
  const { data: subjects, isLoading } = useSubjects();
  const subject = subjects?.find((s) => s.id === id) ?? null;
  return { subjectId: id, subject, isLoading };
}
