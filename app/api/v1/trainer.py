from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.trainer import Trainer, TrainerClient, ChatMessage
from app.schemas.trainer import (
    TrainerRegister, TrainerResponse, ChatMessageCreate,
    ChatMessageResponse, ChatConversation, TrainerClientResponse,
    AssignClientRequest,
)

router = APIRouter()


@router.post("/register")
def register_trainer(data: TrainerRegister, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    existing = db.query(Trainer).filter(Trainer.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Você já está cadastrado como professor")

    trainer = Trainer(
        user_id=user.id,
        full_name=data.full_name,
        cref=data.cref,
        bio=data.bio,
        specialties=data.specialties,
        experience_years=data.experience_years,
        status="pending",
    )
    db.add(trainer)
    db.commit()
    db.refresh(trainer)
    return {"detail": "Cadastro realizado! Aguarde aprovação.", "trainer_id": trainer.id}


@router.get("/me")
def get_my_trainer_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trainer = db.query(Trainer).filter(Trainer.user_id == user.id).first()
    if not trainer:
        return None
    return {
        "id": trainer.id,
        "user_id": trainer.user_id,
        "full_name": trainer.full_name,
        "cref": trainer.cref,
        "bio": trainer.bio,
        "specialties": trainer.specialties,
        "experience_years": trainer.experience_years,
        "status": trainer.status,
        "created_at": trainer.created_at.isoformat() if trainer.created_at else None,
    }


@router.get("/clients")
def get_my_clients(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trainer = db.query(Trainer).filter(Trainer.user_id == user.id).first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Perfil de professor não encontrado")

    clients = db.query(TrainerClient).filter(TrainerClient.trainer_id == trainer.id, TrainerClient.status == "active").all()
    result = []
    for c in clients:
        u = db.query(User).filter(User.id == c.user_id).first()
        result.append({
            "id": c.id,
            "trainer_id": c.trainer_id,
            "user_id": c.user_id,
            "status": c.status,
            "client_name": f"{u.first_name} {u.last_name}".strip() if u else "Desconhecido",
            "client_email": u.email if u else "",
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return result


@router.post("/assign-client")
def assign_client(data: AssignClientRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trainer = db.query(Trainer).filter(Trainer.user_id == user.id).first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Perfil de professor não encontrado")

    client_user = db.query(User).filter(User.email == data.user_email).first()
    if not client_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado com esse email")

    existing = db.query(TrainerClient).filter(
        TrainerClient.trainer_id == trainer.id,
        TrainerClient.user_id == client_user.id,
        TrainerClient.status == "active"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Este aluno já está vinculado a você")

    tc = TrainerClient(trainer_id=trainer.id, user_id=client_user.id, status="active")
    db.add(tc)
    db.commit()
    return {"detail": f"Aluno {client_user.first_name or client_user.email} vinculado com sucesso!"}


@router.delete("/remove-client/{client_id}")
def remove_client(client_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trainer = db.query(Trainer).filter(Trainer.user_id == user.id).first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Perfil de professor não encontrado")

    tc = db.query(TrainerClient).filter(
        TrainerClient.id == client_id,
        TrainerClient.trainer_id == trainer.id
    ).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Vínculo não encontrado")

    tc.status = "removed"
    db.commit()
    return {"detail": "Aluno removido"}


@router.get("/my-trainer")
def get_my_trainer(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tc = db.query(TrainerClient).filter(TrainerClient.user_id == user.id, TrainerClient.status == "active").first()
    if not tc:
        return None

    trainer = db.query(Trainer).filter(Trainer.id == tc.trainer_id).first()
    if not trainer:
        return None

    u = db.query(User).filter(User.id == trainer.user_id).first()
    return {
        "id": trainer.id,
        "full_name": trainer.full_name,
        "cref": trainer.cref,
        "bio": trainer.bio,
        "specialties": trainer.specialties,
        "trainer_name": f"{u.first_name} {u.last_name}".strip() if u else trainer.full_name,
    }
