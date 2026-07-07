export interface Subject {
  id: number;
  name: string;
  description: string | null;
  deconstructed_data?: DeconstructedData | string | null;
  created_at: string;
}

export interface Folder {
  id: number;
  subject_id: number;
  name: string;
  parent_id: number | null;
  created_at: string;
}

export interface StudyDocument {
  id: number;
  subject_id: number;
  folder_id: number | null;
  name: string;
  file_path: string;
  file_type: string;
  created_at: string;
}

export interface Flashcard {
  id: number;
  subject_id: number;
  question: string;
  answer: string;
  ease_factor: number;
  interval_days: number;
  repetitions: number;
  next_review: string;
}

export interface FlashcardStats {
  total: number;
  due: number;
  new: number;
}

export interface OralSession {
  id: number;
  session_id?: number;
  subject_id: number;
  subject_name?: string;
  professor_name: string;
  strictness: 'amichevole' | 'equo' | 'scrupoloso';
  difficulty_level: number;
  score: number | null;
  status: 'active' | 'completed';
  transcript: TranscriptBlock[];
  current_topic: string | null;
  created_at: string;
}

export type TranscriptBlock =
  | { type: 'system'; topics: string[]; message: string }
  | { type: 'question'; topic: string; style: string; text: string }
  | { type: 'answer'; text: string }
  | { type: 'evaluation'; topic: string; score: number; feedback: string; is_correct: boolean }
  | { type: 'system_finish'; avg_score: number; final_grade: string; message: string };

export interface CheatSheetItem {
  term: string;
  definition: string;
}

export interface LikelyQuestion {
  question: string;
  focus_answer: string;
}

export interface MentalHook {
  concept: string;
  mnemonic: string;
}

export interface ConceptMapNode {
  name: string;
  definition: string;
  cluster: string;
}

export interface ConceptMapEdge {
  source: string;
  target: string;
  relationship: string;
  relation_type: string;
}

export interface ConceptMapData {
  nodes: ConceptMapNode[];
  edges: ConceptMapEdge[];
}

export interface DeconstructedData {
  cheat_sheet: CheatSheetItem[];
  likely_questions: LikelyQuestion[];
  mental_hooks: MentalHook[];
  concept_map: ConceptMapData | ConceptMapEdge[];
}

export interface FeynmanEvaluation {
  punti_di_forza: string[];
  lacune: string[];
  inesattezze: string[];
  analogia: string;
  domanda_followup: string;
}

export interface FeynmanTurn {
  role: 'assistant' | 'student';
  text: string;
  evaluation?: FeynmanEvaluation;
}

export interface PodcastEpisode {
  id?: number;
  podcast_id?: number;
  episode_number: number;
  title: string;
  script_text: string;
  audio_filename: string;
  created_at?: string;
}

export interface Podcast {
  id: number;
  subject_id: number;
  title: string;
  topic: string;
  professor_voice: string;
  professor_name: string;
  depth_level: 'breve' | 'normale' | 'approfondito';
  created_at: string;
  episodes: PodcastEpisode[];
}

export type PodcastStreamEvent =
  | {
      status: 'analyzing' | 'scripting' | 'synthesizing';
      message: string;
      total_episodes?: number;
      episode_outlines?: { episode_number: number; title: string }[];
      completed_episodes?: number;
    }
  | {
      status: 'episode_ready' | 'episode_error';
      message: string;
      episode_number: number;
      total_episodes: number;
      completed_episodes: number;
    }
  | { status: 'completed' | 'completed_with_errors'; message: string; podcast: Podcast }
  | { status: 'error'; message: string };

export interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
  sources?: string[];
}

export interface DebugEvent {
  timestamp: string;
  event_type: 'mcts_search' | 'graph_rag' | string;
  details: Record<string, unknown>;
}
