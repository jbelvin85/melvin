from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from ..models.psychographic_profile import (
    AssessmentResponse,
    PlayerProfile,
    PsychographicSubtype,
    PsychographicType,
    PsychographicQuestion,
    QuestionOption,
)
from ..schemas.psychographic import AssessmentResultSummary, PsychographicSubtypeEnum, PsychographicTypeEnum

if TYPE_CHECKING:
    from ..models.user import User


# Archetype descriptions and guidance
ARCHETYPE_INFO = {
    PsychographicType.TIMMY_TAMMY: {
        "label": "Timmy/Tammy",
        "description": "You're motivated by emotional experience and memorable moments. You love the excitement of big, impactful plays and spectacle. Magic is about having fun and creating exciting stories with friends.",
        "play_style": "You gravitate toward powerful effects and dramatic moments. You value the thrill of pulling off impressive plays over optimizing every decision. You enjoy social aspects and group enjoyment.",
        "conversation_guidance": "Emphasize exciting possibilities, memorable outcomes, and the fun factor. Avoid overwhelming you with probability math or efficiency arguments. Focus on how plays will feel and what makes them fun.",
        "subtypes": ["power_gamer", "social_gamer", "adrenaline_gamer"],
    },
    PsychographicType.JOHNNY_JENNY: {
        "label": "Johnny/Jenny",
        "description": "You're driven by creativity and self-expression. Building unique decks and discovering clever interactions is what excites you. You want to win with your own ideas, not cookie-cutter strategies.",
        "play_style": "You're drawn to deckbuilding as an art form. You explore unusual synergies and constraints. You value originality and elegant design. Winning with your unique creation is deeply satisfying.",
        "conversation_guidance": "Explore possibilities, brainstorm creative directions, and highlight synergies. Celebrate unconventional approaches. Discuss the design elegance and interaction patterns that make ideas work.",
        "subtypes": ["combo_builder", "offbeat_builder", "architect"],
    },
    PsychographicType.SPIKE_SHEILA: {
        "label": "Spike/Sheila",
        "description": "You're motivated by competition and optimization. You want to win, understand the meta deeply, and execute your strategy flawlessly. Magic is a game of skill and decision-making.",
        "play_style": "You study matchups, analyze card choices, and optimize every decision. You're competitive and want to understand the technical aspects. You adapt to the meta and stay ahead of trends.",
        "conversation_guidance": "Focus on competitive advantage, technical analysis, and optimization. Discuss win rates, matchups, and strategic depth. Respect the skill and preparation required.",
        "subtypes": ["competitive", "technical", "meta_analyst"],
    },
    PsychographicType.VORTHOS: {
        "label": "Vorthos",
        "description": "You're captivated by the story and world-building of Magic. The lore, flavor, and themes matter deeply to you. You appreciate how cards and mechanics express the narrative.",
        "play_style": "You're drawn to cards with strong flavor and thematic coherence. You enjoy building decks that tell stories. You appreciate the art and the world's history.",
        "conversation_guidance": "Connect mechanics to story and flavor. Discuss the world-building and narrative significance. Explore how cards fit into the larger Magic universe.",
        "subtypes": ["lore_enthusiast"],
    },
    PsychographicType.MELVIN: {
        "label": "Melvin",
        "description": "You're fascinated by the mechanical systems and how cards interact at a deep level. You love understanding rules interactions and the elegant design of mechanics.",
        "play_style": "You appreciate the technical sophistication of card design. You enjoy discovering how mechanics work together. You value clean, elegant mechanical design.",
        "conversation_guidance": "Dive into the mechanics and rules interactions. Explain the design principles and how systems work. Discuss the engineering of card effects.",
        "subtypes": ["mechanics_enthusiast"],
    },
}

SUBTYPE_INFO = {
    PsychographicSubtype.POWER_GAMER: {
        "label": "Power Gamer",
        "description": "You're drawn to raw power and overwhelming effects",
    },
    PsychographicSubtype.SOCIAL_GAMER: {
        "label": "Social Gamer",
        "description": "You value the social and group experience",
    },
    PsychographicSubtype.ADRENALINE_GAMER: {
        "label": "Adrenaline Gamer",
        "description": "You seek risk, tension, and exciting moments",
    },
    PsychographicSubtype.COMBO_BUILDER: {
        "label": "Combo Builder",
        "description": "You love intricate card interactions and synergies",
    },
    PsychographicSubtype.OFFBEAT_BUILDER: {
        "label": "Offbeat Builder",
        "description": "You enjoy building with unusual themes or constraints",
    },
    PsychographicSubtype.ARCHITECT: {
        "label": "Architect",
        "description": "You appreciate structural elegance and design coherence",
    },
    PsychographicSubtype.COMPETITIVE: {
        "label": "Competitive",
        "description": "You're driven by winning and competition",
    },
    PsychographicSubtype.TECHNICAL: {
        "label": "Technical Player",
        "description": "You value skill, precision, and mastery",
    },
    PsychographicSubtype.META_ANALYST: {
        "label": "Meta Analyst",
        "description": "You study trends and adapt to the competitive landscape",
    },
    PsychographicSubtype.LORE_ENTHUSIAST: {
        "label": "Lore Enthusiast",
        "description": "You're fascinated by story and world-building",
    },
    PsychographicSubtype.MECHANICS_ENTHUSIAST: {
        "label": "Mechanics Enthusiast",
        "description": "You love understanding how systems work",
    },
}


class AssessmentService:
    """Service for managing psychographic assessments and player profiles."""

    @staticmethod
    def get_all_questions(db: Session) -> list[PsychographicQuestion]:
        """Fetch all assessment questions ordered by position."""
        return (
            db.query(PsychographicQuestion)
            .order_by(PsychographicQuestion.order)
            .all()
        )

    @staticmethod
    def process_assessment(
        db: Session,
        user: User,
        answers: list[dict[str, int]],
    ) -> PlayerProfile:
        """
        Process user assessment responses and calculate their psychographic profile.
        
        Args:
            db: Database session
            user: User being assessed
            answers: List of {question_id, option_id} dicts
            
        Returns:
            Updated PlayerProfile
        """
        # Get or create profile
        profile = db.query(PlayerProfile).filter(PlayerProfile.user_id == user.id).first()
        if not profile:
            profile = PlayerProfile(user_id=user.id, primary_type=PsychographicType.TIMMY_TAMMY)
            db.add(profile)
            db.flush()
        
        # Clear previous responses
        db.query(AssessmentResponse).filter(AssessmentResponse.profile_id == profile.id).delete()
        
        # Calculate archetype scores
        scores = {
            "timmy": 0.0,
            "johnny": 0.0,
            "spike": 0.0,
            "vorthos": 0.0,
            "melvin": 0.0,
        }
        
        subtype_scores = {
            "power_gamer": 0.0,
            "social_gamer": 0.0,
            "adrenaline": 0.0,
            "combo_builder": 0.0,
            "offbeat_builder": 0.0,
            "architect": 0.0,
            "competitive": 0.0,
            "technical": 0.0,
            "meta_analyst": 0.0,
            "lore": 0.0,
            "mechanics": 0.0,
        }
        
        answer_count = 0
        
        # Process each answer
        for answer in answers:
            question_id = answer.get("question_id")
            option_id = answer.get("option_id")
            
            if not question_id or not option_id:
                continue
            
            option = db.query(QuestionOption).filter(QuestionOption.id == option_id).first()
            if not option:
                continue
            
            # Store response
            response = AssessmentResponse(
                profile_id=profile.id,
                question_id=question_id,
                selected_option_id=option_id,
            )
            db.add(response)
            
            # Accumulate scores
            scores["timmy"] += option.timmy_weight
            scores["johnny"] += option.johnny_weight
            scores["spike"] += option.spike_weight
            scores["vorthos"] += option.vorthos_weight
            scores["melvin"] += option.melvin_weight
            
            subtype_scores["power_gamer"] += option.power_gamer_weight
            subtype_scores["social_gamer"] += option.social_gamer_weight
            subtype_scores["adrenaline"] += option.adrenaline_weight
            subtype_scores["combo_builder"] += option.combo_builder_weight
            subtype_scores["offbeat_builder"] += option.offbeat_builder_weight
            subtype_scores["architect"] += option.architect_weight
            subtype_scores["competitive"] += option.competitive_weight
            subtype_scores["technical"] += option.technical_weight
            subtype_scores["meta_analyst"] += option.meta_analyst_weight
            subtype_scores["lore"] += option.lore_weight
            subtype_scores["mechanics"] += option.mechanics_weight
            
            answer_count += 1
        
        db.commit()
        
        if answer_count == 0:
            profile.total_questions_answered = 0
            db.add(profile)
            db.commit()
            return profile
        
        # Normalize scores (0.0 to 1.0)
        scores = {k: v / answer_count for k, v in scores.items()}
        subtype_scores = {k: v / answer_count for k, v in subtype_scores.items()}
        
        # Find primary and secondary types
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        primary_type = sorted_types[0][0]
        primary_score = sorted_types[0][1]
        
        secondary_type = sorted_types[1][0] if len(sorted_types) > 1 else None
        secondary_score = sorted_types[1][1] if len(sorted_types) > 1 else None
        
        # Find best subtype
        sorted_subtypes = sorted(subtype_scores.items(), key=lambda x: x[1], reverse=True)
        best_subtype = sorted_subtypes[0][0] if sorted_subtypes[0][1] > 0.1 else None
        best_subtype_score = sorted_subtypes[0][1] if best_subtype else None
        
        # Map string keys to enum values
        type_map = {
            "timmy": PsychographicType.TIMMY_TAMMY,
            "johnny": PsychographicType.JOHNNY_JENNY,
            "spike": PsychographicType.SPIKE_SHEILA,
            "vorthos": PsychographicType.VORTHOS,
            "melvin": PsychographicType.MELVIN,
        }
        
        subtype_map = {
            "power_gamer": PsychographicSubtype.POWER_GAMER,
            "social_gamer": PsychographicSubtype.SOCIAL_GAMER,
            "adrenaline": PsychographicSubtype.ADRENALINE_GAMER,
            "combo_builder": PsychographicSubtype.COMBO_BUILDER,
            "offbeat_builder": PsychographicSubtype.OFFBEAT_BUILDER,
            "architect": PsychographicSubtype.ARCHITECT,
            "competitive": PsychographicSubtype.COMPETITIVE,
            "technical": PsychographicSubtype.TECHNICAL,
            "meta_analyst": PsychographicSubtype.META_ANALYST,
            "lore": PsychographicSubtype.LORE_ENTHUSIAST,
            "mechanics": PsychographicSubtype.MECHANICS_ENTHUSIAST,
        }
        
        # Update profile
        profile.primary_type = type_map[primary_type]
        profile.primary_score = primary_score
        profile.secondary_type = type_map[secondary_type] if secondary_type else None
        profile.secondary_score = secondary_score
        profile.subtype = subtype_map.get(best_subtype)
        profile.subtype_score = best_subtype_score
        profile.total_questions_answered = answer_count
        profile.last_assessment_at = datetime.utcnow()
        
        # Set preference scores
        profile.prefers_big_plays = scores["timmy"]
        profile.prefers_originality = scores["johnny"]
        profile.prefers_optimization = scores["spike"]
        profile.enjoys_lore = scores["vorthos"]
        profile.enjoys_mechanics = scores["melvin"]
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        return profile

    @staticmethod
    def get_user_profile(db: Session, user: User) -> PlayerProfile | None:
        """Retrieve a user's psychographic profile."""
        return db.query(PlayerProfile).filter(PlayerProfile.user_id == user.id).first()

    @staticmethod
    def generate_result_summary(profile: PlayerProfile) -> AssessmentResultSummary:
        """Generate a human-readable summary of assessment results."""
        primary_info = ARCHETYPE_INFO[profile.primary_type]
        secondary_info = ARCHETYPE_INFO[profile.secondary_type] if profile.secondary_type else None
        subtype_info = SUBTYPE_INFO.get(profile.subtype) if profile.subtype else None
        
        secondary_type_label = secondary_info["label"] if secondary_info else None
        subtype_label = subtype_info["label"] if subtype_info else None
        
        return AssessmentResultSummary(
            primary_type=PsychographicTypeEnum(profile.primary_type.value),
            primary_type_label=primary_info["label"],
            primary_score=profile.primary_score,
            secondary_type=PsychographicTypeEnum(profile.secondary_type.value) if profile.secondary_type else None,
            secondary_type_label=secondary_type_label,
            secondary_score=profile.secondary_score,
            subtype=PsychographicSubtypeEnum(profile.subtype.value) if profile.subtype else None,
            subtype_label=subtype_label,
            description=primary_info["description"],
            play_style_summary=primary_info["play_style"],
            conversation_guidance=primary_info["conversation_guidance"],
            preference_breakdown={
                "big_plays": profile.prefers_big_plays,
                "originality": profile.prefers_originality,
                "optimization": profile.prefers_optimization,
                "lore": profile.enjoys_lore,
                "mechanics": profile.enjoys_mechanics,
            },
        )


assessment_service = AssessmentService()
