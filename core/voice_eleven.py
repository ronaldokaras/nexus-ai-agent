# core/voice_eleven.py
"""
Módulo de síntese de voz via ElevenLabs para o Nexus Agent.
Voz realista e natural para acessibilidade.
"""

import os
from pathlib import Path
from typing import Optional

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import play
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("⚠️ elevenlabs não instalado. Instale com: pip install elevenlabs")

class ElevenLabsVoice:
    """Integração com ElevenLabs para voz realista e profissional."""

    # Vozes em português adequadas para uso corporativo
    PORTUGUESE_VOICES = {
        "portuguese_female": "21m00Tcm4TlvDq8ikWAM",  # Rachel (ótima para PT)
        "portuguese_male": "AZnzlk1XvdvUeBnXmlld",     # Dominic
        "soft_female": "EXAVITQu4vr4xnSDxMaL",         # Bella (tom suave)
        "clear_female": "ThT5KcbeYPX3keUQqHPh",        # Antonia (voz clara)
    }

    def __init__(self, api_key: str = None, voice_id: str = None):
        if not ELEVENLABS_AVAILABLE:
            raise ImportError("ElevenLabs não está instalado.")

        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY não encontrada no .env")

        self.client = ElevenLabs(api_key=self.api_key)
        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        self.model_id = "eleven_multilingual_v2"  # Suporta português!

    def speak(self, text: str, save_to_file: Optional[str] = None) -> bool:
        """
        Converte texto em fala e reproduz.

        Args:
            text: Texto para sintetizar
            save_to_file: Se fornecido, salva o áudio no caminho especificado

        Returns:
            bool: True se sucesso
        """
        try:
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id,
                output_format="mp3_44100_128",
            )

            if save_to_file:
                with open(save_to_file, "wb") as f:
                    for chunk in audio:
                        f.write(chunk)
                print(f"📁 Áudio salvo em: {save_to_file}")
            else:
                play(audio)

            return True

        except Exception as e:
            print(f"❌ Erro ao gerar fala: {e}")
            return False

    def speak_stream(self, text: str) -> bool:
        """Streaming para respostas mais rápidas (baixa latência)."""
        try:
            audio_stream = self.client.text_to_speech.stream(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_flash_v2_5",
            )

            from elevenlabs import stream
            stream(audio_stream)
            return True

        except Exception as e:
            print(f"❌ Erro no streaming: {e}")
            return False

    def list_voices(self):
        """Lista todas as vozes disponíveis."""
        try:
            response = self.client.voices.search()
            for voice in response.voices:
                print(f"🎤 {voice.name} - ID: {voice.voice_id} - Categoria: {voice.category}")
        except Exception as e:
            print(f"❌ Erro ao listar vozes: {e}")

    def change_voice(self, voice_id: str):
        """Muda a voz atual."""
        self.voice_id = voice_id
        print(f"🎤 Voz alterada para ID: {voice_id}")


# Instância global
eleven_voice = None

def get_voice():
    """Retorna a instância global do ElevenLabsVoice."""
    global eleven_voice
    if eleven_voice is None and ELEVENLABS_AVAILABLE:
        try:
            eleven_voice = ElevenLabsVoice()
        except Exception as e:
            print(f"⚠️ Não foi possível inicializar ElevenLabs: {e}")
    return eleven_voice