"""
sentiment_stability.py - Gerenciamento de estabilidade de sentimento do Nexus Agent
Gerencia níveis de ansiedade, confusão e estabilidade com base nas interações.
"""

from dataclasses import dataclass
from typing import Optional
import time


@dataclass
class SentimentState:
    """Estado de sentimento atual do agente."""
    stability: float          # 0.0 a 1.0 (1.0 = completamente estável)
    anxiety_level: float      # 0.0 a 1.0
    confusion_level: float    # 0.0 a 1.0
    last_emotion: str
    last_stable_time: float
    last_negative_time: float


class SentimentStabilityManager:
    """
    Gerenciador de estabilidade de sentimento do Nexus Agent.
    
    A estabilidade é calculada com base nos níveis de ansiedade e confusão.
    A ansiedade aumenta com interações negativas e diminui com o tempo.
    A confusão aumenta com respostas muito longas ou interações negativas.
    """

    def __init__(self):
        current_time = time.time()
        self.state = SentimentState(
            stability=0.85,
            anxiety_level=0.0,
            confusion_level=0.0,
            last_emotion="neutro",
            last_stable_time=current_time,
            last_negative_time=current_time
        )

    def _calculate_stability(self) -> float:
        """
        Calcula a estabilidade baseada nos níveis atuais.
        Fórmula: stability = 1.0 - (anxiety * 0.6 + confusion * 0.4)
        """
        raw_stability = 1.0 - (self.state.anxiety_level * 0.6 + self.state.confusion_level * 0.4)
        return max(0.0, min(1.0, raw_stability))

    def update(self, sentiment_emotion: str, user_input: str, reply_length: int = 0) -> None:
        """
        Atualiza o estado de sentimento com base na interação.
        
        Args:
            sentiment_emotion: Emoção detectada ("positivo", "negativo", etc.)
            user_input: Texto do usuário
            reply_length: Tamanho da resposta do agente
        """
        current_time = time.time()
        is_negative = sentiment_emotion in ["negativo", "estressado"]

        # ===== ANSIEDADE =====
        if is_negative:
            self.state.anxiety_level = min(1.0, self.state.anxiety_level + 0.25)
            self.state.last_negative_time = current_time
        else:
            time_since_negative = current_time - self.state.last_negative_time
            if time_since_negative > 30:
                recovery_rate = 0.12 * (time_since_negative / 30)
                self.state.anxiety_level = max(0.0, self.state.anxiety_level - recovery_rate)
            else:
                self.state.anxiety_level = max(0.0, self.state.anxiety_level - 0.05)

        # ===== CONFUSÃO =====
        if is_negative:
            self.state.confusion_level = min(1.0, self.state.confusion_level + 0.15)
        
        if reply_length and reply_length > 1200:
            self.state.confusion_level = min(1.0, self.state.confusion_level + 0.10)
        
        self.state.confusion_level = max(0.0, self.state.confusion_level - 0.03)

        # ===== ESTABILIDADE =====
        self.state.stability = self._calculate_stability()

        self.state.last_emotion = sentiment_emotion
        self.state.last_stable_time = current_time

    def get_stability_prompt(self) -> Optional[str]:
        """
        Gera instrução de estabilidade para injetar no prompt do sistema.
        
        Returns:
            String com instruções, ou None se estiver estável
        """
        if self.state.stability > 0.75:
            return None

        if self.state.anxiety_level > 0.6:
            return ("\n[ESTABILIDADE DE SENTIMENTO]: O agente está com nível elevado de ansiedade. "
                    "Mantenha o foco em fornecer respostas claras, objetivas e profissionais. "
                    "Evite divagações e priorize a solução do problema.")

        if self.state.confusion_level > 0.5:
            return ("\n[ESTABILIDADE DE SENTIMENTO]: O agente apresenta sinais de confusão. "
                    "Priorize a simplicidade e a organização lógica da resposta. "
                    "Recomende ao usuário a revisão de dados se necessário.")

        return ("\n[ESTABILIDADE DE SENTIMENTO]: Nível de estabilidade reduzido. "
                "Responda com calma e clareza, mantendo o profissionalismo.")

    def get_status(self) -> str:
        """Retorna uma representação visual do estado de sentimento."""
        stability_pct = int(self.state.stability * 100)
        
        if self.state.stability > 0.8:
            return f"Estável ({stability_pct}%)"
        elif self.state.stability > 0.6:
            return f"Moderada ({stability_pct}%)"
        elif self.state.stability > 0.4:
            return f"Instável ({stability_pct}%)"
        else:
            return f"Crítica ({stability_pct}%)"

    def get_details(self) -> dict:
        """Retorna detalhes completos do estado para debug."""
        return {
            "stability": round(self.state.stability, 3),
            "anxiety_level": round(self.state.anxiety_level, 3),
            "confusion_level": round(self.state.confusion_level, 3),
            "last_emotion": self.state.last_emotion,
            "status": self.get_status()
        }

    def reset(self) -> None:
        """Reseta o estado de sentimento para os valores padrão."""
        current_time = time.time()
        self.state = SentimentState(
            stability=0.9,
            anxiety_level=0.0,
            confusion_level=0.0,
            last_emotion="neutro",
            last_stable_time=current_time,
            last_negative_time=current_time
        )


# Instância global
sentiment_stability = SentimentStabilityManager()