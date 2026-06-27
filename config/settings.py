"""
config/settings.py - Configurações centralizadas do Nexus Agent
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==================== CHAVES DE API ====================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# ==================== MODELOS ====================
# Modelo usado via OpenRouter (ex: google/gemini-2.0-flash-001, anthropic/claude-3-haiku)
MODEL_ID = os.getenv("MODEL_ID", "google/gemini-2.0-flash-001")

# ==================== PARÂMETROS DE COMPORTAMENTO ====================
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.90"))
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "30"))

# ==================== CONFIGURAÇÕES DE VOZ (ElevenLabs) ====================
USE_ELEVENLABS_VOICE = os.getenv("USE_ELEVENLABS_VOICE", "false").lower() == "true"
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "cgSgspJ2msm6clMCkdW9")
VOICE_ENABLED = os.getenv("VOICE_ENABLED", "false").lower() == "true"

# ==================== CONFIGURAÇÕES DE TTS OFFLINE ====================
TTS_OFFLINE_RATE = int(os.getenv("TTS_OFFLINE_RATE", "172"))
TTS_OFFLINE_VOLUME = float(os.getenv("TTS_OFFLINE_VOLUME", "0.95"))

# ==================== MODO ESCUTA (STT) ====================
LISTEN_DURATION = float(os.getenv("LISTEN_DURATION", "5.5"))
LISTEN_SAMPLE_RATE = int(os.getenv("LISTEN_SAMPLE_RATE", "16000"))