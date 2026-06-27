"""
sentiment.py - Análise de sentimento contextual para o Nexus Agent
"""

import hashlib
from typing import Dict, Optional

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dataclasses import dataclass

# Cache global do modelo (singleton)
_MODEL_CACHE = None


def get_sentiment_model() -> SentenceTransformer:
    """Singleton para o modelo de sentimentos (evita recarregar)."""
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        # Modelo multilíngue para suporte a português
        _MODEL_CACHE = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _MODEL_CACHE


@dataclass
class SentimentResult:
    emotion: str          # "positivo", "negativo", "estressado", "neutro"
    confidence: float
    needs_care: bool      # Se o usuário está estressado ou negativo
    tone_adjust: str      # "colaborativo", "suporte", "formal", "neutro"


class SentimentAnalyzer:
    """
    Analisador de sentimento contextual em português.
    Usa Sentence Transformers com modelo multilíngue.
    Detecta emoções para ajustar o tom das respostas do agente.
    """

    def __init__(self, threshold: float = 0.45):
        """
        Inicializa o analisador.
        
        Args:
            threshold: Confiança mínima para classificar como não-neutro
        """
        self.model = get_sentiment_model()
        self.threshold = threshold
        
        # Exemplos de referência por emoção (vocabulário profissional)
        self.emotion_examples = {
            "positivo": [
                "ótimo", "adorei", "muito bom", "feliz", "perfeito", "incrível",
                "maravilhoso", "excelente", "fantástico", "sensacional",
                "gostei", "curti", "legal", "show", "top", "bom demais"
            ],
            "negativo": [
                "ruim", "odeio", "cansado", "triste", "frustrado",
                "chato", "péssimo", "horrível", "detesto", "aborrecido", "chateado",
                "decepcionado", "desanimado"
            ],
            "estressado": [
                "estressado", "muito cansado", "sobrecarregado",
                "não aguento mais", "pressão", "ansioso", "nervoso",
                "estressante", "saturado", "esgotado", "irritado", "tenso"
            ],
            "neutro": [
                "ok", "normal", "tudo bem", "ajuda", "código", 
                "trabalho", "técnico", "como", "porque", "quando",
                "onde", "qual", "pode", "fazer", "ajudar"
            ]
        }
        
        # Pré-calcula embeddings (em cache)
        self.emotion_embeddings = {}
        for emotion, examples in self.emotion_examples.items():
            if examples:
                self.emotion_embeddings[emotion] = self.model.encode(examples)
        
        # Cache para textos já analisados (LRU)
        self._text_cache = {}
        self._cache_max_size = 100

    def _get_cached_embedding(self, text: str):
        """Retorna embedding do cache ou calcula e armazena."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if text_hash in self._text_cache:
            return self._text_cache[text_hash]
        
        # Trunca texto se muito longo (512 tokens ~ 2000 caracteres)
        if len(text) > 2000:
            text = text[:2000]
        
        embedding = self.model.encode([text])[0]
        
        # Mantém cache limitado
        if len(self._text_cache) >= self._cache_max_size:
            oldest_key = next(iter(self._text_cache))
            del self._text_cache[oldest_key]
        
        self._text_cache[text_hash] = embedding
        return embedding

    def analyze(self, text: str) -> SentimentResult:
        """
        Analisa o sentimento do texto.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            SentimentResult com emoção, confiança e ajustes de tom
        """
        if not text or len(text.strip()) < 3:
            return SentimentResult("neutro", 1.0, False, "neutro")

        text_emb = self._get_cached_embedding(text)
        best_emotion = "neutro"
        best_score = 0.0

        for emotion, embeddings in self.emotion_embeddings.items():
            similarities = cosine_similarity([text_emb], embeddings)[0]
            max_sim = float(similarities.max())
            if max_sim > best_score:
                best_score = max_sim
                best_emotion = emotion

        confidence = round(best_score, 3)
        
        # Se confiança for menor que o threshold, força NEUTRO
        if confidence < self.threshold:
            best_emotion = "neutro"
            confidence = 1.0 - self.threshold

        needs_care = best_emotion in ["negativo", "estressado"]
        
        # Ajuste de tom para resposta do agente
        tone_map = {
            "positivo": "colaborativo",
            "negativo": "suporte",
            "estressado": "suporte",
            "neutro": "neutro"
        }
        tone_adjust = tone_map.get(best_emotion, "neutro")

        return SentimentResult(
            emotion=best_emotion,
            confidence=confidence,
            needs_care=needs_care,
            tone_adjust=tone_adjust
        )

    def get_emotion_intensity(self, text: str) -> Dict[str, float]:
        """
        Retorna o score para cada emoção (útil para debug).
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Dict com emoção -> score
        """
        if not text or len(text.strip()) < 3:
            return {"neutro": 1.0}
        
        text_emb = self._get_cached_embedding(text)
        scores = {}
        
        for emotion, embeddings in self.emotion_embeddings.items():
            similarities = cosine_similarity([text_emb], embeddings)[0]
            scores[emotion] = float(similarities.max())
        
        return scores

    def add_custom_example(self, emotion: str, example: str) -> None:
        """
        Adiciona um exemplo personalizado para uma emoção.
        
        Args:
            emotion: Emoção (positivo, negativo, estressado, neutro)
            example: Exemplo de texto para aquela emoção
        """
        if emotion not in self.emotion_examples:
            raise ValueError(f"Emoção inválida: {emotion}")
        
        self.emotion_examples[emotion].append(example)
        # Recalcula embeddings para esta emoção
        self.emotion_embeddings[emotion] = self.model.encode(self.emotion_examples[emotion])