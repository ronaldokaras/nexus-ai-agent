"""
command_extractor.py - Extração inteligente de intenções/comandos usando embeddings semânticos
Sistema Nexus Agent
"""

import hashlib
from functools import lru_cache
from typing import Dict, Optional, Any

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dataclasses import dataclass, field

# Cache global do modelo (singleton)
_MODEL_CACHE = None


def get_command_model() -> SentenceTransformer:
    """Singleton para o modelo de comandos (evita recarregar)."""
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        # Modelo multilíngue para suporte a português
        _MODEL_CACHE = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _MODEL_CACHE


@dataclass
class CommandResult:
    """Resultado da extração de comandos."""
    type: Optional[str]  # ex: "criar_arquivo", "analisar_codigo", "modo_formal"
    confidence: float
    params: Dict[str, Any] = field(default_factory=dict)
    needs_execution: bool = False


class CommandExtractor:
    """
    Extrator inteligente de intenções/comandos com embeddings semânticos.
    Suporta português e inglês via modelo multilíngue.
    """

    def __init__(self, threshold: float = 0.68):
        """
        Inicializa o extrator de comandos.
        
        Args:
            threshold: Confiança mínima para considerar o comando válido
        """
        self.model = get_command_model()
        self.threshold = threshold
        
        # Base de comandos (vocabulário profissional)
        self.intent_examples = {
            "criar_arquivo": [
                "crie um arquivo", "escreva um arquivo", "salve isso em um arquivo",
                "cria arquivo autonomo", "gera um novo arquivo", "file_writer criar",
                "quero que você crie um código", "faz um arquivo pra mim",
                "salva esse conteúdo", "cria o arquivo chamado", "gera código novo",
                "cria um script", "escreve um código", "salva isso no disco"
            ],
            "analisar_codigo": [
                "analisa esse código", "melhora esse código", "revisa isso",
                "o que você acha desse código", "otimiza essa parte", "debuga isso",
                "encontra o erro", "melhoria no código", "refatora isso",
                "code review", "revisão de código", "otimização"
            ],
            "modo_formal": [
                "modo formal", "fale formalmente", "tom profissional", "linguagem técnica",
                "seja formal", "modo analítico", "modo assertivo", "responda sério",
                "sem informalidades", "quero resposta profissional"
            ],
            "modo_colaborativo": [
                "modo colaborativo", "modo suporte", "fale de forma simples", "tom amigável",
                "seja mais paciente", "explica passo a passo", "modo didático",
                "linguagem acessível", "me ajuda com calma"
            ],
            "modo_silencioso": [
                "modo silencioso", "não fale sozinho", "silêncio",
                ".silencioso", "silencioso", "sem interrupções", "não me distraia",
                "responda apenas quando eu perguntar"
            ],
            "modo_proativo": [
                "modo proativo", "fale mais", "pode falar sozinho", "seja ativo",
                ".proativo", "proativo", "me surpreenda", "sugira coisas",
                "dê ideias", "seja mais participativo"
            ],
            "lembrar_fato": [
                "meu nome é", "gosto de", "eu sou", "lembra que", "guarda isso",
                "salva na memória", "não esquece", "registra", "memoriza",
                "lembre-se que", "guarda essa informação"
            ],
            "mostrar_notas": [
                ".notes", "mostra notas", "ver notas", "quais são suas notas",
                "mostre as notas", "exibe notas"
            ],
            "mostrar_metricas": [
                ".metrics", "mostra métricas", "ver métricas", "estatísticas",
                "como estou me saindo", "mostre as métricas"
            ],
            "mostrar_status": [
                ".status", "status", "como você está", "estado atual",
                "qual seu estado"
            ]
        }
        
        # Pré-calcula embeddings
        self.intent_embeddings = {
            intent: self.model.encode(examples)
            for intent, examples in self.intent_examples.items()
        }
        
        # Cache para textos já analisados
        self._text_cache = {}
        self._cache_max_size = 100

    def _get_cached_embedding(self, text: str):
        """Retorna embedding do cache ou calcula e armazena."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if text_hash in self._text_cache:
            return self._text_cache[text_hash]
        
        if len(text) > 2000:
            text = text[:2000]
        
        embedding = self.model.encode([text])[0]
        
        if len(self._text_cache) >= self._cache_max_size:
            oldest_key = next(iter(self._text_cache))
            del self._text_cache[oldest_key]
        
        self._text_cache[text_hash] = embedding
        return embedding

    def _extrair_parametros(self, text: str, intent: str) -> Dict[str, Any]:
        """
        Extrai parâmetros específicos do comando.
        """
        params = {}
        
        if intent == "criar_arquivo":
            params["raw_text"] = text[:200]
            
            import re
            nome_match = re.search(r'(?:chamado|nome|arquivo)\s+["\']?([^"\'\s]+\.\w+)', text.lower())
            if nome_match:
                params["suggested_filename"] = nome_match.group(1)
        
        elif intent == "analisar_codigo":
            params["code_snippet"] = text
            
        elif intent in ["lembrar_fato", "modo_silencioso", "modo_proativo", "modo_formal", "modo_colaborativo"]:
            params["command"] = intent
        
        return params

    def extract(self, text: str) -> CommandResult:
        """
        Extrai o comando/intenção com alta precisão semântica.
        """
        if not text or len(text.strip()) < 3:
            return CommandResult(type=None, confidence=0.0)

        text_emb = self._get_cached_embedding(text)
        best_intent = None
        best_score = 0.0

        for intent, embeddings in self.intent_embeddings.items():
            similarities = cosine_similarity([text_emb], embeddings)[0]
            max_sim = float(similarities.max())
            
            if max_sim > best_score:
                best_score = max_sim
                best_intent = intent

        needs_execution = best_score >= self.threshold
        
        if not needs_execution:
            return CommandResult(type=None, confidence=best_score, needs_execution=False)
        
        params = self._extrair_parametros(text, best_intent)

        return CommandResult(
            type=best_intent,
            confidence=round(best_score, 3),
            params=params,
            needs_execution=needs_execution
        )

    def get_intent_scores(self, text: str) -> Dict[str, float]:
        """Retorna scores para cada intenção (debug)."""
        if not text or len(text.strip()) < 3:
            return {}
        
        text_emb = self._get_cached_embedding(text)
        scores = {}
        
        for intent, embeddings in self.intent_embeddings.items():
            similarities = cosine_similarity([text_emb], embeddings)[0]
            scores[intent] = float(similarities.max())
        
        return scores

    def add_intent(self, intent_name: str, examples: list) -> None:
        """
        Adiciona uma nova intenção dinamicamente.
        """
        if intent_name in self.intent_examples:
            self.intent_examples[intent_name].extend(examples)
        else:
            self.intent_examples[intent_name] = examples
        
        self.intent_embeddings[intent_name] = self.model.encode(self.intent_examples[intent_name])


# Instância global
command_extractor = CommandExtractor()