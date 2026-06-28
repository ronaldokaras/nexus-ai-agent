"""
core/nexus.py - Nexus Agent Core
Sistema central de automação e suporte agentivo.
Gerencia memória, análise de sentimento, segurança, métricas e interações via OpenRouter.
"""

import os
import re
import requests
import time
from typing import List, Tuple, Dict
from pathlib import Path
import logging

from config.settings import TEMPERATURE, MAX_HISTORY, MODEL_ID
from prompts.system_prompt import SYSTEM_PROMPT
from core.memory import NexusMemory
from core.utils import limpar_dados
from core.writer import file_writer
from core.security import SecurityManager
from core.sentiment import SentimentAnalyzer
from core.command_extractor import CommandExtractor, CommandResult
from core.improvement_prioritizer import prioritizer  # mantido, mas não usado diretamente
from core.behavior_versioner import behavior_versioner
from core.ab_testing import ab_testing
from core.engagement_metrics import metrics
from core.behavior_notes import behavior_notes
from core.silent_mode import silent_mode
from core.sentiment_stability import sentiment_stability
from core.telemetry import telemetry
from core.proactive_mode import proactive_mode
from core.memory_manager import memory_manager
from core.voice import voice

logger = logging.getLogger(__name__)

class Nexus:
    """
    Agente principal do sistema Nexus. Coordena processamento de linguagem natural,
    análise de sentimento, escrita autônoma de arquivos, segurança, memória de longo prazo
    e métricas de desempenho.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY não encontrada no arquivo .env")

        self.memory = NexusMemory()
        self.file_writer = file_writer
        self.model_id = os.getenv("MODEL_ID", "google/gemini-2.0-flash-001")
        
        # ==================== MÓDULOS AVANÇADOS ====================
        self.command_extractor = CommandExtractor()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.behavior_versioner = behavior_versioner
        self.ab_testing = ab_testing
        self.metrics = metrics
        self.behavior_notes = behavior_notes
        self.silent_mode = silent_mode
        self.sentiment_stability = sentiment_stability
        self.telemetry = telemetry
        self.proactive_mode = proactive_mode
        self.memory_manager = memory_manager

        self.negative_streak = 0
        self.last_sentiment = "neutro"
        self.problem_context: List[Dict] = []

        self.telemetry.log("INICIADO", "Nexus Agent v1.0 - Silent Mode + Variant + File Writer")
        self.metrics.start_session()
        self.voice = voice
        self.voice_enabled = os.getenv("VOICE_ENABLED", "false").lower() == "true"

        # Cria versão inicial de comportamento
        self._create_initial_behavior_version()

        # Regex para comandos de escrita autônoma
        self.PADRAO_ESCRITA = re.compile(
            r"file_writer\.criar_arquivo_autonomo\s*\(\s*"
            r"['\"](?P<caminho>.*?)['\"]\s*,\s*"
            r"(?P<delimitador>'''|\"\"\"|'|\")(?P<conteudo>.*?)(?P=delimitador)\s*"
            r"\)",
            re.DOTALL | re.IGNORECASE
        )
        
        self._carregar_contexto_inicial()

        # Diretório base = raiz do projeto (detectado automaticamente)
        self.diretorio_base = Path(__file__).resolve().parent.parent

    # ====================== MÉTODOS INTERNOS ======================
    def _create_initial_behavior_version(self):
        """Cria a versão inicial de comportamento."""
        self.behavior_versioner.create_version(
            name="v1.0 - Silent Mode + Variant",
            description="Timeout 180s + sanitização de comandos + consistência",
            system_prompt_snippet=SYSTEM_PROMPT[:400],
            settings={"consistency_focus": True}
        )

    def _carregar_contexto_inicial(self):
        memoria_contexto = self.memory.get_context() 
        status_hardware = self.telemetry.get_last_status()
        
        prompt_completo = (
            f"{SYSTEM_PROMPT}\n\n"
            f"[MEMÓRIA DE LONGO PRAZO (SQLITE)]: {memoria_contexto}\n\n"
            f"[STATUS ATUAL DO HARDWARE]: {status_hardware}"
        )
        self.messages = [{"role": "system", "content": prompt_completo}]

    def _call_api(self, messages: List[Dict], temperature: float = TEMPERATURE, max_tokens: int = 1500) -> str:
        """Método centralizado para chamar a API do OpenRouter."""
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key.strip()}", "Content-Type": "application/json"},
                json={
                    "model": self.model_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=180
            )
            res_json = response.json()
            return res_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip() or "Sem resposta."
        except Exception as e:
            logger.exception("Erro na chamada da API")
            return ""

    # ====================== CHAT PRINCIPAL ======================
    def chat(self, user_input: str) -> str:
        """
        Processa uma entrada do usuário e retorna a resposta do Nexus.
        Inclui análise de sentimento, ajuste de variantes A/B, controle de estabilidade,
        comandos internos e escrita autônoma de arquivos.
        """
        start_time = time.time()
        user_input = limpar_dados(user_input)
        
        if not user_input:
            return "Por favor, digite algo para que eu possa ajudar."

        # Adiciona mensagem do usuário ao histórico
        self.messages.append({"role": "user", "content": user_input})
        self.problem_context.append({"role": "user", "content": user_input})
        if len(self.problem_context) > 10:
            self.problem_context.pop(0)

        try:
            command = self.command_extractor.extract(user_input)
            sentiment = self.sentiment_analyzer.analyze(user_input)

            # ==================== PROCESSAMENTO DE COMANDOS DIRETOS ====================
            if command.type and command.needs_execution:
                if command.type == "modo_silencioso":
                    reply = self.silent_mode.toggle()
                    self.messages.append({"role": "assistant", "content": reply})
                    return reply
                
                if command.type == "modo_proativo":
                    if hasattr(self, 'proactive_mode'):
                        reply = self.proactive_mode.toggle()
                        self.messages.append({"role": "assistant", "content": reply})
                        return reply
                    else:
                        return "Módulo proativo não está disponível no momento."
                
                if command.type == "mostrar_notas":
                    reply = self._get_notes_as_string()
                    self.messages.append({"role": "assistant", "content": reply})
                    return reply
                
                if command.type == "mostrar_metricas":
                    reply = self._get_metrics_as_string()
                    self.messages.append({"role": "assistant", "content": reply})
                    return reply
                
                if command.type == "mostrar_status":
                    reply = self._get_status_as_string()
                    self.messages.append({"role": "assistant", "content": reply})
                    return reply
                
                if command.type == "limpar_memoria" or "limpar memória" in user_input.lower():
                    reply = self.memory.limpar_tudo()
                    self.messages.append({"role": "assistant", "content": reply})
                    return reply

            # ==================== ATUALIZAÇÃO DE ESTABILIDADE DE SENTIMENTO ====================
            self.sentiment_stability.update(sentiment.emotion, user_input, 0)
            stability_prompt = self.sentiment_stability.get_stability_prompt()
            if stability_prompt:
                self.messages.append({"role": "system", "content": stability_prompt})

            # Auto‑cura baseada na estabilidade
            self._check_auto_cure(sentiment, user_input)

            # Rollback inteligente se usuário aceitar
            if self._is_rollback_acceptance(user_input):
                self._perform_intelligent_rollback()

            # Ajuste de formalidade baseado no tom (sem conteúdo adulto)
            if sentiment.tone_adjust == "formal":
                tone_instruction = "Mantenha um tom formal e profissional."
            elif sentiment.tone_adjust == "informal":
                tone_instruction = "Use um tom mais casual, porém respeitoso."
            else:
                tone_instruction = None
            if tone_instruction:
                self.messages.append({"role": "system", "content": tone_instruction})

            # Determina se é um pedido técnico
            is_technical_request = any(word in user_input.lower() for word in 
                ["melhoria", "sugestão", "otimização", "melhorar", "análise", "analisa", "organiza", "organizar"])

            # Geração da resposta com possível modo silencioso ou variante A/B
            if self.silent_mode.is_enabled() and is_technical_request:
                raw_reply = self._raw_chat(user_input)
                resposta_final = self.silent_mode.process_technical_content(raw_reply, topic="melhorias")
            else:
                current_variant = self.ab_testing.get_variant()
                variant_id = current_variant.variant_id

                messages_with_ab = self.messages.copy()
                if current_variant.prompt_modifier:
                    ab_instruction = {"role": "system", "content": f"[TESTE A/B - Variante {variant_id}]: {current_variant.prompt_modifier}"}
                    messages_with_ab.insert(1, ab_instruction)

                notes_injection = self.behavior_notes.get_prompt_injection()
                if notes_injection:
                    messages_with_ab.append({"role": "system", "content": notes_injection})

                raw_reply = self._call_api(messages_with_ab, current_variant.temperature, current_variant.max_tokens)
                resposta_final = raw_reply or "Desculpe, ocorreu uma falha de comunicação. Tente novamente."

            # Processa comandos de escrita embutidos na resposta
            resposta_final = self._processar_comandos(command, resposta_final)

            # Memoriza fatos relevantes
            if len(user_input) > 15 and sentiment.emotion not in ["estressado", "negativo"]:
                limite = 1000 if len(user_input) > 200 else 150
                fato = f"Informação: {user_input[:limite]}"
                self.memory.add_fact(fato)

            # Registro de métricas
            response_time = time.time() - start_time
            self.metrics.record_interaction(user_input, resposta_final, response_time)
            self.ab_testing.record_interaction("C", resposta_final)

            # Nota de cuidado quando sentimento requer atenção
            if sentiment.needs_care:
                resposta_final += "\n\nEstou ajustando meu estilo para melhor atendê-lo(a)."

            self.messages.append({"role": "assistant", "content": resposta_final})

            # Limita o histórico de conversa
            if len(self.messages) > (MAX_HISTORY * 2):
                self.messages = [self.messages[0]] + self.messages[-(MAX_HISTORY * 2 - 1):]
                self.memory_manager.check_and_alert()

            # Síntese de voz, se habilitada
            if self.voice_enabled and resposta_final:
                self.voice.speak(resposta_final)

            return resposta_final

        except Exception as e:
            logger.exception("Erro crítico no método chat")
            if self.messages and self.messages[-1]["role"] == "user":
                self.messages.pop()
            return "Ocorreu um erro inesperado. Por favor, tente novamente."

    def _processar_comandos(self, command: CommandResult, reply: str) -> str:
        return self._executar_comando_escrita(reply)

    def _executar_comando_escrita(self, texto: str) -> str:
        """
        Processa comandos de escrita autônoma de arquivos.
        Agora suporta o retorno em dicionário do file_writer.
        """
        try:
            matches = list(self.PADRAO_ESCRITA.finditer(texto))
            if not matches:
                return texto

            logger.info(f"Encontrados {len(matches)} comando(s) de escrita.")

            arquivos_criados: List[str] = []
            erros: List[Tuple[str, str]] = []

            for i, match in enumerate(matches):
                caminho_raw, conteudo = match.group("caminho"), match.group("conteudo")
                caminho_raw = caminho_raw.strip()
                conteudo_len = len(conteudo.strip())

                try:
                    caminho = self._sanitizar_caminho(caminho_raw)
                    resultado = self.file_writer.criar_arquivo_autonomo(str(caminho), conteudo.strip())
                    
                    if resultado.get("status") == "success":
                        arquivos_criados.append(resultado.get("path", str(caminho)))
                        logger.info(f"✅ Arquivo criado: {resultado.get('path')} ({conteudo_len} chars)")
                    else:
                        erros.append((caminho_raw, resultado.get("message", "Erro desconhecido")))
                        logger.warning(f"⚠️ Falha ao criar arquivo: {resultado.get('message')}")

                except ValueError as e:
                    erros.append((caminho_raw, str(e)))
                    logger.warning(f"⚠️ Caminho rejeitado: {caminho_raw} → {e}")
                except Exception as e:
                    erros.append((caminho_raw, str(e)))
                    logger.error(f"❌ Erro ao criar arquivo '{caminho_raw}': {type(e).__name__}: {e}", exc_info=True)

            # Limpa o texto removendo os comandos de escrita
            texto_limpo = self.PADRAO_ESCRITA.sub("", texto).strip()
            texto_limpo = re.sub(r"```[a-zA-Z0-9]*\s*```", "", texto_limpo).strip()

            if erros:
                return f"❌ Não foi possível criar {len(erros)} arquivo(s). Verifique os logs para mais detalhes."

            if arquivos_criados:
                if not texto_limpo or len(texto_limpo) < 3:
                    return "Arquivos gerados com sucesso."
                return texto_limpo

            return texto_limpo if len(texto_limpo) >= 3 else texto

        except Exception as e:
            logger.exception("Erro inesperado em _executar_comando_escrita")
            return texto

    def _sanitizar_caminho(self, caminho_raw: str) -> Path:
        """
        Sanitiza o caminho do arquivo, garantindo que fique dentro da raiz do projeto.
        """
        if not caminho_raw:
            raise ValueError("Caminho vazio")

        base_permitida = Path(__file__).resolve().parent.parent
        caminho_solicitado = Path(caminho_raw)

        if not caminho_solicitado.is_absolute():
            caminho_final = (base_permitida / caminho_solicitado).resolve()
        else:
            caminho_final = caminho_solicitado.resolve()

        if not str(caminho_final).lower().startswith(str(base_permitida).lower()):
            logger.warning(f"Tentativa de saída detectada! Redirecionando: {caminho_final.name}")
            caminho_final = base_permitida / caminho_final.name

        if not caminho_final.suffix:
            caminho_final = caminho_final.with_suffix('.txt')

        caminho_final.parent.mkdir(parents=True, exist_ok=True)
        return caminho_final

    def _raw_chat(self, user_input: str) -> str:
        """Resposta simplificada para modo silencioso."""
        messages = self.messages.copy()
        messages.append({"role": "user", "content": user_input})
        return self._call_api(messages, TEMPERATURE, 1500)

    def _check_auto_cure(self, sentiment, user_input: str):
        """Auto-cura baseada em queda de estabilidade de sentimento."""
        if sentiment.emotion in ["negativo", "estressado"]:
            self.negative_streak += 1
        else:
            self.negative_streak = max(0, self.negative_streak - 1)

        if self.negative_streak >= 4 and getattr(self.sentiment_stability.state, 'stability', 0) < 0.65:
            versions = self.behavior_versioner.list_versions()
            if len(versions) > 1:
                previous = versions[-2]
                cure_msg = (f"\n\nEstou percebendo que o estilo atual pode não estar atendendo bem. "
                           f"Deseja que eu volte para a versão anterior estável (v{previous.version_id} - {previous.name})?")
                self.messages.append({"role": "system", "content": cure_msg})
                self.negative_streak = 2

    def _is_rollback_acceptance(self, user_input: str) -> bool:
        lower = user_input.lower()
        return any(kw in lower for kw in ["sim", "volta", "reverte", "aceito", "quero", "anterior", "estável"])

    def _perform_intelligent_rollback(self):
        versions = self.behavior_versioner.list_versions()
        if len(versions) <= 1:
            return
        previous_version = versions[-2]
        context = self._get_problem_context()
        success = self.behavior_versioner.rollback_to_version(previous_version.version_id)
        if success:
            self.behavior_notes.add_note("negative", f"Evitar problema da versão {previous_version.version_id + 1}", 
                                       f"Insatisfação detectada. Contexto: {context}", context, 9)
            self.behavior_notes.add_note("positive", f"Reforçar versão {previous_version.version_id}", 
                                       "Comportamento que gerava maior satisfação.", context, 8)
            self.negative_streak = 0
            self.problem_context.clear()

    def _get_problem_context(self) -> str:
        if not self.problem_context:
            return "Sem contexto disponível"
        return " | ".join([msg["content"][:80] for msg in self.problem_context[-6:]])

    # ==================== MÉTODOS AUXILIARES PARA COMANDOS ====================
    def _get_notes_as_string(self) -> str:
        """Retorna as notas de comportamento como string."""
        try:
            if hasattr(self.behavior_notes, 'get_notes_as_string'):
                return self.behavior_notes.get_notes_as_string()
            elif hasattr(self.behavior_notes, 'show_notes'):
                import io, sys
                captured_output = io.StringIO()
                sys.stdout = captured_output
                self.behavior_notes.show_notes()
                sys.stdout = sys.__stdout__
                return captured_output.getvalue() or "Nenhuma nota registrada."
            else:
                return "Módulo de notas não disponível."
        except Exception as e:
            logger.error(f"Erro ao obter notas: {e}")
            return "Não foi possível recuperar as notas."

    def _get_metrics_as_string(self) -> str:
        """Retorna as métricas de uso como string."""
        try:
            if hasattr(self.metrics, 'get_dashboard_as_string'):
                return self.metrics.get_dashboard_as_string()
            elif hasattr(self.metrics, 'show_dashboard'):
                import io, sys
                captured_output = io.StringIO()
                sys.stdout = captured_output
                self.metrics.show_dashboard()
                sys.stdout = sys.__stdout__
                dashboard = captured_output.getvalue()
                
                if hasattr(self.ab_testing, 'show_results'):
                    captured_output = io.StringIO()
                    sys.stdout = captured_output
                    self.ab_testing.show_results()
                    sys.stdout = sys.__stdout__
                    dashboard += "\n\n" + captured_output.getvalue()
                
                return dashboard or "Nenhuma métrica disponível."
            else:
                return "Módulo de métricas não disponível."
        except Exception as e:
            logger.error(f"Erro ao obter métricas: {e}")
            return "Não foi possível recuperar as métricas."

    def _get_status_as_string(self) -> str:
        """Retorna o status atual dos módulos."""
        try:
            status_lines = ["📊 STATUS ATUAL DO NEXUS", ""]
            
            silent = "ON" if self.silent_mode.is_enabled() else "OFF"
            status_lines.append(f"🔇 Modo Silencioso: {silent}")
            
            pro = "OFF"
            if hasattr(self, 'proactive_mode') and self.proactive_mode.is_enabled():
                pro = "ON"
            status_lines.append(f"💬 Modo Proativo: {pro}")
            
            stability_pct = getattr(self.sentiment_stability.state, 'stability', 0) * 100
            status_lines.append(f"📈 Estabilidade de Sentimento: {stability_pct:.0f}%")
            
            try:
                fact_count = self.memory.get_fact_count() if hasattr(self.memory, 'get_fact_count') else "?"
                status_lines.append(f"🧠 Fatos armazenados: {fact_count}")
            except:
                status_lines.append("🧠 Fatos armazenados: ?")
            
            if hasattr(self.metrics, 'total_interactions'):
                status_lines.append(f"💬 Total de interações: {self.metrics.total_interactions}")
            
            return "\n".join(status_lines)
        except Exception as e:
            logger.error(f"Erro ao obter status: {e}")
            return "Não foi possível recuperar o status."

    def show_notes(self):
        """Exibe as notas de comportamento (para uso em console)."""
        if hasattr(self.behavior_notes, 'show_notes'):
            self.behavior_notes.show_notes()
        else:
            print("Função de notas não implementada.")

    def show_metrics(self):
        """Exibe o dashboard de métricas e testes A/B."""
        self.metrics.show_dashboard()
        self.ab_testing.show_results()

    def __del__(self):
        """Finaliza a sessão de métricas ao destruir a instância."""
        try:
            self.metrics.end_session()
        except Exception:
            pass