"""
behavior_notes.py - Sistema de notas de comportamento do Nexus Agent
Aprende com interações passadas e reforça ou evita padrões de resposta.
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime
from rich.console import Console

console = Console()


@dataclass
class BehaviorNote:
    """Representa uma nota de comportamento (positivo ou negativo)."""
    id: str                      # timestamp baseado (ex: "20241210_143022")
    type: str                    # "positive" ou "negative"
    title: str
    description: str
    context: str
    base_strength: int           # Força inicial (1-10)
    current_strength: int        # Força atual (1-10)
    frequency: int               # Quantas vezes foi detectado
    sessions_affected: int       # Em quantas sessões diferentes apareceu
    last_seen: str
    active: bool = True


class BehaviorNotesManager:
    """
    Sistema avançado de notas de comportamento com Coeficiente de Intensidade.
    
    As notas ganham força com repetição e perdem força com o tempo (decaimento).
    Notas com força < 3 são automaticamente desativadas.
    """

    def __init__(self, decay_days: int = 7, min_strength: int = 3):
        """
        Args:
            decay_days: Dias para reduzir força pela metade
            min_strength: Força mínima para manter nota ativa
        """
        self.notes_file = Path("build/behavior_notes.json")
        self.notes: List[BehaviorNote] = []
        self.decay_days = decay_days
        self.min_strength = min_strength
        self._load()
        self._apply_decay()  # Aplica decaimento ao carregar

    def _load(self) -> None:
        """Carrega notas do arquivo JSON."""
        if self.notes_file.exists():
            try:
                data = json.loads(self.notes_file.read_text(encoding="utf-8"))
                self.notes = [BehaviorNote(**note) for note in data]
            except Exception as e:
                console.print(f"[yellow]⚠️ Erro ao carregar notas: {e}[/yellow]")
                self.notes = []

    def _save(self) -> None:
        """Salva notas no arquivo JSON."""
        try:
            data = [asdict(note) for note in self.notes]
            self.notes_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), 
                encoding="utf-8"
            )
        except Exception as e:
            console.print(f"[red]❌ Erro ao salvar notas: {e}[/red]")

    def _generate_id(self) -> str:
        """Gera um ID único baseado em timestamp."""
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def _apply_decay(self) -> None:
        """Aplica decaimento de força baseado no tempo."""
        now = datetime.now()
        changed = False
        
        for note in self.notes:
            if not note.active:
                continue
            
            try:
                last_seen = datetime.strptime(note.last_seen, "%Y-%m-%d %H:%M")
                days_ago = (now - last_seen).days
                
                if days_ago >= self.decay_days:
                    # Decaimento: perde força proporcionalmente ao tempo
                    decay_factor = max(0.5, 1.0 - (days_ago / (self.decay_days * 2)))
                    new_strength = int(note.current_strength * decay_factor)
                    note.current_strength = max(1, new_strength)
                    
                    # Desativa se força abaixo do mínimo
                    if note.current_strength < self.min_strength:
                        note.active = False
                        console.print(f"[dim]📝 Nota desativada por baixa força: {note.title}[/dim]")
                    
                    changed = True
            except Exception:
                pass
        
        if changed:
            self._save()

    def add_note(
        self, 
        note_type: str, 
        title: str, 
        description: str, 
        context: str, 
        base_strength: int = 6,
        session_id: str = None
    ) -> None:
        """
        Adiciona ou reforça uma nota com coeficiente de intensidade.
        
        Args:
            note_type: "positive" ou "negative"
            title: Título curto da nota
            description: Descrição detalhada
            context: Contexto onde a nota foi gerada
            base_strength: Força inicial (1-10)
            session_id: ID da sessão atual (para contar sessões afetadas)
        """
        # Valida base_strength
        base_strength = max(1, min(10, base_strength))
        
        # Normaliza título para detectar duplicatas
        normalized_title = title.lower().strip()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        for note in self.notes:
            if note.type == note_type and normalized_title in note.title.lower():
                # Reforça nota existente
                note.frequency += 1
                
                # Atualiza sessões afetadas se for uma sessão diferente
                if session_id and session_id not in getattr(note, '_sessions', ''):
                    note.sessions_affected += 1
                    if not hasattr(note, '_sessions'):
                        note._sessions = session_id
                    else:
                        note._sessions += f",{session_id}"
                
                # Aumenta força com repetição (diminuição de retorno)
                increase = min(4, note.frequency // 2)
                note.current_strength = min(10, note.base_strength + increase)
                note.last_seen = now_str
                note.active = True  # Reativa se estava desativada
                
                self._save()
                console.print(f"🔄 Nota reforçada [bold]{note.title}[/bold] → Força: {note.current_strength}/10 (freq: {note.frequency})")
                return

        # Cria nova nota
        note = BehaviorNote(
            id=self._generate_id(),
            type=note_type,
            title=title,
            description=description,
            context=context[:1000],
            base_strength=base_strength,
            current_strength=base_strength,
            frequency=1,
            sessions_affected=1,
            last_seen=now_str,
            active=True
        )
        
        # Armazena sessão para contagem futura
        if session_id:
            note._sessions = session_id
        
        self.notes.append(note)
        self._save()
        
        emoji = "✅" if note_type == "positive" else "⚠️"
        console.print(f"{emoji} Nova nota: [bold]{title}[/bold] | Força inicial: {base_strength}/10")

    def get_active_notes(self, min_strength: int = None) -> List[BehaviorNote]:
        """
        Retorna notas ativas, priorizando as mais fortes.
        
        Args:
            min_strength: Força mínima (usa self.min_strength se None)
        """
        threshold = min_strength if min_strength is not None else self.min_strength
        return sorted(
            [n for n in self.notes if n.active and n.current_strength >= threshold],
            key=lambda x: x.current_strength,
            reverse=True
        )

    def get_prompt_injection(self, max_notes: int = 4) -> str:
        """
        Gera texto limpo para injetar no prompt do agente.
        
        Args:
            max_notes: Número máximo de notas por tipo
        """
        active_notes = self.get_active_notes()
        if not active_notes:
            return ""

        positive = [n for n in active_notes if n.type == "positive"]
        negative = [n for n in active_notes if n.type == "negative"]

        injection = "\n\n[REGRAS DE COMPORTAMENTO ATUAIS - Alta Prioridade]\n"

        if positive:
            injection += "→ REFORÇAR (faça sempre que possível):\n"
            for n in positive[:max_notes]:
                strength_bar = "█" * (n.current_strength // 2) + "░" * (5 - (n.current_strength // 2))
                injection += f"   • {n.title} [{strength_bar}] {n.current_strength}/10\n"

        if negative:
            injection += "\n→ EVITAR (nunca faça isso):\n"
            for n in negative[:max_notes]:
                strength_bar = "█" * (n.current_strength // 2) + "░" * (5 - (n.current_strength // 2))
                injection += f"   • {n.title} [{strength_bar}] {n.current_strength}/10\n"

        return injection

    def get_merge_recommendation(self, min_strength: int = 8, min_notes: int = 3) -> Optional[str]:
        """
        Recomenda quando é hora de fazer merge das notas fortes no System Prompt.
        
        Args:
            min_strength: Força mínima para considerar
            min_notes: Número mínimo de notas fortes para recomendar
        """
        now = datetime.now()
        strong_notes = []
        
        for n in self.notes:
            if not n.active or n.current_strength < min_strength:
                continue
            
            # Verifica se a nota é recente (últimos 30 dias)
            try:
                last_seen = datetime.strptime(n.last_seen, "%Y-%m-%d %H:%M")
                days_ago = (now - last_seen).days
                if days_ago <= 30:
                    strong_notes.append(n)
            except Exception:
                strong_notes.append(n)
        
        if len(strong_notes) >= min_notes:
            return (f"⚠️ Recomendação: Temos {len(strong_notes)} notas fortes (força ≥{min_strength}). "
                    f"Considere criar uma nova versão do System Prompt (V2.0) incorporando:\n"
                    + "\n".join([f"   • {n.title}" for n in strong_notes[:5]]))
        return None

    def deactivate_note(self, note_id: str) -> bool:
        """
        Desativa uma nota manualmente.
        
        Args:
            note_id: ID da nota
            
        Returns:
            True se desativada com sucesso
        """
        for note in self.notes:
            if note.id == note_id and note.active:
                note.active = False
                self._save()
                console.print(f"[bold yellow]📝 Nota desativada: {note.title}[/bold yellow]")
                return True
        return False

    def show_notes(self) -> None:
        """Exibe todas as notas formatadas."""
        if not self.notes:
            console.print("[dim]Nenhuma nota de comportamento registrada.[/dim]")
            return
        
        console.print("\n[bold cyan]📝 NOTAS DE COMPORTAMENTO DO AGENTE[/bold cyan]\n")
        
        active = self.get_active_notes()
        inactive = [n for n in self.notes if not n.active]
        
        console.print(f"[bold green]Ativas ({len(active)}):[/bold green]")
        for n in active[:10]:
            emoji = "✅" if n.type == "positive" else "⚠️"
            console.print(f"   {emoji} [bold]{n.title}[/bold] | Força: {n.current_strength}/10 | Visto: {n.last_seen}")
        
        if inactive:
            console.print(f"\n[dim]Inativas ({len(inactive)}):[/dim]")
            for n in inactive[:5]:
                console.print(f"   • {n.title} (era {n.current_strength}/10)")

    def get_summary(self) -> Dict:
        """Retorna um resumo das notas."""
        active = self.get_active_notes()
        positive = [n for n in active if n.type == "positive"]
        negative = [n for n in active if n.type == "negative"]
        
        return {
            "total_notes": len(self.notes),
            "active_notes": len(active),
            "positive_notes": len(positive),
            "negative_notes": len(negative),
            "avg_strength": sum(n.current_strength for n in active) / len(active) if active else 0,
            "merge_recommendation": self.get_merge_recommendation()
        }


# Instância global
behavior_notes = BehaviorNotesManager()