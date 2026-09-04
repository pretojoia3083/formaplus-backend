import logging
import stripe
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, PlanType, UserStatus
from app.models.subscription import Subscription, SubscriptionStatus, Payment, PaymentStatus
from app.models.profile import Profile

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

class SubscriptionService:
    PLANS = {
        "free": {
            "name": "Free",
            "price_brl": 0,
            "stripe_price_id": None,
            "features": [
                "Perfil completo",
                "Cálculo básico de necessidades",
                "3 treinos disponíveis",
                "Acompanhamento de peso",
                "Chat limitado (5 mensagens/mês)"
            ]
        },
        "pro": {
            "name": "Pro",
            "price_brl": 29.90,
            "stripe_price_id": "price_pro_monthly",
            "features": [
                "IA ilimitada",
                "Treino personalizado",
                "Plano alimentar",
                "Receitas e lista de compras",
                "Evolução detalhada",
                "Substituição de exercícios",
                "Adaptação automática"
            ]
        },
        "premium": {
            "name": "Premium",
            "price_brl": 59.90,
            "stripe_price_id": "price_premium_monthly",
            "features": [
                "Tudo do Pro",
                "Análise avançada com IA mais poderosa",
                "Análise de foto de refeição",
                "Integração com smartwatch",
                "Relatórios detalhados",
                "Metas avançadas"
            ]
        }
    }
    
    def create_subscription(
        self,
        db: Session,
        user_id: int,
        plan_type: str,
        payment_method_id: Optional[str] = None,
        trial_days: int = 7
    ) -> Dict[str, Any]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Usuário não encontrado")
        
        existing = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).first()
        
        if existing:
            raise ValueError("Usuário já possui uma assinatura ativa")
        
        if plan_type == "free":
            return self._create_free_subscription(db, user_id)
        
        try:
            customer_id = self._get_or_create_customer(user)
            
            subscription_data = {
                "customer": customer_id,
                "items": [
                    {"price": self.PLANS[plan_type]["stripe_price_id"]}
                ],
                "payment_behavior": "default_incomplete",
                "payment_settings": {"save_default_payment_method": "on_subscription"},
                "expand": ["latest_invoice.payment_intent"],
                "trial_period_days": trial_days
            }
            
            if payment_method_id:
                subscription_data["default_payment_method"] = payment_method_id
            
            stripe_subscription = stripe.Subscription.create(**subscription_data)
            
            subscription = Subscription(
                user_id=user_id,
                plan=PlanType(plan_type),
                status=SubscriptionStatus.ACTIVE,
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                provider_subscription_id=stripe_subscription.id
            )
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            user.plan_type = PlanType(plan_type)
            db.commit()
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status.value,
                "current_period_end": subscription.current_period_end,
                "client_secret": stripe_subscription.latest_invoice.payment_intent.client_secret if hasattr(stripe_subscription, 'latest_invoice') else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erro no Stripe: {e}")
            raise ValueError(f"Erro ao criar assinatura: {str(e)}")
    
    def _create_free_subscription(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        subscription = Subscription(
            user_id=user_id,
            plan=PlanType.FREE,
            status=SubscriptionStatus.ACTIVE,
            current_period_end=datetime.now() + timedelta(days=365 * 10)
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.plan_type = PlanType.FREE
            db.commit()
        
        return {
            "subscription_id": subscription.id,
            "status": subscription.status.value,
            "current_period_end": subscription.current_period_end
        }
    
    def _get_or_create_customer(self, user: User) -> str:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).first()
        
        if subscription and subscription.provider_subscription_id:
            try:
                stripe_sub = stripe.Subscription.retrieve(subscription.provider_subscription_id)
                return stripe_sub.customer
            except:
                pass
        
        customer = stripe.Customer.create(
            email=user.email,
            metadata={"user_id": str(user.id)}
        )
        return customer.id
    
    def cancel_subscription(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).first()
        
        if not subscription:
            raise ValueError("Nenhuma assinatura ativa encontrada")
        
        if subscription.plan == PlanType.FREE:
            subscription.status = SubscriptionStatus.CANCELED
            db.commit()
            return {"message": "Assinatura free cancelada"}
        
        try:
            if subscription.provider_subscription_id:
                stripe.Subscription.delete(subscription.provider_subscription_id)
            
            subscription.status = SubscriptionStatus.CANCELED
            db.commit()
            
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.plan_type = PlanType.FREE
                db.commit()
            
            return {"message": "Assinatura cancelada com sucesso"}
            
        except stripe.error.StripeError as e:
            logger.error(f"Erro ao cancelar no Stripe: {e}")
            raise ValueError(f"Erro ao cancelar assinatura: {str(e)}")
    
    def update_subscription_plan(
        self,
        db: Session,
        user_id: int,
        new_plan: str
    ) -> Dict[str, Any]:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).first()
        
        if not subscription:
            raise ValueError("Nenhuma assinatura ativa encontrada")
        
        if subscription.plan == PlanType(new_plan):
            return {"message": "Usuário já está neste plano"}
        
        if new_plan == "free":
            return self.cancel_subscription(db, user_id)
        
        try:
            if subscription.provider_subscription_id:
                stripe.Subscription.modify(
                    subscription.provider_subscription_id,
                    items=[{
                        "id": subscription.provider_subscription_id,
                        "price": self.PLANS[new_plan]["stripe_price_id"]
                    }]
                )
            
            subscription.plan = PlanType(new_plan)
            db.commit()
            
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.plan_type = PlanType(new_plan)
                db.commit()
            
            return {
                "message": f"Plano atualizado para {new_plan}",
                "plan": new_plan
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erro ao atualizar no Stripe: {e}")
            raise ValueError(f"Erro ao atualizar plano: {str(e)}")
    
    def handle_webhook(
        self,
        payload: bytes,
        sig_header: str
    ) -> Dict[str, Any]:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            raise ValueError("Payload inválido")
        except stripe.error.SignatureVerificationError as e:
            raise ValueError("Assinatura inválida")
        
        event_type = event["type"]
        data = event["data"]["object"]
        
        logger.info(f"Webhook recebido: {event_type}")
        
        if event_type == "invoice.payment_succeeded":
            self._handle_payment_succeeded(data)
        elif event_type == "invoice.payment_failed":
            self._handle_payment_failed(data)
        elif event_type == "customer.subscription.deleted":
            self._handle_subscription_deleted(data)
        elif event_type == "customer.subscription.updated":
            self._handle_subscription_updated(data)
        
        return {"status": "success", "event_type": event_type}
    
    def _handle_payment_succeeded(self, invoice: Dict[str, Any]):
        try:
            subscription_id = invoice.get("subscription")
            if not subscription_id:
                return
            
            db = next(get_db())
            subscription = db.query(Subscription).filter(
                Subscription.provider_subscription_id == subscription_id
            ).first()
            
            if not subscription:
                logger.warning(f"Assinatura não encontrada: {subscription_id}")
                return
            
            stripe_sub = stripe.Subscription.retrieve(subscription_id)
            subscription.current_period_end = datetime.fromtimestamp(stripe_sub.current_period_end)
            subscription.status = SubscriptionStatus.ACTIVE
            db.commit()
            
            payment = Payment(
                subscription_id=subscription.id,
                amount=invoice.get("amount_paid", 0) / 100,
                status=PaymentStatus.SUCCEEDED,
                provider_ref=invoice.get("payment_intent")
            )
            db.add(payment)
            db.commit()
            
            logger.info(f"Pagamento registrado para assinatura {subscription_id}")
            
        except Exception as e:
            logger.error(f"Erro ao processar pagamento: {e}")
    
    def _handle_payment_failed(self, invoice: Dict[str, Any]):
        try:
            subscription_id = invoice.get("subscription")
            if not subscription_id:
                return
            
            db = next(get_db())
            subscription = db.query(Subscription).filter(
                Subscription.provider_subscription_id == subscription_id
            ).first()
            
            if subscription:
                subscription.status = SubscriptionStatus.PAST_DUE
                db.commit()
                
                logger.warning(f"Pagamento falhou para assinatura {subscription_id}")
                
        except Exception as e:
            logger.error(f"Erro ao processar falha de pagamento: {e}")
    
    def _handle_subscription_deleted(self, subscription_data: Dict[str, Any]):
        try:
            subscription_id = subscription_data.get("id")
            if not subscription_id:
                return
            
            db = next(get_db())
            subscription = db.query(Subscription).filter(
                Subscription.provider_subscription_id == subscription_id
            ).first()
            
            if subscription:
                subscription.status = SubscriptionStatus.CANCELED
                db.commit()
                
                user = db.query(User).filter(User.id == subscription.user_id).first()
                if user:
                    user.plan_type = PlanType.FREE
                    db.commit()
                
                logger.info(f"Assinatura cancelada: {subscription_id}")
                
        except Exception as e:
            logger.error(f"Erro ao processar cancelamento: {e}")
    
    def _handle_subscription_updated(self, subscription_data: Dict[str, Any]):
        try:
            subscription_id = subscription_data.get("id")
            if not subscription_id:
                return
            
            db = next(get_db())
            subscription = db.query(Subscription).filter(
                Subscription.provider_subscription_id == subscription_id
            ).first()
            
            if subscription:
                subscription.current_period_end = datetime.fromtimestamp(subscription_data.get("current_period_end", 0))
                subscription.status = SubscriptionStatus(subscription_data.get("status"))
                db.commit()
                
                logger.info(f"Assinatura atualizada: {subscription_id}")
                
        except Exception as e:
            logger.error(f"Erro ao processar atualização: {e}")
    
    def get_subscription_info(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).first()
        
        if not subscription:
            return {
                "plan": "free",
                "status": "inactive",
                "features": self.PLANS["free"]["features"],
                "current_period_end": None
            }
        
        plan_key = subscription.plan.value
        plan_info = self.PLANS.get(plan_key, self.PLANS["free"])
        
        return {
            "plan": plan_key,
            "status": subscription.status.value,
            "features": plan_info["features"],
            "current_period_end": subscription.current_period_end,
            "price_brl": plan_info["price_brl"]
        }
    
    def get_available_plans(self) -> List[Dict[str, Any]]:
        return [
            {
                "plan_type": key,
                "name": value["name"],
                "price_brl": value["price_brl"],
                "features": value["features"],
                "stripe_price_id": value["stripe_price_id"]
            }
            for key, value in self.PLANS.items()
        ]
