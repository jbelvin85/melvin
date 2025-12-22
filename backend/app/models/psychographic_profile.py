from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


class PsychographicType(str, Enum):
    """Magic player psychographic archetypes based on Mark Rosewater's player types."""
    
    # Primary archetypes
    TIMMY_TAMMY = "timmy_tammy"
    JOHNNY_JENNY = "johnny_jenny"
    SPIKE_SHEILA = "spike_sheila"
    
    # Secondary considerations
    VORTHOS = "vorthos"
    MELVIN = "melvin"


class PsychographicSubtype(str, Enum):
    """Subtypes that refine the main archetype."""
    
    # Timmy/Tammy subtypes
    POWER_GAMER = "power_gamer"
    SOCIAL_GAMER = "social_gamer"
    ADRENALINE_GAMER = "adrenaline_gamer"
    
    # Johnny/Jenny subtypes
    COMBO_BUILDER = "combo_builder"
    OFFBEAT_BUILDER = "offbeat_builder"
    ARCHITECT = "architect"
    
    # Spike/Sheila subtypes
    COMPETITIVE = "competitive"
    TECHNICAL = "technical"
    META_ANALYST = "meta_analyst"
    
    # Other subtypes
    LORE_ENTHUSIAST = "lore_enthusiast"
    MECHANICS_ENTHUSIAST = "mechanics_enthusiast"


class PlayerProfile(Base):
    """Stores user psychographic profile and assessment results."""
    
    __tablename__ = "player_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Primary profile assessment
    primary_type = Column(SQLEnum(PsychographicType), nullable=False)
    primary_score = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Secondary profile (if close match)
    secondary_type = Column(SQLEnum(PsychographicType), nullable=True)
    secondary_score = Column(Float, nullable=True)
    
    # Subtype for more granular classification
    subtype = Column(SQLEnum(PsychographicSubtype), nullable=True)
    subtype_score = Column(Float, nullable=True)
    
    # Assessment details
    total_questions_answered = Column(Integer, default=0)
    assessment_version = Column(Integer, default=1)  # For future improvements
    
    # Preferences inferred from profile
    prefers_big_plays = Column(Float, default=0.5)  # Timmy trait
    prefers_originality = Column(Float, default=0.5)  # Johnny trait
    prefers_optimization = Column(Float, default=0.5)  # Spike trait
    enjoys_lore = Column(Float, default=0.5)  # Vorthos trait
    enjoys_mechanics = Column(Float, default=0.5)  # Melvin trait
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_assessment_at = Column(DateTime, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="profile")
    assessment_responses = relationship("AssessmentResponse", back_populates="profile", cascade="all, delete-orphan")


class PsychographicQuestion(Base):
    """Assessment questions used to classify player archetype."""
    
    __tablename__ = "psychographic_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # e.g., "emotional_impact", "creativity", "competition"
    assessment_version = Column(Integer, default=1)
    order = Column(Integer, nullable=False, index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")


class QuestionOption(Base):
    """Answer options for assessment questions with archetype weights."""
    
    __tablename__ = "question_options"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("psychographic_questions.id"), nullable=False)
    option_text = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    
    # Archetype weights (sum should equal 1.0)
    timmy_weight = Column(Float, default=0.0)
    johnny_weight = Column(Float, default=0.0)
    spike_weight = Column(Float, default=0.0)
    vorthos_weight = Column(Float, default=0.0)
    melvin_weight = Column(Float, default=0.0)
    
    # Subtype weights
    power_gamer_weight = Column(Float, default=0.0)
    social_gamer_weight = Column(Float, default=0.0)
    adrenaline_weight = Column(Float, default=0.0)
    combo_builder_weight = Column(Float, default=0.0)
    offbeat_builder_weight = Column(Float, default=0.0)
    architect_weight = Column(Float, default=0.0)
    competitive_weight = Column(Float, default=0.0)
    technical_weight = Column(Float, default=0.0)
    meta_analyst_weight = Column(Float, default=0.0)
    lore_weight = Column(Float, default=0.0)
    mechanics_weight = Column(Float, default=0.0)
    
    question = relationship("PsychographicQuestion", back_populates="options")


class AssessmentResponse(Base):
    """User responses to assessment questions."""
    
    __tablename__ = "assessment_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("player_profiles.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("psychographic_questions.id"), nullable=False)
    selected_option_id = Column(Integer, ForeignKey("question_options.id"), nullable=False)
    
    # Metadata
    answered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    profile = relationship("PlayerProfile", back_populates="assessment_responses")
