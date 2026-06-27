"""
core/voice.py - Módulo de Síntese de Voz e Acessibilidade do Nexus Agent
Suporte a ElevenLabs (voz realista) e fallback offline (pyttsx3)
"""

import os
import tempfile
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# TTS Offline
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# STT
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Áudio
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

# ElevenLabs
try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import play, stream
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

# Configurações do .env
USE_ELEVENLABS = os.getenv("USE_ELEVENLABS_VOICE", "false").lower() == "true"
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "cgSgspJ2msm6clMCkdW9")


class NexusVoice:
    """
    Gerenciador de voz do Nexus Agent.
    
    Prioridade:
    1. ElevenLabs (voz realista)
    2. pyttsx3 (fallback offline)
    """

    def __init__(self):
        self.tts_engine = None
        
        # ==================== TTS (Text-to-Speech) ====================
        self.use_elevenlabs = USE_ELEVENLABS and ELEVENLABS_AVAILABLE and ELEVENLABS_API_KEY
        
        if PYTTSX3_AVAILABLE:
            self._init_pyttsx3()
        
        if self.use_elevenlabs:
            self._init_elevenlabs()
        
        if not self.use_elevenlabs and not self.tts_engine:
            print("⚠️ Nenhum TTS disponível. Instale pyttsx3 ou elevenlabs")
        
        # ==================== STT (Speech-to-Text) ====================
        self._init_whisper()
        
        self.sample_rate = 16000
        self.default_duration = 5.5

    def _init_elevenlabs(self):
        """Inicializa o ElevenLabs para voz realista."""
        try:
            self.eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            self.eleven_voice_id = ELEVENLABS_VOICE_ID
            self.eleven_model = "eleven_multilingual_v2"
            self.use_elevenlabs = True
            print("🔊 ElevenLabs inicializado (síntese de voz corporativa)")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar ElevenLabs: {e}")
            self.use_elevenlabs = False

    def _init_pyttsx3(self):
        """Inicializa o pyttsx3 para TTS offline (fallback)."""
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 172)
            self.tts_engine.setProperty('volume', 0.95)
            
            # Tenta selecionar voz feminina em português
            voices = self.tts_engine.getProperty('voices')
            for v in voices:
                if 'portuguese' in v.name.lower() or 'brazil' in v.name.lower():
                    self.tts_engine.setProperty('voice', v.id)
                    break
            
            print("🔊 pyttsx3 inicializado (síntese offline)")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar pyttsx3: {e}")
            self.tts_engine = None

    def _init_whisper(self):
        """Inicializa o Faster-Whisper para STT."""
        if WHISPER_AVAILABLE:
            try:
                self.stt_model = WhisperModel("base", device="cpu", compute_type="int8")
                print("🎙️ Whisper inicializado (reconhecimento de fala)")
            except Exception as e:
                print(f"⚠️ Erro ao inicializar Whisper: {e}")
                self.stt_model = None
        else:
            self.stt_model = None

    # ==================== TTS (Fala) ====================

    def speak(self, text: str, use_streaming: bool = True) -> bool:
        """
        Converte texto em fala.
        
        Args:
            text: Texto para sintetizar
            use_streaming: Se True, usa streaming (menor latência)
            
        Returns:
            bool: True se sucesso
        """
        if not text:
            return False
        
        if len(text) > 500:
            text = text[:500] + "..."
        
        if self.use_elevenlabs and hasattr(self, 'eleven_client') and self.eleven_client:
            try:
                return self._speak_elevenlabs(text, use_streaming)
            except Exception as e:
                print(f"⚠️ ElevenLabs falhou: {e}")
                if self.tts_engine:
                    print("🔄 Mudando para voz offline...")
                    return self._speak_pyttsx3(text)
                return False
        
        if self.tts_engine:
            return self._speak_pyttsx3(text)
        
        print(f"🔊 (sem voz) Nexus Agent diria: {text[:100]}...")
        return False

    def _speak_elevenlabs(self, text: str, use_streaming: bool = True) -> bool:
        """Fala usando ElevenLabs (voz realista)."""
        try:
            if use_streaming:
                try:
                    audio_stream = self.eleven_client.text_to_speech.stream(
                        text=text,
                        voice_id=self.eleven_voice_id,
                        model_id="eleven_flash_v2_5",
                    )
                    stream(audio_stream)
                    return True
                except Exception as e:
                    if "mpv" in str(e) or "stream" in str(e).lower():
                        print("🔊 Streaming falhou, tentando método alternativo...")
                        return self._speak_elevenlabs(text, use_streaming=False)
                    raise e
            else:
                audio = self.eleven_client.text_to_speech.convert(
                    text=text,
                    voice_id=self.eleven_voice_id,
                    model_id=self.eleven_model,
                    output_format="mp3_44100_128",
                )
                
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    for chunk in audio:
                        tmp.write(chunk)
                    tmp_path = tmp.name
                
                try:
                    os.startfile(tmp_path)
                except:
                    try:
                        import subprocess
                        subprocess.run(["start", tmp_path], shell=True)
                    except:
                        print(f"🔊 Áudio salvo em: {tmp_path}")
                
                return True
        except Exception as e:
            print(f"❌ Erro no ElevenLabs: {e}")
            if self.tts_engine:
                print("🔄 Mudando para voz offline...")
                return self._speak_pyttsx3(text)
            return False

    def _speak_pyttsx3(self, text: str) -> bool:
        """Fala usando pyttsx3 (voz offline)."""
        try:
            print(f"🔊 Nexus Agent: {text[:100]}..." if len(text) > 100 else f"🔊 Nexus Agent: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            return True
        except Exception as e:
            print(f"❌ Erro no pyttsx3: {e}")
            return False

    # ==================== STT (Escuta) ====================

    def listen(self, duration: float = None) -> str:
        """
        Escuta o microfone e transcreve o que foi dito.
        
        Args:
            duration: Duração em segundos (padrão: 5.5)
            
        Returns:
            str: Texto transcrito ou "[não entendi]" se falhar
        """
        if not SOUNDDEVICE_AVAILABLE or not self.stt_model:
            print("🎙️ Sistema de escuta não disponível")
            return "[não entendi]"
        
        duration = duration or self.default_duration
        
        try:
            import winsound
            winsound.Beep(800, 200)
        except:
            print("\a")
        
        print(f"🎙️ Ouvindo... fale agora ({duration} segundos)")
        
        try:
            recording = sd.rec(int(duration * self.sample_rate), 
                               samplerate=self.sample_rate, 
                               channels=1, 
                               dtype='float32')
            sd.wait()
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                import wave
                with wave.open(tmp.name, 'w') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes((recording * 32767).astype(np.int16).tobytes())
                
                segments, _ = self.stt_model.transcribe(tmp.name, language="pt")
                os.unlink(tmp.name)
            
            text = " ".join(seg.text for seg in segments).strip()
            return text if text else "[não entendi]"
            
        except Exception as e:
            print(f"❌ Erro ao escutar: {e}")
            return "[não entendi]"

    # ==================== UTILIDADES ====================

    def change_elevenlabs_voice(self, voice_id: str) -> bool:
        """Altera a voz do ElevenLabs."""
        if not self.use_elevenlabs or not hasattr(self, 'eleven_client'):
            print("⚠️ ElevenLabs não está ativo")
            return False
        
        self.eleven_voice_id = voice_id
        print(f"🔊 Voz alterada para: {voice_id}")
        return True

    def list_elevenlabs_voices(self) -> list:
        """Lista vozes disponíveis no ElevenLabs."""
        if not self.use_elevenlabs or not hasattr(self, 'eleven_client'):
            print("⚠️ ElevenLabs não está ativo")
            return []
        
        try:
            response = self.eleven_client.voices.get_all()
            voices = []
            for v in response.voices:
                voices.append({"name": v.name, "id": v.voice_id})
                print(f"🔊 {v.name} - {v.voice_id}")
            return voices
        except Exception as e:
            print(f"❌ Erro ao listar vozes: {e}")
            return []

    def is_elevenlabs_available(self) -> bool:
        """Verifica se o ElevenLabs está disponível e configurado."""
        return self.use_elevenlabs and hasattr(self, 'eleven_client') and self.eleven_client is not None

    def get_status(self) -> dict:
        """Retorna o status do módulo de voz."""
        return {
            "tts_elevenlabs": self.is_elevenlabs_available(),
            "tts_offline": self.tts_engine is not None,
            "stt_available": self.stt_model is not None,
            "current_voice_id": self.eleven_voice_id if self.use_elevenlabs else None
        }


# Instância global do módulo de voz
voice = NexusVoice()