from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PsychographicTypeEnum(str, Enum):
    """Psychographic type enumeration for schemas."""
    TIMMY_TAMMY = "timmy_tammy"
    JOHNNY_JENNY = "johnny_jenny"
    SPIKE_SHEILA = "spike_sheila"
    VORTHOS = "vorthos"
    MELVIN = "melvin"


class PsychographicSubtypeEnum(str, Enum):
    """Subtype enumeration for schemas."""
    POWER_GAMER = "power_gamer"
    SOCIAL_GAMER = "social_gamer"
    ADRENALINE_GAMER = "adrenaline_gamer"
    COMBO_BUILDER = "combo_builder"
    OFFBEAT_BUILDER = "offbeat_builder"
    ARCHITECT = "architect"
    COMPETITIVE = "competitive"
    TECHNICAL = "technical"
    META_ANALYST = "meta_analyst"
    LORE_ENTHUSIAST = "lore_enthusiast"
    MECHANICS_ENTHUSIAST = "mechanics_enthusiast"


class QuestionOptionOut(BaseModel):
    """Represents an answer option for an assessment question."""
    id: int
    option_text: str
    order: int

    class Config:
        from_attributes = True


class PsychographicQuestionOut(BaseModel):
    """Represents a single assessment question."""
    id: int
    question_text: str
    category: str
    order: int
    options: list[QuestionOptionOut]

    class Config:
        from_attributes = True


class AssessmentQuestionnaireResponse(BaseModel):
    """Response containing all assessment questions for a user."""
    questions: list[PsychographicQuestionOut] = Field(description="List of assessment questions")
    total_questions: int = Field(description="Total number of questions in the assessment")


class AnswerSubmission(BaseModel):
    """User's answer to a single question."""
    question_id: int = Field(description="ID of the question being answered")
    option_id: int = Field(description="ID of the selected option")


class AssessmentSubmission(BaseModel):
    """Complete assessment submission from user."""
    answers: list[AnswerSubmission] = Field(description="List of answers submitted")


class PlayerProfileOut(BaseModel):
    """Complete player profile information."""
    id: int
    user_id: int
    primary_type: PsychographicTypeEnum
    primary_score: float = Field(description="Score 0.0-1.0 for primary archetype")
    secondary_type: PsychographicTypeEnum | None = None
    secondary_score: float | None = None
    subtype: PsychographicSubtypeEnum | None = None
    subtype_score: float | None = None
    
    # Preference scores
    prefers_big_plays: float = Field(description="Tendency toward Timmy playstyle (0.0-1.0)")
    prefers_originality: float = Field(description="Tendency toward Johnny playstyle (0.0-1.0)")
    prefers_optimization: float = Field(description="Tendency toward Spike playstyle (0.0-1.0)")
    enjoys_lore: float = Field(description="Tendency toward Vorthos interests (0.0-1.0)")
    enjoys_mechanics: float = Field(description="Tendency toward Melvin interests (0.0-1.0)")
    
    total_questions_answered: int
    created_at: datetime
    updated_at: datetime
    last_assessment_at: datetime | None = None

    class Config:
        from_attributes = True


class AssessmentResultSummary(BaseModel):
    """Summary of assessment results for display to user."""
    primary_type: PsychographicTypeEnum
    primary_type_label: str = Field(description="Human-readable name for primary type")
    primary_score: float
    secondary_type: PsychographicTypeEnum | None = None
    secondary_type_label: str | None = None
    secondary_score: float | None = None
    subtype: PsychographicSubtypeEnum | None = None
    subtype_label: str | None = None
    
    description: str = Field(description="Description of the player type")
    play_style_summary: str = Field(description="Summary of how this type typically plays")
    conversation_guidance: str = Field(description="How Melvin should adjust responses for this player")
    
    preference_breakdown: dict[str, float] = Field(description="Breakdown of all preference scores")


class ProfilePreferences(BaseModel):
    """Player preferences derived from their profile."""
    prefers_big_plays: float
    prefers_originality: float
    prefers_optimization: float
    enjoys_lore: float
    enjoys_mechanics: float
    
    class Config:
        from_attributes = True
