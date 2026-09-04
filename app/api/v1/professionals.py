from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_plan_type
from app.models.user import User
from app.models.professional import ProfessionalStatus, SessionStatus
from app.schemas.professional import (
    ProfessionalCreate,
    ProfessionalUpdate,
    ProfessionalResponse,
    ProfessionalListResponse,
    ProfessionalServiceCreate,
    ProfessionalServiceResponse,
    ProfessionalAvailabilityCreate,
    ProfessionalAvailabilityResponse,
    ProfessionalSessionCreate,
    ProfessionalSessionResponse,
    ProfessionalSessionUpdate,
    ProfessionalReviewCreate,
    ProfessionalReviewResponse,
    ProfessionalSearchParams,
)
from app.services.professional_service import ProfessionalService

router = APIRouter()
professional_service = ProfessionalService()

@router.post("/professionals/register", response_model=ProfessionalResponse)
async def register_professional(
    data: ProfessionalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = professional_service.register_professional(
            db=db,
            data={**data.dict(), "user_id": current_user.id}
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/professionals/{professional_id}", response_model=ProfessionalResponse)
async def update_professional(
    professional_id: int,
    data: ProfessionalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    professional = professional_service.get_professional_by_user(db, current_user.id)
    if not professional or professional.id != professional_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        result = professional_service.update_professional(
            db=db,
            professional_id=professional_id,
            data=data.dict(exclude_unset=True)
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/professionals/me", response_model=ProfessionalResponse)
async def get_my_professional_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    professional = professional_service.get_professional_by_user(db, current_user.id)
    if not professional:
        raise HTTPException(status_code=404, detail="Perfil profissional não encontrado")
    return professional

@router.get("/professionals/search", response_model=dict)
async def search_professionals(
    professional_type: Optional[str] = None,
    service_type: Optional[str] = None,
    specialties: Optional[List[str]] = Query(None),
    min_rating: Optional[float] = None,
    max_price: Optional[float] = None,
    experience_min_years: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    filters = {
        "professional_type": professional_type,
        "service_type": service_type,
        "specialties": specialties,
        "min_rating": min_rating,
        "max_price": max_price,
        "experience_min_years": experience_min_years,
        "limit": limit,
        "offset": offset,
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    
    result = professional_service.search_professionals(db=db, filters=filters)
    return result

@router.get("/professionals/{professional_id}", response_model=ProfessionalResponse)
async def get_professional(
    professional_id: int,
    db: Session = Depends(get_db)
):
    professional = professional_service.get_professional(db, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    return professional

@router.post("/professionals/{professional_id}/services", response_model=ProfessionalServiceResponse)
async def add_service(
    professional_id: int,
    data: ProfessionalServiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    professional = professional_service.get_professional_by_user(db, current_user.id)
    if not professional or professional.id != professional_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        result = professional_service.add_service(
            db=db,
            professional_id=professional_id,
            data=data.dict()
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/professionals/{professional_id}/services", response_model=List[ProfessionalServiceResponse])
async def get_services(
    professional_id: int,
    db: Session = Depends(get_db)
):
    return professional_service.get_services(db, professional_id)

@router.post("/professionals/{professional_id}/availability", response_model=ProfessionalAvailabilityResponse)
async def add_availability(
    professional_id: int,
    data: ProfessionalAvailabilityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    professional = professional_service.get_professional_by_user(db, current_user.id)
    if not professional or professional.id != professional_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        result = professional_service.add_availability(
            db=db,
            professional_id=professional_id,
            data=data.dict()
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/professionals/{professional_id}/availability", response_model=List[ProfessionalAvailabilityResponse])
async def get_availability(
    professional_id: int,
    db: Session = Depends(get_db)
):
    return professional_service.get_availability(db, professional_id)

@router.get("/professionals/{professional_id}/slots")
async def get_available_slots(
    professional_id: int,
    date: str,
    db: Session = Depends(get_db)
):
    from datetime import datetime
    try:
        target_date = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida")
    
    slots = professional_service.get_available_slots(db, professional_id, target_date)
    return {"slots": slots}

@router.post("/professionals/sessions", response_model=ProfessionalSessionResponse)
async def book_session(
    data: ProfessionalSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = professional_service.book_session(
            db=db,
            user_id=current_user.id,
            data=data.dict()
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/professionals/sessions/{session_id}/confirm", response_model=ProfessionalSessionResponse)
async def confirm_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    professional = professional_service.get_professional_by_user(db, current_user.id)
    if not professional:
        raise HTTPException(status_code=403, detail="Não é profissional")
    
    try:
        result = professional_service.confirm_session(db, session_id, professional.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/professionals/sessions/{session_id}/cancel", response_model=ProfessionalSessionResponse)
async def cancel_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    professional = professional_service.get_professional_by_user(db, current_user.id)
    is_professional = professional is not None
    
    try:
        result = professional_service.cancel_session(
            db, session_id, current_user.id, is_professional
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/professionals/sessions/{session_id}/complete", response_model=ProfessionalSessionResponse)
async def complete_session(
    session_id: int,
    professional_notes: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    professional = professional_service.get_professional_by_user(db, current_user.id)
    if not professional:
        raise HTTPException(status_code=403, detail="Não é profissional")
    
    try:
        result = professional_service.complete_session(
            db, session_id, professional.id, professional_notes
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/professionals/reviews", response_model=ProfessionalReviewResponse)
async def add_review(
    data: ProfessionalReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = professional_service.add_review(
            db=db,
            user_id=current_user.id,
            data=data.dict()
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/professionals/{professional_id}/reviews")
async def get_reviews(
    professional_id: int,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    return professional_service.get_reviews(db, professional_id, limit, offset)

@router.get("/professionals/my-sessions")
async def get_my_sessions(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_status = SessionStatus(status) if status else None
    return professional_service.get_user_sessions(db, current_user.id, session_status)

@router.get("/professionals/my-professional-sessions")
async def get_my_professional_sessions(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    professional = professional_service.get_professional_by_user(db, current_user.id)
    if not professional:
        raise HTTPException(status_code=403, detail="Não é profissional")
    
    session_status = SessionStatus(status) if status else None
    return professional_service.get_professional_sessions(db, professional.id, session_status)
