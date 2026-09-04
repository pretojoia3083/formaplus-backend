from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai import CoachRequest, CoachResponse
from app.services.coach_service import CoachService

router = APIRouter()

@router.post("/coach/message", response_model=CoachResponse)
async def send_coach_message(
    request: CoachRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot send messages for other users"
        )
    
    if current_user.plan_type == "free":
        pass
    
    service = CoachService()
    result = service.process_message(
        db=db,
        user_id=request.user_id,
        user_message=request.user_message,
        conversation_id=request.conversation_id
    )
    
    return result

@router.get("/coach/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.ai import AIConversation
    
    conversations = db.query(AIConversation).filter(
        AIConversation.user_id == current_user.id
    ).order_by(AIConversation.started_at.desc()).all()
    
    return conversations

@router.get("/coach/conversations/{conversation_id}")
async def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.ai import AIConversation, AIMessage
    
    conversation = db.query(AIConversation).filter(
        AIConversation.id == conversation_id,
        AIConversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = db.query(AIMessage).filter(
        AIMessage.conversation_id == conversation_id
    ).order_by(AIMessage.created_at.asc()).all()
    
    return {
        "conversation_id": conversation_id,
        "messages": messages
    }
