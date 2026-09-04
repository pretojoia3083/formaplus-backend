import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta

from app.models.professional import (
    Professional,
    ProfessionalService,
    ProfessionalAvailability,
    ProfessionalSession,
    ProfessionalReview,
    ProfessionalStatus,
    SessionStatus,
)
from app.models.user import User

logger = logging.getLogger(__name__)

class ProfessionalService:
    def register_professional(
        self,
        db: Session,
        data: Dict[str, Any]
    ) -> Professional:
        existing = db.query(Professional).filter(
            Professional.user_id == data["user_id"]
        ).first()
        if existing:
            raise ValueError("Usuário já é um profissional")
        
        professional = Professional(**data)
        db.add(professional)
        db.commit()
        db.refresh(professional)
        
        logger.info(f"Profissional registrado: {professional.id} - {professional.name}")
        return professional
    
    def update_professional(
        self,
        db: Session,
        professional_id: int,
        data: Dict[str, Any]
    ) -> Professional:
        professional = db.query(Professional).filter(
            Professional.id == professional_id
        ).first()
        
        if not professional:
            raise ValueError("Profissional não encontrado")
        
        for key, value in data.items():
            if hasattr(professional, key) and value is not None:
                setattr(professional, key, value)
        
        db.commit()
        db.refresh(professional)
        return professional
    
    def get_professional(
        self,
        db: Session,
        professional_id: int
    ) -> Optional[Professional]:
        return db.query(Professional).filter(
            Professional.id == professional_id,
            Professional.status == ProfessionalStatus.ACTIVE
        ).first()
    
    def get_professional_by_user(
        self,
        db: Session,
        user_id: int
    ) -> Optional[Professional]:
        return db.query(Professional).filter(
            Professional.user_id == user_id
        ).first()
    
    def search_professionals(
        self,
        db: Session,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        query = db.query(Professional).filter(
            Professional.status == ProfessionalStatus.ACTIVE
        )
        
        if filters.get("professional_type"):
            query = query.filter(
                Professional.professional_type == filters["professional_type"]
            )
        
        if filters.get("service_type"):
            query = query.filter(
                Professional.service_type.in_([filters["service_type"], "both"])
            )
        
        if filters.get("specialties"):
            specialty_filters = []
            for specialty in filters["specialties"]:
                specialty_filters.append(
                    Professional.specialties.contains([specialty])
                )
            query = query.filter(or_(*specialty_filters))
        
        if filters.get("min_rating"):
            query = query.filter(Professional.rating_avg >= filters["min_rating"])
        
        if filters.get("max_price"):
            query = query.filter(
                or_(
                    Professional.price_per_session_brl <= filters["max_price"],
                    Professional.price_per_session_brl.is_(None)
                )
            )
        
        if filters.get("experience_min_years"):
            query = query.filter(
                Professional.experience_years >= filters["experience_min_years"]
            )
        
        limit = filters.get("limit", 20)
        offset = filters.get("offset", 0)
        
        total = query.count()
        professionals = query.offset(offset).limit(limit).all()
        
        return {
            "total": total,
            "professionals": professionals,
            "limit": limit,
            "offset": offset
        }
    
    def add_service(
        self,
        db: Session,
        professional_id: int,
        data: Dict[str, Any]
    ) -> ProfessionalService:
        professional = db.query(Professional).filter(
            Professional.id == professional_id
        ).first()
        if not professional:
            raise ValueError("Profissional não encontrado")
        
        service = ProfessionalService(
            professional_id=professional_id,
            **data
        )
        db.add(service)
        db.commit()
        db.refresh(service)
        return service
    
    def get_services(
        self,
        db: Session,
        professional_id: int
    ) -> List[ProfessionalService]:
        return db.query(ProfessionalService).filter(
            ProfessionalService.professional_id == professional_id,
            ProfessionalService.is_active == True
        ).all()
    
    def add_availability(
        self,
        db: Session,
        professional_id: int,
        data: Dict[str, Any]
    ) -> ProfessionalAvailability:
        availability = ProfessionalAvailability(
            professional_id=professional_id,
            **data
        )
        db.add(availability)
        db.commit()
        db.refresh(availability)
        return availability
    
    def get_availability(
        self,
        db: Session,
        professional_id: int
    ) -> List[ProfessionalAvailability]:
        return db.query(ProfessionalAvailability).filter(
            ProfessionalAvailability.professional_id == professional_id,
            ProfessionalAvailability.is_available == True
        ).order_by(
            ProfessionalAvailability.day_of_week,
            ProfessionalAvailability.start_time
        ).all()
    
    def get_available_slots(
        self,
        db: Session,
        professional_id: int,
        date: datetime
    ) -> List[Dict[str, Any]]:
        day_of_week = date.weekday()
        availabilities = db.query(ProfessionalAvailability).filter(
            ProfessionalAvailability.professional_id == professional_id,
            ProfessionalAvailability.day_of_week == day_of_week,
            ProfessionalAvailability.is_available == True
        ).all()
        
        if not availabilities:
            return []
        
        date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        booked_sessions = db.query(ProfessionalSession).filter(
            ProfessionalSession.professional_id == professional_id,
            ProfessionalSession.scheduled_date.between(date_start, date_end),
            ProfessionalSession.status.in_(["pending", "confirmed", "in_progress"])
        ).all()
        
        booked_times = [
            session.scheduled_date.strftime("%H:%M")
            for session in booked_sessions
        ]
        
        slots = []
        for availability in availabilities:
            start_hour, start_min = map(int, availability.start_time.split(":"))
            end_hour, end_min = map(int, availability.end_time.split(":"))
            
            current = datetime(
                date.year, date.month, date.day,
                start_hour, start_min
            )
            end = datetime(
                date.year, date.month, date.day,
                end_hour, end_min
            )
            
            while current + timedelta(minutes=60) <= end:
                time_str = current.strftime("%H:%M")
                if time_str not in booked_times:
                    slots.append({
                        "time": time_str,
                        "datetime": current.isoformat(),
                        "available": True
                    })
                current += timedelta(minutes=60)
        
        return slots
    
    def book_session(
        self,
        db: Session,
        user_id: int,
        data: Dict[str, Any]
    ) -> ProfessionalSession:
        professional_id = data["professional_id"]
        scheduled_date = data["scheduled_date"]
        
        professional = db.query(Professional).filter(
            Professional.id == professional_id,
            Professional.status == ProfessionalStatus.ACTIVE
        ).first()
        if not professional:
            raise ValueError("Profissional não encontrado ou inativo")
        
        day_of_week = scheduled_date.weekday()
        availability = db.query(ProfessionalAvailability).filter(
            ProfessionalAvailability.professional_id == professional_id,
            ProfessionalAvailability.day_of_week == day_of_week,
            ProfessionalAvailability.is_available == True
        ).first()
        
        if not availability:
            raise ValueError("Profissional não disponível neste dia")
        
        time_str = scheduled_date.strftime("%H:%M")
        if time_str < availability.start_time or time_str > availability.end_time:
            raise ValueError("Horário fora do período de atendimento")
        
        conflicting = db.query(ProfessionalSession).filter(
            ProfessionalSession.professional_id == professional_id,
            ProfessionalSession.scheduled_date == scheduled_date,
            ProfessionalSession.status.in_(["pending", "confirmed", "in_progress"])
        ).first()
        
        if conflicting:
            raise ValueError("Horário já reservado")
        
        service_id = data.get("service_id")
        price = None
        
        if service_id:
            service = db.query(ProfessionalService).filter(
                ProfessionalService.id == service_id,
                ProfessionalService.professional_id == professional_id,
                ProfessionalService.is_active == True
            ).first()
            if service:
                price = service.price_brl
                duration = service.duration_minutes
            else:
                raise ValueError("Serviço não encontrado")
        else:
            price = professional.price_per_session_brl or 0
            duration = 60
        
        scheduled_end = scheduled_date + timedelta(minutes=duration)
        
        session = ProfessionalSession(
            professional_id=professional_id,
            user_id=user_id,
            service_id=service_id,
            scheduled_date=scheduled_date,
            scheduled_end=scheduled_end,
            session_type=data.get("session_type", "online"),
            location=data.get("location"),
            notes=data.get("notes"),
            price_brl=price,
            payment_status="pending",
            status=SessionStatus.PENDING
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Sessão agendada: {session.id} - Usuário {user_id} com profissional {professional_id}")
        return session
    
    def confirm_session(
        self,
        db: Session,
        session_id: int,
        professional_id: int
    ) -> ProfessionalSession:
        session = db.query(ProfessionalSession).filter(
            ProfessionalSession.id == session_id,
            ProfessionalSession.professional_id == professional_id
        ).first()
        
        if not session:
            raise ValueError("Sessão não encontrada")
        
        if session.status != SessionStatus.PENDING:
            raise ValueError(f"Status atual: {session.status}, não pode confirmar")
        
        session.status = SessionStatus.CONFIRMED
        db.commit()
        db.refresh(session)
        
        return session
    
    def cancel_session(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        is_professional: bool = False
    ) -> ProfessionalSession:
        query = db.query(ProfessionalSession).filter(
            ProfessionalSession.id == session_id
        )
        
        if is_professional:
            query = query.filter(ProfessionalSession.professional.has(user_id=user_id))
        else:
            query = query.filter(ProfessionalSession.user_id == user_id)
        
        session = query.first()
        
        if not session:
            raise ValueError("Sessão não encontrada")
        
        if session.status in [SessionStatus.COMPLETED, SessionStatus.CANCELLED]:
            raise ValueError(f"Sessão já {session.status}")
        
        session.status = SessionStatus.CANCELLED
        db.commit()
        db.refresh(session)
        
        return session
    
    def complete_session(
        self,
        db: Session,
        session_id: int,
        professional_id: int,
        professional_notes: str
    ) -> ProfessionalSession:
        session = db.query(ProfessionalSession).filter(
            ProfessionalSession.id == session_id,
            ProfessionalSession.professional_id == professional_id
        ).first()
        
        if not session:
            raise ValueError("Sessão não encontrada")
        
        if session.status not in [SessionStatus.CONFIRMED, SessionStatus.IN_PROGRESS]:
            raise ValueError(f"Status atual: {session.status}, não pode completar")
        
        session.status = SessionStatus.COMPLETED
        session.professional_notes = professional_notes
        db.commit()
        db.refresh(session)
        
        return session
    
    def add_review(
        self,
        db: Session,
        user_id: int,
        data: Dict[str, Any]
    ) -> ProfessionalReview:
        professional_id = data["professional_id"]
        session_id = data.get("session_id")
        
        professional = db.query(Professional).filter(
            Professional.id == professional_id
        ).first()
        if not professional:
            raise ValueError("Profissional não encontrado")
        
        existing = db.query(ProfessionalReview).filter(
            ProfessionalReview.professional_id == professional_id,
            ProfessionalReview.user_id == user_id
        ).first()
        
        if existing:
            raise ValueError("Usuário já avaliou este profissional")
        
        is_verified = False
        if session_id:
            session = db.query(ProfessionalSession).filter(
                ProfessionalSession.id == session_id,
                ProfessionalSession.user_id == user_id,
                ProfessionalSession.professional_id == professional_id,
                ProfessionalSession.status == SessionStatus.COMPLETED
            ).first()
            
            if session:
                is_verified = True
        
        review = ProfessionalReview(
            professional_id=professional_id,
            user_id=user_id,
            session_id=session_id,
            rating=data["rating"],
            comment=data.get("comment"),
            is_verified=is_verified
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        self._update_professional_rating(db, professional_id)
        
        return review
    
    def _update_professional_rating(
        self,
        db: Session,
        professional_id: int
    ):
        result = db.query(
            func.avg(ProfessionalReview.rating).label('avg'),
            func.count(ProfessionalReview.id).label('count')
        ).filter(
            ProfessionalReview.professional_id == professional_id
        ).first()
        
        professional = db.query(Professional).filter(
            Professional.id == professional_id
        ).first()
        
        if professional:
            professional.rating_avg = result.avg or 0
            professional.rating_count = result.count or 0
            db.commit()
    
    def get_reviews(
        self,
        db: Session,
        professional_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        query = db.query(ProfessionalReview).filter(
            ProfessionalReview.professional_id == professional_id
        ).order_by(ProfessionalReview.created_at.desc())
        
        total = query.count()
        reviews = query.offset(offset).limit(limit).all()
        
        user_ids = [r.user_id for r in reviews]
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        user_map = {u.id: u.email for u in users}
        
        return {
            "total": total,
            "reviews": [
                {
                    **r.__dict__,
                    "user_name": user_map.get(r.user_id, "Usuário")
                }
                for r in reviews
            ]
        }
    
    def get_user_sessions(
        self,
        db: Session,
        user_id: int,
        status: Optional[SessionStatus] = None
    ) -> List[ProfessionalSession]:
        query = db.query(ProfessionalSession).filter(
            ProfessionalSession.user_id == user_id
        )
        
        if status:
            query = query.filter(ProfessionalSession.status == status)
        
        return query.order_by(ProfessionalSession.scheduled_date.desc()).all()
    
    def get_professional_sessions(
        self,
        db: Session,
        professional_id: int,
        status: Optional[SessionStatus] = None
    ) -> List[ProfessionalSession]:
        query = db.query(ProfessionalSession).filter(
            ProfessionalSession.professional_id == professional_id
        )
        
        if status:
            query = query.filter(ProfessionalSession.status == status)
        
        return query.order_by(ProfessionalSession.scheduled_date.desc()).all()
