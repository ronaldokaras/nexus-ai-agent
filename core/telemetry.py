"""
telemetry.py - Sistema de telemetria do Nexus Agent
Registra eventos, status e mantém histórico de execução.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# Configura logger
logger = logging.getLogger(__name__)


class TelemetryManager:
    """
    Gerenciador de telemetria do Nexus Agent.
    
    Registra eventos com níveis de severidade (INFO, WARNING, ERROR)
    e mantém rotação automática de logs.
    """

    def __init__(self, max_lines: int = 1000, log_format: str = "json"):
        """
        Args:
            max_lines: Número máximo de linhas no arquivo de log (rotação)
            log_format: Formato do log ("text" ou "json")
        """
        self.log_file = Path("build/telemetry.log")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_start = datetime.now()
        self.max_lines = max_lines
        self.log_format = log_format

    def _rotate_log_if_needed(self) -> None:
        """Rotaciona o arquivo de log se exceder o limite de linhas."""
        if not self.log_file.exists():
            return
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            if len(lines) > self.max_lines:
                with open(self.log_file, "w", encoding="utf-8") as f:
                    f.writelines(lines[-self.max_lines:])
                logger.info(f"Log rotacionado: mantidas últimas {self.max_lines} linhas")
        except Exception as e:
            logger.warning(f"Erro na rotação de log: {e}")

    def _format_entry(self, level: str, status: str, details: str) -> str:
        """Formata a entrada de log de acordo com o formato escolhido."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if self.log_format == "json":
            entry = json.dumps({
                "timestamp": timestamp,
                "level": level,
                "status": status,
                "details": details
            }, ensure_ascii=False)
            return entry + "\n"
        else:
            return f"[{timestamp}] [{level}] {status} | {details}\n"

    def log(self, status: str, details: str = "", level: str = "INFO") -> None:
        """
        Registra telemetria de forma segura.
        
        Args:
            status: Status ou evento (ex: "INICIADO", "ERRO", "CONEXÃO")
            details: Detalhes adicionais
            level: Nível do log (INFO, WARNING, ERROR)
        """
        try:
            entry = self._format_entry(level, status, details)
            
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry)
            
            self._rotate_log_if_needed()
            
        except Exception as e:
            logger.error(f"Erro ao registrar telemetria: {e}")

    def log_info(self, status: str, details: str = "") -> None:
        """Atalho para log com nível INFO."""
        self.log(status, details, level="INFO")

    def log_warning(self, status: str, details: str = "") -> None:
        """Atalho para log com nível WARNING."""
        self.log(status, details, level="WARNING")

    def log_error(self, status: str, details: str = "") -> None:
        """Atalho para log com nível ERROR."""
        self.log(status, details, level="ERROR")

    def get_last_status(self) -> Dict[str, str]:
        """
        Retorna o último status registrado como dicionário estruturado.
        
        Returns:
            Dict com timestamp, level, status, details
        """
        try:
            if not self.log_file.exists():
                return {"status": "Sistema iniciado", "level": "INFO", "timestamp": None}
            
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            if not lines:
                return {"status": "Sem telemetria", "level": "INFO", "timestamp": None}
            
            last_line = lines[-1].strip()
            
            if self.log_format == "json" or last_line.startswith("{"):
                try:
                    return json.loads(last_line)
                except:
                    pass
            
            import re
            match = re.match(r'\[(.*?)\]\s*\[(.*?)\]\s*(.*?)\s*\|\s*(.*)', last_line)
            if match:
                return {
                    "timestamp": match.group(1),
                    "level": match.group(2),
                    "status": match.group(3),
                    "details": match.group(4)
                }
            
            return {"status": last_line, "level": "INFO", "timestamp": None}
            
        except Exception as e:
            logger.warning(f"Erro ao ler último status: {e}")
            return {"status": "Erro ao ler telemetria", "level": "ERROR", "timestamp": None}

    def get_logs_since(self, since: datetime) -> List[Dict]:
        """
        Retorna logs a partir de uma data/hora específica.
        
        Args:
            since: Timestamp mínimo para filtro
            
        Returns:
            Lista de entradas de log como dicionários
        """
        logs = []
        
        try:
            if not self.log_file.exists():
                return logs
            
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    timestamp_str = None
                    if self.log_format == "json" or line.startswith("{"):
                        try:
                            data = json.loads(line)
                            timestamp_str = data.get("timestamp")
                        except:
                            pass
                    else:
                        import re
                        match = re.match(r'\[(.*?)\]', line)
                        if match:
                            timestamp_str = match.group(1)
                    
                    if timestamp_str:
                        try:
                            log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            if log_time >= since:
                                logs.append(self._parse_log_line(line))
                        except:
                            logs.append({"raw": line})
                    else:
                        logs.append({"raw": line})
            
            return logs
            
        except Exception as e:
            logger.warning(f"Erro ao buscar logs: {e}")
            return []

    def _parse_log_line(self, line: str) -> Dict:
        """Parseia uma linha de log para dicionário."""
        if self.log_format == "json" or line.startswith("{"):
            try:
                return json.loads(line)
            except:
                pass
        
        import re
        match = re.match(r'\[(.*?)\]\s*\[(.*?)\]\s*(.*?)\s*\|\s*(.*)', line)
        if match:
            return {
                "timestamp": match.group(1),
                "level": match.group(2),
                "status": match.group(3),
                "details": match.group(4)
            }
        
        return {"raw": line}

    def get_session_duration(self) -> Dict[str, int]:
        """
        Retorna a duração da sessão atual como dicionário estruturado.
        
        Returns:
            Dict com days, hours, minutes, seconds
        """
        duration = datetime.now() - self.session_start
        total_seconds = int(duration.total_seconds())
        
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return {
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "total_seconds": total_seconds
        }

    def get_session_info(self) -> str:
        """Retorna string amigável com a duração da sessão."""
        duration = self.get_session_duration()
        
        if duration["days"] > 0:
            return f"Sessão ativa há {duration['days']}d {duration['hours']}h {duration['minutes']}m"
        elif duration["hours"] > 0:
            return f"Sessão ativa há {duration['hours']}h {duration['minutes']}m"
        else:
            return f"Sessão ativa há {duration['minutes']}m {duration['seconds']}s"

    def clear_logs(self) -> bool:
        """Limpa todos os logs."""
        try:
            if self.log_file.exists():
                self.log_file.unlink()
            self.log("LOGS_LIMPOS", "Arquivo de log limpo manualmente", level="INFO")
            logger.info("Logs limpos com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar logs: {e}")
            return False

    def get_stats(self) -> Dict:
        """Retorna estatísticas do sistema de telemetria."""
        try:
            if not self.log_file.exists():
                return {"total_entries": 0, "file_size_kb": 0}
            
            file_size = self.log_file.stat().st_size / 1024  # KB
            
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            level_count = {"INFO": 0, "WARNING": 0, "ERROR": 0, "OTHER": 0}
            for line in lines:
                if "[INFO]" in line:
                    level_count["INFO"] += 1
                elif "[WARNING]" in line:
                    level_count["WARNING"] += 1
                elif "[ERROR]" in line:
                    level_count["ERROR"] += 1
                else:
                    level_count["OTHER"] += 1
            
            return {
                "total_entries": len(lines),
                "file_size_kb": round(file_size, 2),
                "by_level": level_count,
                "session_duration": self.get_session_duration()
            }
        except Exception as e:
            logger.warning(f"Erro ao obter estatísticas: {e}")
            return {"error": str(e)}


# Instância global
telemetry = TelemetryManager()