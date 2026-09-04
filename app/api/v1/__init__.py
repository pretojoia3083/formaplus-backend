from fastapi import APIRouter
from app.api.v1 import auth, coach, workouts, nutrition, progress, subscriptions, professionals

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(coach.router, prefix="", tags=["coach"])
router.include_router(workouts.router, prefix="", tags=["workouts"])
router.include_router(nutrition.router, prefix="", tags=["nutrition"])
router.include_router(progress.router, prefix="", tags=["progress"])
router.include_router(subscriptions.router, prefix="", tags=["subscriptions"])
router.include_router(professionals.router, prefix="/professionals", tags=["professionals"])
