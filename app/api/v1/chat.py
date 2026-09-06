from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.trainer import ChatMessage, TrainerClient, Trainer
from app.schemas.trainer import ChatMessageCreate, ChatMessageResponse, ChatConversation

router = APIRouter()


@router.post("/send")
def send_message(data: ChatMessageCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    receiver = db.query(User).filter(User.id == data.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Destinatário não encontrado")

    msg = ChatMessage(
        sender_id=user.id,
        receiver_id=data.receiver_id,
        message=data.message,
        is_read=False,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "receiver_id": msg.receiver_id,
        "message": msg.message,
        "is_read": msg.is_read,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


@router.get("/conversations")
def get_conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trainer = db.query(Trainer).filter(Trainer.user_id == user.id).first()
    is_trainer = trainer is not None

    if is_trainer:
        client_ids_raw = db.query(TrainerClient.user_id).filter(
            TrainerClient.trainer_id == trainer.id,
            TrainerClient.status == "active"
        ).all()
        client_ids = [c[0] for c in client_ids_raw]
        chat_user_ids = set(client_ids)
    else:
        trainer_rel = db.query(TrainerClient).filter(
            TrainerClient.user_id == user.id,
            TrainerClient.status == "active"
        ).first()
        if trainer_rel:
            trainer_user = db.query(Trainer).filter(Trainer.id == trainer_rel.trainer_id).first()
            if trainer_user:
                chat_user_ids = {trainer_user.user_id}
            else:
                chat_user_ids = set()
        else:
            chat_user_ids = set()

    conversations = []
    for uid in chat_user_ids:
        other = db.query(User).filter(User.id == uid).first()
        if not other:
            continue

        last_msg = db.query(ChatMessage).filter(
            ((ChatMessage.sender_id == user.id) & (ChatMessage.receiver_id == uid)) |
            ((ChatMessage.sender_id == uid) & (ChatMessage.receiver_id == user.id))
        ).order_by(ChatMessage.created_at.desc()).first()

        unread = db.query(ChatMessage).filter(
            ChatMessage.sender_id == uid,
            ChatMessage.receiver_id == user.id,
            ChatMessage.is_read == False
        ).count()

        conversations.append({
            "user_id": uid,
            "user_name": f"{other.first_name} {other.last_name}".strip() if other.first_name else other.email,
            "last_message": last_msg.message if last_msg else "",
            "last_message_at": last_msg.created_at.isoformat() if last_msg and last_msg.created_at else "",
            "unread_count": unread,
        })

    conversations.sort(key=lambda x: x["last_message_at"], reverse=True)
    return conversations


@router.get("/messages/{other_user_id}")
def get_messages(other_user_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    messages = db.query(ChatMessage).filter(
        ((ChatMessage.sender_id == user.id) & (ChatMessage.receiver_id == other_user_id)) |
        ((ChatMessage.sender_id == other_user_id) & (ChatMessage.receiver_id == user.id))
    ).order_by(ChatMessage.created_at.asc()).all()

    db.query(ChatMessage).filter(
        ChatMessage.sender_id == other_user_id,
        ChatMessage.receiver_id == user.id,
        ChatMessage.is_read == False
    ).update({"is_read": True})
    db.commit()

    return [{
        "id": m.id,
        "sender_id": m.sender_id,
        "receiver_id": m.receiver_id,
        "message": m.message,
        "is_read": m.is_read,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    } for m in messages]


@router.get("/unread-count")
def get_unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = db.query(ChatMessage).filter(
        ChatMessage.receiver_id == user.id,
        ChatMessage.is_read == False
    ).count()
    return {"count": count}
