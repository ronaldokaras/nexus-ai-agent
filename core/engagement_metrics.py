"""
engagement_metrics.py - Sistema de métricas de qualidade de interação do Nexus Agent
Monitora sessões, interações, sentimento do usuário e utilidade das respostas.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from rich.console import Console

console = Console()


@dataclass
class SessionMetrics:
    """Métricas de uma sessão de interação."""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    messages_count: int = 0
    total_tokens: int = 0
    avg_response_time: float = 0.0
    sentiment_quality: float = 0.0      # 0.0 a 5.0 – indicador composto de qualidade percebida
    satisfaction_score: float = 0.0     # 0.0 a 1.0 – índice de utilidade das respostas
    _response_time_sum: float = 0.0     # soma para cálculo correto (não serializado)


class EngagementMetrics:
    """
    Sistema de monitoramento de qualidade de interação do Nexus Agent.
    Persiste dados em JSON e fornece dashboard analítico.
    """

    def __init__(self):
        self.metrics_dir = Path("build/metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_file = self.metrics_dir / "sessions.json"
        self.daily_stats_file = self.metrics_dir / "daily_stats.json"
        
        self.current_session: Optional[SessionMetrics] = None
        self.sessions: List[SessionMetrics] = []
        self.daily_stats: Dict = {}
        self._load()

    def _load(self):
        """Carrega dados históricos dos arquivos JSON."""
        if self.sessions_file.exists():
            try:
                data = json.loads(self.sessions_file.read_text(encoding="utf-8"))
                self.sessions = [SessionMetrics(**s) for s in data]
            except Exception as e:
                console.print(f"[yellow]⚠️ Erro ao carregar sessões: {e}[/yellow]")
                self.sessions = []

        if self.daily_stats_file.exists():
            try:
                self.daily_stats = json.loads(self.daily_stats_file.read_text(encoding="utf-8"))
            except Exception as e:
                console.print(f"[yellow]⚠️ Erro ao carregar estatísticas diárias: {e}[/yellow]")
                self.daily_stats = {}

    def _save(self):
        """Persiste os dados em arquivos JSON."""
        try:
            sessions_data = []
            for s in self.sessions:
                s_dict = asdict(s)
                s_dict.pop('_response_time_sum', None)
                sessions_data.append(s_dict)
            
            self.sessions_file.write_text(
                json.dumps(sessions_data, ensure_ascii=False, indent=2), 
                encoding="utf-8"
            )
            
            self.daily_stats_file.write_text(
                json.dumps(self.daily_stats, ensure_ascii=False, indent=2), 
                encoding="utf-8"
            )
        except Exception as e:
            console.print(f"[red]❌ Erro ao salvar métricas: {e}[/red]")

    def start_session(self) -> str:
        """Inicia uma nova sessão de interação."""
        if self.current_session:
            self.end_session()
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = SessionMetrics(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            _response_time_sum=0.0
        )
        console.print(f"[dim]📊 Sessão iniciada: {session_id}[/dim]")
        return session_id

    def _calculate_satisfaction(self, user_input: str, reply: str) -> float:
        """
        Calcula um índice de utilidade da resposta (0.0 a 1.0).
        Baseado em clareza, completude e indicadores de resultado.
        """
        score = 0.0
        
        # Indicadores de conclusão/resultado (peso 0.4)
        completion_markers = ["✅", "pronto", "feito", "criado", "salvo", "arquivo", "📁", "📊", "🔧", "⚙️"]
        marker_count = sum(1 for m in completion_markers if m in reply)
        score += min(0.4, marker_count * 0.1)
        
        # Tamanho adequado da resposta (peso 0.3)
        reply_len = len(reply)
        if 50 < reply_len < 800:
            score += 0.3
        elif reply_len >= 800:
            score += 0.15
        elif reply_len < 20:
            score -= 0.1
        
        # Palavras-chave de entrega de valor (peso 0.3)
        value_keywords = ["análise", "sugestão", "recomendação", "resultado", "relatório", "otimização", "passo", "explicação", "resumo", "conclusão"]
        if any(word in reply.lower() for word in value_keywords):
            score += 0.3
        
        return max(0.0, min(1.0, score))

    def _calculate_sentiment_quality(self, user_input: str) -> float:
        """
        Estima a qualidade do sentimento do usuário na interação (0.0 a 5.0).
        Utiliza heurística simples baseada em palavras positivas/negativas.
        """
        positive_words = ["obrigado", "valeu", "bom", "ótimo", "excelente", "perfeito", "legal", "show"]
        negative_words = ["ruim", "péssimo", "horrível", "não gostei", "difícil", "complicado", "erro"]
        
        pos_count = sum(1 for w in positive_words if w in user_input.lower())
        neg_count = sum(1 for w in negative_words if w in user_input.lower())
        
        # Base 2.5 (neutro) + ajuste por sentimento
        quality = 2.5 + (pos_count * 0.8) - (neg_count * 1.0)
        return max(0.0, min(5.0, quality))

    def record_interaction(self, user_input: str, reply: str, response_time: float) -> None:
        """Registra cada interação na sessão atual."""
        if not self.current_session:
            self.start_session()

        self.current_session.messages_count += 1
        self.current_session.total_tokens += len(user_input) + len(reply)

        # Qualidade de sentimento baseada na entrada do usuário
        sentiment = self._calculate_sentiment_quality(user_input)
        # Média móvel simples
        if self.current_session.messages_count == 1:
            self.current_session.sentiment_quality = sentiment
        else:
            self.current_session.sentiment_quality = (
                (self.current_session.sentiment_quality * (self.current_session.messages_count - 1)) + sentiment
            ) / self.current_session.messages_count

        # Satisfação baseada na resposta
        self.current_session.satisfaction_score = self._calculate_satisfaction(user_input, reply)

        # Tempo de resposta
        self.current_session._response_time_sum += response_time
        self.current_session.avg_response_time = (
            self.current_session._response_time_sum / self.current_session.messages_count
        )

    def end_session(self) -> None:
        """Finaliza a sessão atual e persiste as métricas."""
        if not self.current_session:
            return

        self.current_session.end_time = datetime.now().isoformat()
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.daily_stats:
            self.daily_stats[today] = {
                "sessions": 0, 
                "messages": 0, 
                "sentiment_quality_sum": 0.0,
                "satisfaction_sum": 0.0
            }

        self.daily_stats[today]["sessions"] += 1
        self.daily_stats[today]["messages"] += self.current_session.messages_count
        self.daily_stats[today]["sentiment_quality_sum"] += self.current_session.sentiment_quality
        self.daily_stats[today]["satisfaction_sum"] += self.current_session.satisfaction_score

        self.sessions.append(self.current_session)
        
        # Mantém apenas as últimas 100 sessões
        if len(self.sessions) > 100:
            self.sessions = self.sessions[-100:]
        
        self._save()

        console.print(f"[dim]📊 Sessão finalizada. Mensagens: {self.current_session.messages_count} | Sentimento: {self.current_session.sentiment_quality:.1f}/5 | Satisfação: {self.current_session.satisfaction_score:.2f}[/dim]")
        self.current_session = None

    def get_today_stats(self) -> dict:
        """Retorna estatísticas consolidadas do dia atual."""
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.daily_stats:
            return {"sessions": 0, "messages": 0, "avg_sentiment": 0, "avg_satisfaction": 0}
        
        stats = self.daily_stats[today]
        avg_sentiment = stats["sentiment_quality_sum"] / stats["sessions"] if stats["sessions"] > 0 else 0
        avg_satisfaction = stats["satisfaction_sum"] / stats["sessions"] if stats["sessions"] > 0 else 0
        
        return {
            "sessions": stats["sessions"],
            "messages": stats["messages"],
            "avg_sentiment": round(avg_sentiment, 1),
            "avg_satisfaction": round(avg_satisfaction, 2)
        }

    def show_dashboard(self) -> None:
        """Exibe o dashboard analítico de qualidade de interação."""
        console.print("\n[bold cyan]📈 PAINEL DE QUALIDADE DE INTERAÇÃO – NEXUS AGENT[/bold cyan]\n")

        total_sessions = len(self.sessions)
        total_messages = sum(s.messages_count for s in self.sessions)
        
        if total_sessions == 0:
            console.print("[dim]Nenhuma sessão registrada ainda. Inicie uma conversa para gerar métricas.[/dim]")
            return

        console.print(f"📊 Total de sessões: [bold cyan]{total_sessions}[/bold cyan]")
        console.print(f"💬 Total de mensagens: [bold cyan]{total_messages}[/bold cyan]")
        
        if total_sessions > 0:
            avg_sentiment = sum(s.sentiment_quality for s in self.sessions) / total_sessions
            avg_satisfaction = sum(s.satisfaction_score for s in self.sessions) / total_sessions
            avg_response = sum(s.avg_response_time for s in self.sessions) / total_sessions
            
            console.print(f"📈 Sentimento médio: [bold]{avg_sentiment:.1f}/5[/bold]")
            console.print(f"✅ Índice de utilidade médio: [bold green]{avg_satisfaction:.2f}/1.00[/bold green]")
            console.print(f"⏱️ Tempo médio de resposta: [bold yellow]{avg_response:.2f}s[/bold yellow]")
            
            total_tokens = sum(s.total_tokens for s in self.sessions)
            console.print(f"🔤 Total de tokens processados: [bold cyan]{total_tokens:,}[/bold cyan]")

        today_stats = self.get_today_stats()
        console.print(f"\n[bold]📅 Estatísticas de hoje:[/bold]")
        console.print(f"   Sessões: {today_stats['sessions']} | Mensagens: {today_stats['messages']}")
        console.print(f"   Sentimento médio: {today_stats['avg_sentiment']}/5 | Utilidade: {today_stats['avg_satisfaction']:.2f}")

        console.print("\n[bold]🕐 Últimas sessões:[/bold]")
        for session in self.sessions[-5:]:
            duration_str = "Em andamento" if not session.end_time else "Finalizada"
            console.print(f"   • {session.start_time[:16]} | {session.messages_count} msgs | Sentimento: {session.sentiment_quality:.1f}/5 | Utilidade: {session.satisfaction_score:.2f}")

        console.print("\n[dim]💡 Use `.metrics` para exibir este painel novamente.[/dim]")

    def reset_metrics(self, confirm: bool = False) -> str:
        """
        Reseta todas as métricas acumuladas.
        
        Args:
            confirm: Precisa ser True para confirmar a operação
            
        Returns:
            Mensagem de confirmação ou aviso
        """
        if not confirm:
            return "⚠️ Para resetar todas as métricas, use `.metrics_reset confirmar`"
        
        self.sessions = []
        self.daily_stats = {}
        self.current_session = None
        self._save()
        return "✅ Todas as métricas foram resetadas com sucesso."

    def get_summary(self) -> dict:
        """Retorna um resumo das métricas para uso externo."""
        if not self.sessions:
            return {"total_sessions": 0, "total_messages": 0}
        
        return {
            "total_sessions": len(self.sessions),
            "total_messages": sum(s.messages_count for s in self.sessions),
            "avg_sentiment": sum(s.sentiment_quality for s in self.sessions) / len(self.sessions),
            "avg_satisfaction": sum(s.satisfaction_score for s in self.sessions) / len(self.sessions),
            "today_stats": self.get_today_stats()
        }


# Instância global
metrics = EngagementMetrics()