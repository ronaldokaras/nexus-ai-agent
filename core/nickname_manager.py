"""
nickname_manager.py - Gerenciador de termos personalizados do Nexus Agent
Permite que o usuário defina termos de tratamento (ex: "senhor", "chefe", "equipe") 
e o agente os reconheça em conversas.
"""

import re
import json
from pathlib import Path
from typing import List, Set, Optional
from dataclasses import dataclass

# Cache global do modelo (carregado sob demanda)
_MODEL = None


def _get_model():
    """Carrega o modelo sob demanda (evita carregar se não for usado)."""
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        # Modelo multilíngue para suporte a português
        _MODEL = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _MODEL


@dataclass
class TermResult:
    """Resultado da extração e correção de termo de tratamento."""
    original: str
    corrected: str
    confidence: float
    is_known: bool


class TermManager:
    """
    Gerenciador de termos de tratamento personalizados.
    
    Reconhece padrões como "senhor", "chefe", "equipe", "você", etc.
    Aprende novos termos dinamicamente e persiste em JSON.
    """

    def __init__(self):
        self.file_path = Path("build/terms_memory.json")
        
        # Termos de tratamento conhecidos (base + aprendidos)
        self.known_terms: Set[str] = {
            "senhor", "chefe", "equipe", "você", "colega",
            "parceiro", "cliente", "usuário", "operador", "admin"
        }
        
        # Padrões de regex expandidos
        self.patterns = [
            re.compile(r'(meu|minha|nossa|nosso)\s+([a-zA-ZçÇáéíóúãõâêîôûàèìòù\']{2,20})', re.IGNORECASE),
            re.compile(r'(o|a)\s+([a-zA-ZçÇáéíóúãõâêîôûàèìòù\']{2,20})', re.IGNORECASE),
        ]
        
        self._load_memory()

    def _load_memory(self) -> None:
        """Carrega termos aprendidos do arquivo JSON."""
        if self.file_path.exists():
            try:
                data = json.loads(self.file_path.read_text(encoding="utf-8"))
                self.known_terms.update(data.get("terms", []))
            except Exception as e:
                print(f"⚠️ Erro ao carregar termos: {e}")

    def _save_memory(self) -> None:
        """Salva termos aprendidos no arquivo JSON."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"terms": list(self.known_terms)}
            self.file_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), 
                encoding="utf-8"
            )
        except Exception as e:
            print(f"⚠️ Erro ao salvar termos: {e}")

    def _clean_term(self, text: str) -> str:
        """
        Limpa emojis e caracteres especiais mantendo o significado.
        Preserva apóstrofos e acentos.
        """
        # Remove emojis
        text = re.sub(r'[\U0001F000-\U0001FFFF]', '', text)
        # Remove caracteres especiais (exceto letras, números, apóstrofo, espaço, acentos)
        text = re.sub(r'[^a-zA-Z0-9çÇáéíóúãõâêîôûàèìòù\'\s]', '', text.lower().strip())
        # Remove espaços extras
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def learn_new_term(self, term: str) -> bool:
        """
        Aprende um novo termo de tratamento usado pelo usuário.
        
        Returns:
            True se aprendeu, False se já existia ou inválido
        """
        clean = self._clean_term(term)
        
        # Validação: termo muito curto ou muito longo
        if not clean or len(clean) < 2 or len(clean) > 30:
            return False
        
        # Evita palavras comuns que não são termos de tratamento
        common_words = {"meu", "minha", "o", "a", "um", "uma", "de", "para", "com"}
        if clean in common_words:
            return False
        
        if clean not in self.known_terms:
            self.known_terms.add(clean)
            self._save_memory()
            return True
        return False

    def extract_terms(self, text: str) -> List[str]:
        """
        Extrai todos os possíveis termos de tratamento do texto.
        
        Returns:
            Lista de termos encontrados
        """
        terms = []
        
        for pattern in self.patterns:
            matches = pattern.findall(text)
            for match in matches:
                # match pode ser tupla (prefixo, termo) ou apenas termo
                if isinstance(match, tuple):
                    term = match[-1]  # pega o último elemento
                else:
                    term = match
                
                clean = self._clean_term(term)
                if clean and len(clean) >= 2 and clean not in terms:
                    terms.append(clean)
        
        return terms

    def extract_and_correct(self, text: str, threshold: float = 0.75) -> TermResult:
        """
        Extrai e corrige termos de tratamento com alta precisão.
        
        Retorna o primeiro termo encontrado (ou o mais relevante).
        """
        terms = self.extract_terms(text)
        
        if not terms:
            return TermResult(original="", corrected="", confidence=0.0, is_known=False)
        
        # Pega o primeiro termo encontrado
        original = terms[0]
        clean_original = original

        # Se já conhecemos, retorna direto
        if clean_original in self.known_terms:
            return TermResult(
                original=original, 
                corrected=clean_original, 
                confidence=1.0, 
                is_known=True
            )

        # Correção inteligente com embeddings (apenas se houver termos conhecidos)
        best_match = ""
        best_score = 0.0

        known_list = list(self.known_terms)
        if known_list:
            model = _get_model()  # carrega sob demanda
            emb_original = model.encode([clean_original])[0]
            emb_known = model.encode(known_list)
            
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity([emb_original], emb_known)[0]

            best_idx = int(similarities.argmax())
            best_score = float(similarities[best_idx])
            best_match = known_list[best_idx] if best_score >= threshold else ""

        corrected = best_match if best_match else clean_original

        # Aprende o novo termo (sempre que for usado)
        if clean_original not in self.known_terms:
            self.learn_new_term(clean_original)

        return TermResult(
            original=original,
            corrected=corrected,
            confidence=round(best_score, 3),
            is_known=corrected in self.known_terms
        )

    def get_known_terms(self) -> List[str]:
        """Retorna a lista de termos de tratamento conhecidos."""
        return sorted(list(self.known_terms))

    def get_summary(self) -> dict:
        """Retorna um resumo do gerenciador de termos."""
        return {
            "total_terms": len(self.known_terms),
            "terms": self.get_known_terms()[:20],  # apenas 20 primeiros
            "has_model_loaded": _MODEL is not None
        }

    def reset(self) -> None:
        """Reseta os termos aprendidos (mantém os padrão)."""
        default_terms = {
            "senhor", "chefe", "equipe", "você", "colega",
            "parceiro", "cliente", "usuário", "operador", "admin"
        }
        self.known_terms = default_terms
        self._save_memory()


# Instância global
term_manager = TermManager()