# 🤖 Nexus Agent — Sistema Agentivo de Automação e Suporte

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey)](https://www.sqlite.org/)
[![Sentence Transformers](https://img.shields.io/badge/Sentence%20Transformers-multilingual-orange)](https://www.sbert.net/)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-TTS-purple)](https://elevenlabs.io/)
[![Rich](https://img.shields.io/badge/Rich-CLI%20UI-ff69b4)](https://github.com/Textualize/rich)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Nexus Agent** é uma plataforma inteligente de automação e suporte que integra análise de sentimento, memória de longo prazo (SQLite), síntese de voz (ElevenLabs + offline), segurança de código, testes A/B e métricas de qualidade em uma arquitetura multi-agente adaptativa.

Projetado para cenários corporativos — atendimento ao cliente, CRM, suporte técnico e automação de infraestrutura — o Nexus oferece três perfis operacionais (Analítico, Colaborativo e Adaptativo) que se ajustam automaticamente ao contexto da conversa.

---

## ✨ Funcionalidades

### 🧠 Multi‑Agente Adaptativo
- **Analítico/Assertivo**: respostas diretas, técnicas e orientadas a resultados.
- **Colaborativo/Suporte**: tom paciente, didático e encorajador.
- **Adaptativo**: ajusta‑se em tempo real ao humor do usuário.

### 💾 Memória de Longo Prazo (SQLite)
- Persistência automática de fatos relevantes.
- Injeção de contexto histórico no prompt.
- Poda automática para evitar crescimento infinito.

### 🔊 Síntese de Voz
- Integração com **ElevenLabs** (voz neural realista).
- Fallback offline com **pyttsx3**.
- Suporte a streaming para baixa latência.

### 🛡️ Segurança e Governança
- **CodeGuard**: bloqueio de comandos destrutivos (`rm -rf`, `format C:`, fork bombs, etc.).
- **SecurityManager**: confinamento de arquivos ao diretório `build/`, rate limiting, sanitização de nomes.
- Sanitização de inputs contra injeção de prompt.

### 📊 Testes A/B & Otimização Contínua
- Comparação de variantes de personalidade.
- Métricas de vitória, uso e taxa de sucesso.
- Versionamento de comportamento com rollback.

### 📈 Métricas de Qualidade
- Sessões, mensagens, tokens processados, tempos de resposta.
- Índice de utilidade das respostas.
- Sentimento médio do usuário por sessão.

### 📝 Auto‑Evolução
- Geração de propostas de melhoria de código.
- Validação de sintaxe e aplicação segura com backup automático.

---

## 📐 Estrutura do Projeto

```bash
nexus-ai-agent/
├── main.py                     # CLI principal (Rich)
├── prompts/
│   └── system_prompt.py        # Definição das personas
├── config/
│   └── settings.py             # Configurações (.env)
├── core/
│   ├── nexus.py                # Coordenação dos módulos
│   ├── memory.py               # Memória de longo prazo
│   ├── database.py             # Abstração do SQLite
│   ├── sentiment.py            # Análise de sentimento
│   ├── command_extractor.py    # Extração de intenções
│   ├── security.py             # Barreiras de segurança
│   ├── code_guard.py           # Proteção contra comandos
│   ├── writer.py               # Escrita autônoma (build/)
│   ├── voice.py                # Síntese de voz
│   ├── silent_mode.py          # Modo silencioso
│   ├── proactive_mode.py       # Modo proativo
│   ├── sentiment_stability.py  # Estabilidade de sentimento
│   ├── ab_testing.py           # Testes A/B
│   ├── engagement_metrics.py   # Métricas de interação
│   ├── behavior_notes.py       # Notas de comportamento
│   ├── behavior_versioner.py   # Versionamento
│   ├── memory_manager.py       # Gerenciamento de RAM
│   ├── telemetry.py            # Logging
│   ├── improvement_prioritizer.py # Priorização
│   ├── auto_evolution.py       # Propostas de melhoria
│   ├── term_manager.py         # Termos de tratamento
│   ├── string_utils.py         # Utilitários de string
│   └── utils.py                # Funções auxiliares
├── data/                       # Banco SQLite (gerado)
├── build/                      # Arquivos gerados (gitignorado)
├── docs/                       # Documentação
├── tests/                      # Testes unitários
├── requirements.txt
└── .gitignore
```

---

## 🚀 Instalação e Uso

### Pré‑requisitos

- Python 3.10+
- (Opcional) Conta no [ElevenLabs](https://elevenlabs.io/) para TTS avançado

### 1. Clone o repositório

```bash
git clone https://github.com/ronaldokaras/nexus-ai-agent.git
cd nexus-ai-agent
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz:

```ini
OPENROUTER_API_KEY=sua_chave_aqui
MODEL_ID=google/gemini-2.0-flash-001
TEMPERATURE=0.90
MAX_HISTORY=30

# Voz (opcional)
USE_ELEVENLABS_VOICE=false
ELEVENLABS_API_KEY=sua_chave_elevenlabs
ELEVENLABS_VOICE_ID=cgSgspJ2msm6clMCkdW9
VOICE_ENABLED=false
```

### 5. Execute

```bash
python main.py
```

---

## 🎮 Comandos da CLI

| Comando | Ação |
|---------|------|
| `sair`, `exit`, `quit` | Encerra o agente |
| `limpar`, `clear` | Limpa o terminal |
| `reiniciar`, `reset` | Reinicia a conversa (zera memória) |
| `atualizar`, `reload` | Reinicia o programa |
| `.silencioso`, `modo silencioso` | Alterna modo silencioso |
| `.proativo`, `modo proativo` | Alterna modo proativo |
| `.voz`, `ativar voz` / `.silenciar` | Ativa/desativa voz |
| `.notes`, `mostra notas` | Exibe notas de comportamento |
| `.metrics`, `mostra métricas` | Exibe painel de métricas |
| `.status`, `status` | Estado atual dos módulos |
| `.help`, `ajuda` | Lista todos os comandos |

---

## 🧩 Tecnologias

- **OpenRouter** – gateway de LLMs
- **Sentence Transformers** – embeddings semânticos
- **scikit‑learn** – similaridade de cosseno
- **ElevenLabs** – TTS neural
- **pyttsx3** – TTS offline
- **Faster Whisper** – reconhecimento de fala
- **Rich** – terminal UI
- **SQLite** – banco de dados local

---

## 🤝 Contribuição

Sugestões são bem‑vindas via issues.

---

## 📄 Licença

MIT © Ronaldo Karas
```

---