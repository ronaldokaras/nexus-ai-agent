"""
improvement_prioritizer.py - Sistema de priorização de melhorias para o Nexus Agent
Calcula prioridade baseada em Impacto / Esforço (quanto maior, mais prioritário).
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime
from rich.console import Console

console = Console()


@dataclass
class ImprovementSuggestion:
    """Representa uma sugestão de melhoria para o agente."""
    id: str                      # timestamp based ID
    title: str
    description: str
    impact: int                  # 1-10 (10 = crítico, como segurança)
    effort: int                  # 1-5  (1 = fácil, 5 = muito complexo)
    category: str                # segurança, usabilidade, performance, etc.
    status: str = "pending"      # pending, in_progress, done
    created_at: str = None
    started_at: str = None
    completed_at: str = None


class ImprovementPrioritizer:
    """
    Sistema inteligente de priorização de melhorias para o Nexus Agent.
    
    A prioridade é calculada como: score = impact / effort
    Quanto maior o score, mais prioritária a melhoria.
    """

    def __init__(self, dashboard_limit: int = 10):
        """
        Args:
            dashboard_limit: Número máximo de itens no dashboard
        """
        self.file_path = Path("build/improvements.json")
        self.dashboard_limit = dashboard_limit
        self.suggestions: List[ImprovementSuggestion] = []
        self._load()

    def _generate_id(self) -> str:
        """Gera um ID único baseado em timestamp."""
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def _load(self) -> None:
        """Carrega sugestões do arquivo JSON."""
        if self.file_path.exists():
            try:
                data = json.loads(self.file_path.read_text(encoding="utf-8"))
                self.suggestions = [ImprovementSuggestion(**item) for item in data]
            except Exception as e:
                console.print(f"[yellow]⚠️ Erro ao carregar melhorias: {e}[/yellow]")
                self.suggestions = []

    def _save(self) -> None:
        """Salva sugestões no arquivo JSON."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            data = [asdict(s) for s in self.suggestions]
            self.file_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), 
                encoding="utf-8"
            )
        except Exception as e:
            console.print(f"[red]❌ Erro ao salvar melhorias: {e}[/red]")

    def add_suggestion(
        self, 
        title: str, 
        description: str, 
        impact: int, 
        effort: int, 
        category: str
    ) -> Optional[str]:
        """
        Adiciona uma nova sugestão de melhoria.
        
        Args:
            title: Título curto da melhoria
            description: Descrição detalhada
            impact: Impacto (1-10, 10 = mais importante)
            effort: Esforço (1-5, 1 = mais fácil)
            category: Categoria (segurança, usabilidade, performance, etc.)
            
        Returns:
            ID da sugestão criada, ou None se erro
        """
        if not title or len(title) < 3:
            console.print(f"[red]❌ Título muito curto (mínimo 3 caracteres).[/red]")
            return None
        
        if impact < 1 or impact > 10:
            console.print(f"[red]❌ Impacto deve ser entre 1 e 10.[/red]")
            return None
        
        if effort < 1 or effort > 5:
            console.print(f"[red]❌ Esforço deve ser entre 1 e 5.[/red]")
            return None
        
        suggestion_id = self._generate_id()
        suggestion = ImprovementSuggestion(
            id=suggestion_id,
            title=title,
            description=description,
            impact=impact,
            effort=effort,
            category=category.lower(),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        self.suggestions.append(suggestion)
        self._save()
        
        score = impact / effort
        console.print(f"[bold green]✅ Nova melhoria adicionada →[/bold green] {title}")
        console.print(f"   [dim]Impacto: {impact}/10 | Esforço: {effort}/5 | Score: {score:.2f}[/dim]")
        
        return suggestion_id

    def _priority_score(self, suggestion: ImprovementSuggestion) -> float:
        """Calcula o score de prioridade da sugestão."""
        return suggestion.impact / suggestion.effort if suggestion.effort > 0 else 0

    def get_prioritized_list(self, include_in_progress: bool = False) -> List[ImprovementSuggestion]:
        """
        Retorna a lista ordenada por prioridade (Impacto / Esforço).
        
        Args:
            include_in_progress: Se True, inclui sugestões em andamento
        """
        status_filter = ["pending"]
        if include_in_progress:
            status_filter.append("in_progress")
        
        return sorted(
            [s for s in self.suggestions if s.status in status_filter],
            key=self._priority_score,
            reverse=True
        )

    def get_all_by_status(self) -> Dict[str, List[ImprovementSuggestion]]:
        """Retorna sugestões agrupadas por status."""
        result = {"pending": [], "in_progress": [], "done": []}
        for s in self.suggestions:
            if s.status in result:
                result[s.status].append(s)
        return result

    def start_work(self, suggestion_id: str) -> bool:
        """
        Marca uma sugestão como em andamento.
        
        Args:
            suggestion_id: ID da sugestão
            
        Returns:
            True se encontrada e atualizada
        """
        for sug in self.suggestions:
            if sug.id == suggestion_id and sug.status == "pending":
                sug.status = "in_progress"
                sug.started_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                self._save()
                console.print(f"[bold yellow]🚀 Trabalho iniciado: {sug.title}[/bold yellow]")
                return True
            elif sug.id == suggestion_id:
                console.print(f"[yellow]⚠️ Sugestão já está em status '{sug.status}'[/yellow]")
                return False
        
        console.print(f"[red]❌ Sugestão {suggestion_id} não encontrada.[/red]")
        return False

    def mark_as_done(self, suggestion_id: str) -> bool:
        """
        Marca uma melhoria como concluída.
        
        Args:
            suggestion_id: ID da sugestão
            
        Returns:
            True se encontrada e atualizada
        """
        for sug in self.suggestions:
            if sug.id == suggestion_id and sug.status in ["pending", "in_progress"]:
                sug.status = "done"
                sug.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                self._save()
                console.print(f"[bold green]✅ Melhoria concluída: {sug.title}[/bold green]")
                return True
            elif sug.id == suggestion_id:
                console.print(f"[yellow]⚠️ Sugestão já está concluída.[/yellow]")
                return False
        
        console.print(f"[red]❌ Sugestão {suggestion_id} não encontrada.[/red]")
        return False

    def delete_suggestion(self, suggestion_id: str) -> bool:
        """
        Deleta uma sugestão (útil para remover duplicatas ou inválidas).
        
        Args:
            suggestion_id: ID da sugestão
            
        Returns:
            True se deletada com sucesso
        """
        original_count = len(self.suggestions)
        self.suggestions = [s for s in self.suggestions if s.id != suggestion_id]
        
        if len(self.suggestions) < original_count:
            self._save()
            console.print(f"[bold yellow]🗑️ Sugestão {suggestion_id} deletada.[/bold yellow]")
            return True
        
        console.print(f"[red]❌ Sugestão {suggestion_id} não encontrada.[/red]")
        return False

    def show_dashboard(self) -> None:
        """Mostra um dashboard bonito com as prioridades."""
        prioritized = self.get_prioritized_list(include_in_progress=True)
        by_status = self.get_all_by_status()
        
        console.print("\n[bold magenta]🚀 SISTEMA DE PRIORIZAÇÃO DE MELHORIAS[/bold magenta]")
        console.print(f"[dim]📊 Total: {len(self.suggestions)} | Pendentes: {len(by_status['pending'])} | Em andamento: {len(by_status['in_progress'])} | Concluídas: {len(by_status['done'])}[/dim]\n")

        active = [s for s in prioritized if s.status in ["pending", "in_progress"]]
        
        if not active:
            console.print("[green]✅ Todas as melhorias foram implementadas![/green]")
            return
        
        for i, sug in enumerate(active[:self.dashboard_limit], 1):
            score = self._priority_score(sug)
            status_icon = "⏳" if sug.status == "pending" else "🚀"
            status_color = "yellow" if sug.status == "pending" else "cyan"
            
            console.print(f"{i:2d}. {status_icon} [bold {status_color}]{sug.title}[/bold {status_color}]")
            console.print(f"    📌 [{sug.category.upper()}] | Impacto: {sug.impact}/10 | Esforço: {sug.effort}/5 | Score: {score:.2f}")
            console.print(f"    📝 {sug.description[:100]}...")
            if sug.started_at:
                console.print(f"    🕐 Iniciado em: {sug.started_at}")
            print()

        if len(active) > self.dashboard_limit:
            console.print(f"[dim]... e mais {len(active) - self.dashboard_limit} itens não exibidos[/dim]")

    def get_summary(self) -> Dict:
        """Retorna um resumo estatístico das melhorias."""
        by_status = self.get_all_by_status()
        
        category_stats = {}
        for sug in self.suggestions:
            if sug.category not in category_stats:
                category_stats[sug.category] = {"count": 0, "total_impact": 0, "total_effort": 0}
            category_stats[sug.category]["count"] += 1
            category_stats[sug.category]["total_impact"] += sug.impact
            category_stats[sug.category]["total_effort"] += sug.effort
        
        for cat in category_stats:
            category_stats[cat]["avg_impact"] = category_stats[cat]["total_impact"] / category_stats[cat]["count"]
            category_stats[cat]["avg_effort"] = category_stats[cat]["total_effort"] / category_stats[cat]["count"]
        
        next_priority = self.get_prioritized_list()
        next_suggestion = next_priority[0] if next_priority else None
        
        return {
            "total": len(self.suggestions),
            "pending": len(by_status["pending"]),
            "in_progress": len(by_status["in_progress"]),
            "done": len(by_status["done"]),
            "by_category": category_stats,
            "next_priority": {
                "title": next_suggestion.title,
                "score": self._priority_score(next_suggestion)
            } if next_suggestion else None
        }


# Instância global
prioritizer = ImprovementPrioritizer()