"""
behavior_versioner.py - Sistema de versionamento de comportamentos do Nexus Agent
Permite criar, listar, reverter e avaliar diferentes versões da personalidade.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from rich.console import Console

console = Console()


@dataclass
class BehaviorVersion:
    """Representa uma versão do comportamento do Nexus Agent."""
    version_id: int
    timestamp: str
    name: str                    # ex: "v1.0 - Perfil Analítico"
    description: str
    system_prompt_snippet: str   # trecho importante do prompt
    settings: Dict               # temperature, max_tokens, tom preferido, etc.
    performance_score: float = 0.0  # 0-10, avaliado pelo usuário


class BehaviorVersioner:
    """
    Sistema de versionamento de comportamentos do Nexus Agent (Git-like para personalidade).
    
    As versões são armazenadas em JSON e podem ser revertidas a qualquer momento.
    """

    def __init__(self):
        self.versions_dir = Path("build/behavior_versions")
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.versions_file = self.versions_dir / "versions.json"
        self.versions: List[BehaviorVersion] = []
        self.current_version_id: Optional[int] = None
        self._load()

    def _load(self) -> None:
        """Carrega versões do arquivo JSON."""
        if self.versions_file.exists():
            try:
                data = json.loads(self.versions_file.read_text(encoding="utf-8"))
                self.versions = [BehaviorVersion(**v) for v in data]
                if self.versions:
                    self.current_version_id = self.versions[-1].version_id
            except Exception as e:
                console.print(f"[yellow]⚠️ Erro ao carregar versões: {e}[/yellow]")
                self.versions = []

    def _save(self) -> None:
        """Salva versões no arquivo JSON."""
        try:
            data = [asdict(v) for v in self.versions]
            self.versions_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), 
                encoding="utf-8"
            )
        except Exception as e:
            console.print(f"[red]❌ Erro ao salvar versões: {e}[/red]")

    def create_version(
        self, 
        name: str, 
        description: str, 
        system_prompt_snippet: str, 
        settings: Dict
    ) -> int:
        """
        Cria uma nova versão do comportamento.
        
        Args:
            name: Nome da versão (ex: "v1.0 - Perfil Colaborativo")
            description: Descrição detalhada das mudanças
            system_prompt_snippet: Trecho do system prompt (máx 2000 chars)
            settings: Configurações (temperature, max_tokens, etc.)
            
        Returns:
            ID da nova versão
        """
        next_id = max([v.version_id for v in self.versions], default=0) + 1
        
        version = BehaviorVersion(
            version_id=next_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            name=name,
            description=description,
            system_prompt_snippet=system_prompt_snippet[:2000],
            settings=settings.copy()
        )
        self.versions.append(version)
        self.current_version_id = version.version_id
        self._save()

        console.print(f"[bold green]✅ Nova versão de comportamento criada:[/bold green] {name} (v{version.version_id})")
        return version.version_id

    def list_versions(self) -> List[BehaviorVersion]:
        """Lista todas as versões salvas."""
        return self.versions.copy()

    def get_version(self, version_id: int) -> Optional[BehaviorVersion]:
        """Retorna uma versão específica pelo ID."""
        for v in self.versions:
            if v.version_id == version_id:
                return v
        return None

    def rollback_to_version(self, version_id: int) -> bool:
        """
        Reverte para uma versão anterior.
        
        Args:
            version_id: ID da versão para reverter
            
        Returns:
            True se revertido com sucesso
        """
        target_version = self.get_version(version_id)
        if not target_version:
            console.print(f"[bold red]❌ Versão {version_id} não encontrada.[/bold red]")
            return False
        
        self.current_version_id = version_id
        self._save()
        
        console.print(f"[bold yellow]↩️ Revertido para a versão {version_id}: {target_version.name}[/bold yellow]")
        return True

    def get_current_version(self) -> Optional[BehaviorVersion]:
        """Retorna a versão atual."""
        if not self.current_version_id:
            return None
        return self.get_version(self.current_version_id)

    def get_current_settings(self) -> Dict:
        """Retorna as configurações da versão atual."""
        current = self.get_current_version()
        return current.settings.copy() if current else {}

    def rate_version(self, version_id: int, score: float) -> bool:
        """
        Avalia uma versão com uma nota.
        
        Args:
            version_id: ID da versão
            score: Nota de 0 a 10
            
        Returns:
            True se avaliado com sucesso
        """
        if score < 0 or score > 10:
            console.print(f"[red]❌ Nota deve ser entre 0 e 10.[/red]")
            return False
        
        version = self.get_version(version_id)
        if not version:
            console.print(f"[red]❌ Versão {version_id} não encontrada.[/red]")
            return False
        
        version.performance_score = score
        self._save()
        
        console.print(f"[bold green]✅ Versão {version_id} avaliada com nota {score}/10[/bold green]")
        return True

    def delete_version(self, version_id: int) -> bool:
        """
        Deleta uma versão (não pode deletar a versão atual).
        
        Args:
            version_id: ID da versão para deletar
            
        Returns:
            True se deletado com sucesso
        """
        if version_id == self.current_version_id:
            console.print(f"[red]❌ Não é possível deletar a versão atual.[/red]")
            return False
        
        original_count = len(self.versions)
        self.versions = [v for v in self.versions if v.version_id != version_id]
        
        if len(self.versions) == original_count:
            console.print(f"[red]❌ Versão {version_id} não encontrada.[/red]")
            return False
        
        self._save()
        console.print(f"[bold yellow]🗑️ Versão {version_id} deletada.[/bold yellow]")
        return True

    def compare_versions(self, version_id_1: int, version_id_2: int) -> Dict:
        """
        Compara duas versões e retorna as diferenças.
        
        Args:
            version_id_1: Primeira versão
            version_id_2: Segunda versão
            
        Returns:
            Dicionário com as diferenças
        """
        v1 = self.get_version(version_id_1)
        v2 = self.get_version(version_id_2)
        
        if not v1 or not v2:
            return {"error": "Versão não encontrada"}
        
        diff = {
            "name": f"{v1.name} → {v2.name}" if v1.name != v2.name else "mesmo nome",
            "description": f"{v1.description[:50]}... → {v2.description[:50]}..." if v1.description != v2.description else "mesma descrição",
            "settings": {}
        }
        
        all_keys = set(v1.settings.keys()) | set(v2.settings.keys())
        for key in all_keys:
            val1 = v1.settings.get(key)
            val2 = v2.settings.get(key)
            if val1 != val2:
                diff["settings"][key] = f"{val1} → {val2}"
        
        return diff

    def get_summary(self) -> Dict:
        """Retorna um resumo do sistema de versionamento."""
        return {
            "total_versions": len(self.versions),
            "current_version_id": self.current_version_id,
            "current_version_name": self.get_current_version().name if self.get_current_version() else None,
            "versions": [
                {
                    "id": v.version_id,
                    "name": v.name,
                    "score": v.performance_score,
                    "date": v.timestamp
                }
                for v in self.versions[-10:]  # últimas 10
            ]
        }


# Instância global
behavior_versioner = BehaviorVersioner()