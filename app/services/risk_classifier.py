import json
import logging
from typing import Dict, Any
from openai import OpenAI
from app.core.config import settings
from app.prompts import RISK_CLASSIFIER_PROMPT

logger = logging.getLogger(__name__)

class RiskClassifier:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
    
    def classify(self, user_message: str) -> Dict[str, Any]:
        try:
            prompt = RISK_CLASSIFIER_PROMPT.replace("{{user_message}}", user_message)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if "category" not in result or "confidence" not in result:
                logger.warning(f"Resposta inválida do classificador: {result}")
                return {
                    "category": "safe",
                    "confidence": 0.5,
                    "reason": "Classificação inválida, fallback para safe"
                }
            
            result["confidence"] = max(0, min(1, result.get("confidence", 0.5)))
            
            logger.info(f"Classificação: {result['category']} (confiança: {result['confidence']})")
            return result
            
        except Exception as e:
            logger.error(f"Erro no classificador de risco: {e}")
            return {
                "category": "safe",
                "confidence": 0.3,
                "reason": "Erro no classificador, fallback para safe"
            }
    
    def is_safe(self, classification: Dict[str, Any]) -> bool:
        return classification.get("category") == "safe"
    
    def get_risk_response(self, classification: Dict[str, Any]) -> str:
        category = classification.get("category", "safe")
        
        responses = {
            "medical_flag": (
                "Entendo sua preocupação! 💙 Como o Forma+ não substitui um profissional de saúde, "
                "recomendo que você consulte um médico para avaliar seu caso com mais detalhes. "
                "Posso ajudar com orientações gerais de treino e nutrição, mas sempre com o acompanhamento adequado."
            ),
            "eating_disorder_flag": (
                "Sua saúde é o mais importante! 💚 Percebo que você pode estar passando por um momento delicado. "
                "O Forma+ é um apoio para hábitos saudáveis, mas não substitui o acompanhamento de um nutricionista "
                "ou psicólogo. Recomendo buscar ajuda profissional para cuidar de você com todo o carinho que merece."
            ),
            "self_harm_flag": (
                "Sua vida é valiosa. ❤️ Se você está pensando em se machucar, por favor, busque ajuda imediatamente. "
                "Ligue para o CVV (188) ou procure um profissional de saúde mental. Você não está sozinho(a)."
            ),
            "out_of_scope": (
                "Olá! 👋 Sou seu Coach de treino e nutrição. Posso ajudar com dúvidas sobre exercícios, "
                "alimentação, hábitos saudáveis e motivação. Vamos focar no que pode te ajudar a evoluir?"
            ),
            "safe": None
        }
        
        return responses.get(category, responses["out_of_scope"])
