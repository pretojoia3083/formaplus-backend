from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.trainer import Trainer

router = APIRouter()

ADMIN_EMAIL = "luisrenatotrader@gmail.com"


def require_admin(user: User = Depends(get_current_user)):
    if user.email != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Apenas o administrador pode acessar")
    return user


@router.get("/trainers")
def list_trainers(status: str = None, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    query = db.query(Trainer)
    if status:
        query = query.filter(Trainer.status == status)
    trainers = query.order_by(Trainer.created_at.desc()).all()
    result = []
    for t in trainers:
        u = db.query(User).filter(User.id == t.user_id).first()
        result.append({
            "id": t.id,
            "user_id": t.user_id,
            "full_name": t.full_name,
            "cref": t.cref,
            "bio": t.bio,
            "specialties": t.specialties,
            "experience_years": t.experience_years,
            "status": t.status,
            "email": u.email if u else "",
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })
    return result


@router.post("/trainers/{trainer_id}/approve")
def approve_trainer(trainer_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    trainer = db.query(Trainer).filter(Trainer.id == trainer_id).first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    trainer.status = "approved"
    db.commit()
    return {"detail": f"Professor {trainer.full_name} aprovado!"}


@router.post("/trainers/{trainer_id}/reject")
def reject_trainer(trainer_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    trainer = db.query(Trainer).filter(Trainer.id == trainer_id).first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    trainer.status = "rejected"
    db.commit()
    return {"detail": f"Professor {trainer.full_name} rejeitado"}


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from app.models.trainer import TrainerClient, ChatMessage
    total_users = db.query(User).count()
    total_trainers = db.query(Trainer).count()
    approved_trainers = db.query(Trainer).filter(Trainer.status == "approved").count()
    pending_trainers = db.query(Trainer).filter(Trainer.status == "pending").count()
    total_clients = db.query(TrainerClient).filter(TrainerClient.status == "active").count()
    total_messages = db.query(ChatMessage).count()
    return {
        "total_users": total_users,
        "total_trainers": total_trainers,
        "approved_trainers": approved_trainers,
        "pending_trainers": pending_trainers,
        "total_clients": total_clients,
        "total_messages": total_messages,
    }
