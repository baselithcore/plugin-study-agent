"""Pydantic data models for study agent router API."""

from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    name: str = Field(..., description="Name of the course/subject")
    description: str | None = Field(
        None, description="Detailed description of the subject"
    )


class FlashcardReview(BaseModel):
    flashcard_id: int = Field(..., description="ID of the reviewed flashcard")
    rating: int = Field(
        ...,
        ge=0,
        le=5,
        description="Response rating (0-5) for SM-2 scheduler: 0=forgot, 5=perfect recall",
    )


class OralSessionStart(BaseModel):
    subject_id: int = Field(..., description="Subject ID for the oral simulation")
    professor_name: str = Field(
        "Prof. Rossi", description="Name of the simulated professor"
    )
    strictness: str = Field(
        "equo",
        description="Professor personality: amichevole (friendly), equo (fair), scrupoloso (strict)",
    )
    difficulty_level: int = Field(
        3, ge=1, le=5, description="Difficulty level from 1 to 5"
    )


class OralSessionAnswer(BaseModel):
    session_id: int = Field(..., description="Running session ID")
    answer_text: str = Field(..., description="Student's verbal or typed response")


class FlashcardGenerateRequest(BaseModel):
    num_flashcards: int = Field(
        10, ge=1, le=30, description="Number of flashcards to generate"
    )


class PodcastGenerateRequest(BaseModel):
    topic: str = Field(..., description="The main topic of the podcast")
    depth_level: str = Field(
        "normale", description="Depth level: breve, normale, approfondito"
    )


class BulkDeleteRequest(BaseModel):
    document_ids: list[int] = Field(
        default_factory=list, description="IDs of documents/files to delete"
    )
    folder_ids: list[int] = Field(
        default_factory=list, description="IDs of folders to delete"
    )


class BulkMoveRequest(BaseModel):
    document_ids: list[int] = Field(
        default_factory=list, description="IDs of documents/files to move"
    )
    folder_ids: list[int] = Field(
        default_factory=list, description="IDs of folders to move"
    )
    target_folder_id: int | None = Field(
        None, description="Target folder ID (None or null for root)"
    )
