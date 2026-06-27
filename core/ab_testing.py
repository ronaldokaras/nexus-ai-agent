"""
ab_testing.py - Sistema de Testes A/B para otimização contínua do Nexus Agent
Permite testar diferentes variantes de personalidade e medir qual performa melhor.
"""

import json
import random
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
from rich.console import Console

console = Console()


@dataclass
class ABVariant:
    """Representa uma variante de teste A/B."""
    variant_id: str
    name: str
    description: str
    prompt_modifier: str          # Texto extra no system prompt
    temperature: float
    max_tokens: int
    active: bool = True
    wins: int = 0
    total_uses: int = 0
    _length_sum: float = 0.0      # Soma para cálculo correto da média
    last_used: str = None

    @property
    def avg_length(self) -> float:
        """Retorna o tamanho médio da resposta."""
        if self.total_uses == 0:
            return 0.0
        return self._length_sum / self.total_uses

    @property
    def win_rate(self) -> float:
        """Retorna a taxa de vitória como porcentagem."""
        if self.total_uses == 0:
            return 0.0
        return (self.wins / self.total_uses) * 100


class ABTestingManager:
    """
    Sistema de Testes A/B para otimização contínua do Nexus Agent.
    
    Distribui aleatoriamente variantes de personalidade e rastreia
    qual oferece melhor experiência com base em heurísticas de qualidade.
    """

    def __init__(self):
        self.versions_dir = Path("build/ab_tests")
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = self.versions_dir / "ab_tests.json"
        self.variants: Dict[str, ABVariant] = {}
        self._load()

        # Cria variantes iniciais se não existirem
        self._create_default_variants()

    def _load(self) -> None:
        """Carrega variantes do arquivo JSON."""
        if self.data_file.exists():
            try:
                data = json.loads(self.data_file.read_text(encoding="utf-8"))
                for vid, vdata in data.items():
                    self.variants[vid] = ABVariant(**vdata)
            except Exception as e:
                console.print(f"[yellow]⚠️ Erro ao carregar AB tests: {e}[/yellow]")
                self.variants = {}

    def _save(self) -> None:
        """Salva variantes no arquivo JSON."""
        try:
            data = {}
            for vid, var in self.variants.items():
                var_dict = asdict(var)
                data[vid] = var_dict
            self.data_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), 
                encoding="utf-8"
            )
        except Exception as e:
            console.print(f"[red]❌ Erro ao salvar AB tests: {e}[/red]")

    def _create_default_variants(self) -> None:
        """Cria as variantes padrão alinhadas à arquitetura multi‑persona do Nexus."""
        if self.variants:
            return

        variants = [
            ABVariant(
                variant_id="A",
                name="Perfil Analítico/Assertivo",
                description="Tom direto, técnico e orientado a resultados",
                prompt_modifier="Responda de forma concisa, técnica e direta. Priorize fatos, dados e objetividade.",
                temperature=0.65,
                max_tokens=1500
            ),
            ABVariant(
                variant_id="B",
                name="Perfil Colaborativo/Suporte",
                description="Tom acessível, paciente e encorajador",
                prompt_modifier="Adote um tom amigável e paciente. Explique passo a passo, usando linguagem acessível e demonstrando empatia profissional.",
                temperature=0.75,
                max_tokens=1600
            ),
            ABVariant(
                variant_id="C",
                name="Perfil Adaptativo (Padrão)",
                description="Equilíbrio entre análise, suporte e proatividade, com ajuste automático pelo sentimento",
                prompt_modifier="Mantenha um equilíbrio entre clareza técnica e tom acolhedor. Adapte-se ao contexto e à análise de sentimento da conversa.",
                temperature=0.70,
                max_tokens=1500
            )
        ]

        for v in variants:
            self.variants[v.variant_id] = v

        self._save()

    def get_variant(self, variant_id: str = None, force_random: bool = False) -> ABVariant:
        """
        Retorna uma variante.
        
        Args:
            variant_id: ID específico (A, B, C). Se None, usa aleatório.
            force_random: Se True, ignora variant_id e escolhe aleatório.
            
        Returns:
            ABVariant selecionada
        """
        if force_random or variant_id is None:
            active_variants = [v for v in self.variants.values() if v.active]
            if not active_variants:
                active_variants = list(self.variants.values())
            return random.choice(active_variants)
        
        if variant_id in self.variants:
            return self.variants[variant_id]
        
        active_variants = [v for v in self.variants.values() if v.active]
        return active_variants[0] if active_variants else list(self.variants.values())[0]

    def record_interaction(self, variant_id: str, reply: str) -> None:
        """
        Registra o resultado de uma interação para análise posterior.
        
        Args:
            variant_id: ID da variante usada
            reply: Resposta do agente
        """
        if variant_id not in self.variants:
            return

        variant = self.variants[variant_id]
        variant.total_uses += 1
        variant._length_sum += len(reply)
        variant.last_used = datetime.now().strftime("%Y-%m-%d %H:%M")

        quality_score = self._calculate_quality_score(reply)
        
        if quality_score > 0.6:
            variant.wins += 1

        self._save()

    def _calculate_quality_score(self, reply: str) -> float:
        """
        Calcula um score de qualidade profissional para a resposta (0.0 a 1.0).
        
        Critérios:
        - Presença de indicadores de resultado (✅, "pronto", "feito", etc.)
        - Tamanho adequado da resposta
        - Estruturação (quebras de linha, pontuação)
        - Emojis informativos (não emocionais)
        """
        score = 0.0
        
        # Indicadores de conclusão/resultado (peso 0.3)
        success_markers = ["✅", "pronto", "feito", "criado", "salvo", "arquivo", "código", "📁", "📊", "🔧"]
        marker_count = sum(1 for m in success_markers if m in reply)
        score += min(0.3, marker_count * 0.1)
        
        # Tamanho adequado (peso 0.3)
        reply_len = len(reply)
        if 100 < reply_len < 1200:
            score += 0.3
        elif 50 < reply_len < 1500:
            score += 0.15
        
        # Estrutura e clareza (peso 0.2)
        if "\n" in reply:
            score += 0.1
        if reply.count(".") > 3 or reply.count("!") > 1 or reply.count("?") > 0:
            score += 0.1
        
        # Conteúdo útil (peso 0.2) – palavras-chave de entrega de valor
        useful_keywords = ["análise", "sugestão", "recomendação", "resultado", "relatório", "otimização", "passo", "explicação", "resumo"]
        if any(word in reply.lower() for word in useful_keywords):
            score += 0.2
        
        return min(1.0, score)

    def add_variant(
        self, 
        variant_id: str, 
        name: str, 
        description: str, 
        prompt_modifier: str, 
        temperature: float = 0.75, 
        max_tokens: int = 1500
    ) -> bool:
        """
        Adiciona uma nova variante de teste.
        
        Args:
            variant_id: ID único da variante
            name: Nome amigável
            description: Descrição do que a variante faz
            prompt_modifier: Texto extra para o system prompt
            temperature: Temperatura da API
            max_tokens: Máximo de tokens
            
        Returns:
            True se adicionada com sucesso
        """
        if variant_id in self.variants:
            console.print(f"[red]❌ Variante {variant_id} já existe.[/red]")
            return False
        
        self.variants[variant_id] = ABVariant(
            variant_id=variant_id,
            name=name,
            description=description,
            prompt_modifier=prompt_modifier,
            temperature=temperature,
            max_tokens=max_tokens
        )
        self._save()
        console.print(f"[bold green]✅ Variante {variant_id} adicionada: {name}[/bold green]")
        return True

    def reset_stats(self, variant_id: str = None) -> None:
        """
        Reseta as estatísticas de uma ou todas as variantes.
        
        Args:
            variant_id: ID específico ou None para todas
        """
        if variant_id:
            if variant_id in self.variants:
                v = self.variants[variant_id]
                v.wins = 0
                v.total_uses = 0
                v._length_sum = 0.0
                console.print(f"[bold yellow]🔄 Estatísticas da variante {variant_id} resetadas.[/bold yellow]")
        else:
            for v in self.variants.values():
                v.wins = 0
                v.total_uses = 0
                v._length_sum = 0.0
            console.print(f"[bold yellow]🔄 Estatísticas de todas as variantes resetadas.[/bold yellow]")
        
        self._save()

    def get_best_variant(self) -> Optional[ABVariant]:
        """Retorna a variante com melhor win rate."""
        active_variants = [v for v in self.variants.values() if v.total_uses > 0]
        if not active_variants:
            return None
        
        return max(active_variants, key=lambda v: v.win_rate)

    def show_results(self) -> None:
        """Exibe o ranking atual dos testes A/B."""
        console.print("\n[bold cyan]📊 RESULTADOS DE TESTES A/B – OTIMIZAÇÃO CONTÍNUA[/bold cyan]\n")
        
        if not self.variants:
            console.print("[dim]Nenhuma variante cadastrada.[/dim]")
            return
        
        sorted_variants = sorted(
            self.variants.values(), 
            key=lambda v: v.win_rate, 
            reverse=True
        )
        
        best = self.get_best_variant()
        
        for v in sorted_variants:
            prefix = "🏆 " if best and v.variant_id == best.variant_id else "   "
            
            console.print(f"{prefix}[bold cyan]{v.name} ({v.variant_id})[/bold cyan]")
            console.print(f"      Uses: {v.total_uses} | Wins: {v.wins} | Win Rate: {v.win_rate:.1f}%")
            console.print(f"      Avg Length: {v.avg_length:.0f} chars | Temp: {v.temperature}")
            console.print(f"      {v.description}\n")

    def get_summary(self) -> Dict:
        """Retorna um resumo dos testes A/B."""
        return {
            "total_variants": len(self.variants),
            "best_variant": self.get_best_variant().variant_id if self.get_best_variant() else None,
            "variants": [
                {
                    "id": v.variant_id,
                    "name": v.name,
                    "win_rate": v.win_rate,
                    "total_uses": v.total_uses
                }
                for v in self.variants.values()
            ]
        }


# Instância global
ab_testing = ABTestingManager()