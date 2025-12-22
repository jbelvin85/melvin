from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models.user import User
from ..schemas.psychographic import (
    AssessmentQuestionnaireResponse,
    AssessmentResultSummary,
    AssessmentSubmission,
    PlayerProfileOut,
    PsychographicQuestionOut,
)
from ..services.assessment import assessment_service


router = APIRouter(prefix="/profiles", tags=["player-profiles"])


@router.get("/questionnaire", response_model=AssessmentQuestionnaireResponse)
def get_assessment_questionnaire(
    db: Session = Depends(get_db),
) -> AssessmentQuestionnaireResponse:
    """
    Get the complete psychographic assessment questionnaire.
    This endpoint is public and doesn't require authentication.
    """
    questions = assessment_service.get_all_questions(db)
    
    # Convert to response schema
    question_responses = [
        PsychographicQuestionOut(
            id=q.id,
            question_text=q.question_text,
            category=q.category,
            order=q.order,
            options=[
                {
                    "id": opt.id,
                    "option_text": opt.option_text,
                    "order": opt.order,
                }
                for opt in q.options
            ],
        )
        for q in questions
    ]
    
    return AssessmentQuestionnaireResponse(
        questions=question_responses,
        total_questions=len(question_responses),
    )


@router.post("/assess", response_model=AssessmentResultSummary)
def submit_assessment(
    payload: AssessmentSubmission,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentResultSummary:
    """
    Submit assessment responses and get psychographic profile classification.
    Requires authentication. Creates or updates user's player profile.
    """
    if not payload.answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one answer is required",
        )
    
    # Convert to format expected by service
    answers = [
        {
            "question_id": answer.question_id,
            "option_id": answer.selected_option_id,
        }
        for answer in payload.answers
    ]
    
    # Process assessment
    profile = assessment_service.process_assessment(db, user, answers)
    
    # Generate summary
    summary = assessment_service.generate_result_summary(profile)
    
    return summary


@router.get("/me", response_model=PlayerProfileOut)
def get_user_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlayerProfileOut:
    """
    Get the current user's psychographic profile.
    Returns 404 if user hasn't completed assessment yet.
    """
    profile = assessment_service.get_user_profile(db, user)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has not completed psychographic assessment",
        )
    
    return profile


@router.get("/me/summary", response_model=AssessmentResultSummary)
def get_user_profile_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentResultSummary:
    """
    Get a human-readable summary of the current user's profile.
    Returns 404 if user hasn't completed assessment yet.
    """
    profile = assessment_service.get_user_profile(db, user)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has not completed psychographic assessment",
        )
    
    return assessment_service.generate_result_summary(profile)
