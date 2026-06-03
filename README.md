# Social Content Agents

Framework de agentes de IA para criação automatizada de conteúdo para redes sociais.  
Gera copy, define a identidade visual, produz slides em HTML/PNG e gerencia o fluxo de imagem externa — tudo com um único comando.

---

## Sumário

- [Como funciona](#como-funciona)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [CLI — Referência completa](#cli--referência-completa)
- [Pipeline visual passo a passo](#pipeline-visual-passo-a-passo)
- [Formato do brief](#formato-do-brief)
- [API REST](#api-rest)
- [Rodando os testes](#rodando-os-testes)
- [Docker](#docker)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Roadmap](#roadmap)

---

## Como funciona

O framework orquestra um conjunto de agentes especializados que executam em sequência:

```
NicheIntelligenceAgent     → descobre o nicho, define ângulo editorial e tom de linguagem
ResearchAgent              → pesquisa contexto e fontes sobre o tema
TrendAgent + ProspectingAgent (paralelo)
CopyAgent                  → gera copies por plataforma com hook, corpo e CTA
VisualSpecAgent            → define paleta, tipografia, layout e tipo de slide
PromptEngineerAgent        → decide: HTML automático (95%) ou imagem externa (5%)
HTMLRenderer               → produz slides em HTML responsivo
PuppeteerExporter          → exporta HTML → PNG de alta resolução (2×)
```

### Filosofia do pipeline visual

> A imagem externa é a exceção, não a regra.  
> O sistema decide sozinho quando precisa — e quando não precisa, não pergunta.

**95 % dos slides** são gerados inteiramente em HTML com CSS puro: tipografia, gradientes, dados e screenshots.  
**5 % dos casos** — especificamente slides gancho (`SlideRole.GANCHO`) com tipo visual `FOTO_TEXTO` e tratamento `image-overlay` — o pipeline pausa, imprime o prompt para o operador e aguarda o upload da imagem.

---

## Pré-requisitos

| Requisito | Versão |
|-----------|--------|
| Python | ≥ 3.11 |
| Claude Code CLI | qualquer versão atual |
| Node.js (opcional, para PNG) | ≥ 18 |

**Não é necessário nenhuma API key** para o modo padrão.  
O framework usa o **Claude Code CLI** (`claude -p`) que já está autenticado no VS Code.

---

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/Felproenca/social-content-agents.git
cd social-content-agents

# Instalar dependências base
pip install -e .

# Com exportação PNG (requer Node.js)
pip install -e ".[visual]"

# Com API Anthropic direta (opcional)
pip install -e ".[anthropic]"

# Tudo + ferramentas de dev
pip install -e ".[visual,anthropic,dev]"
```

> **Alternativa sem setuptools** (ambientes gerenciados):
> ```bash
> pip install pydantic pydantic-settings fastapi uvicorn sqlalchemy aiosqlite httpx python-dotenv tenacity rich pytest pytest-asyncio
> ```

---

## Configuração

```bash
cp .env.example .env
```

As configurações mínimas já vêm preenchidas no `.env.example`. Edite conforme necessário:

```dotenv
# ── LLM ──────────────────────────────────────────────────────────────────────
# "claude_code" usa o CLI autenticado no VS Code — sem API key necessária.
# Troque para "anthropic" se quiser usar a SDK diretamente.
LLM_PROVIDER=claude_code
LLM_MODEL=                        # vazio = modelo padrão do provider

# Só preencher se LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# ── Storage ───────────────────────────────────────────────────────────────────
DATABASE_URL=sqlite:///./data/agents.db

# ── Publicação (opcional) ─────────────────────────────────────────────────────
LINKEDIN_ACCESS_TOKEN=
META_ACCESS_TOKEN=
TIKTOK_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN=
```

---

## CLI — Referência completa

O framework expõe três subcomandos:

```
python -m src.main <subcomando> [opções]
```

Ou, se instalado como pacote:

```
social-agents <subcomando> [opções]
```

---

### `generate` — Criar conteúdo

```bash
# Modo simples — só topic
python -m src.main generate --topic "Produtividade com IA" --platform linkedin

# Com brief completo (recomendado para pipeline visual)
python -m src.main generate --brief brief.json

# Opções disponíveis
python -m src.main generate --help
```

| Opção | Padrão | Descrição |
|-------|--------|-----------|
| `--topic TEXT` | `"Inteligência Artificial..."` | Tema do conteúdo |
| `--platform TEXT` | `linkedin` | Plataforma alvo |
| `--variations N` | `3` | Número de variações de copy |
| `--brief FILE` | — | Caminho para JSON de brief completo |

**Saída esperada:**

```
============================================================
Tópico:     Produtividade com IA
Status:     completo
Content ID: minha-empresa-produtividade-c-20260601-143022
Copies:     3
HTML:       5 slides → tmp/minha-empresa/slides
PNG:        5 exportados
============================================================
```

Se o pipeline detectar um slide que precisa de imagem externa, o status será `aguardando_imagens` e a mensagem abaixo será impressa:

```
============================================================
PIPELINE PAUSADO — IMAGEM NECESSÁRIA
============================================================
Cliente:               minha-empresa
Conteúdo:              minha-empresa-produtividade-c-20260601-143022
Slides automáticos:    [2, 3, 4, 5]
Aguardando imagem:     [1]
============================================================

SLIDE 1
----------------------------------------

PROMPT (cole no serviço externo):
Wide angle shot of a professional at their desk, soft window light...

NEGATIVO (o que evitar):
stock photo, forced smile, generic office...

NOTAS PARA VOCÊ:
Buscar tom cinza frio, ângulo levemente superior...

DICAS POR SERVIÇO:
  Midjourney: adicione ao final → --ar 1:1 --style raw
  Ideogram:   Realistic photo, cinematic lighting

============================================================
APÓS GERAR A IMAGEM:
  python -m src.main upload-image \
    --content minha-empresa-produtividade-c-20260601-143022 \
    --slide 1 \
    --file [CAMINHO_DA_IMAGEM]
============================================================
```

---

### `upload-image` — Registrar imagem gerada externamente

Após gerar a imagem no Midjourney, Ideogram, Pollinations ou DALL-E 3:

```bash
python -m src.main upload-image \
  --content minha-empresa-produtividade-c-20260601-143022 \
  --slide 1 \
  --file ~/Downloads/imagem-gerada.jpg
```

| Opção | Obrigatório | Descrição |
|-------|-------------|-----------|
| `--content` | sim | ID do conteúdo (impresso no passo anterior) |
| `--slide` | sim | Número do slide (ex: `1`) |
| `--file` | sim | Caminho da imagem baixada |

O que acontece internamente:
1. Copia a imagem para `tmp/{cliente}/slides/image-slide-01.jpg`
2. Injeta a imagem como `background-image` no HTML do slide com overlay gradiente
3. Marca o slide como `IMAGE_READY` no status persistido
4. Se **todos** os slides estiverem prontos: inicia a renderização final e exporta os PNGs automaticamente

---

### `serve` — Iniciar a API REST

```bash
python -m src.main serve
# ou simplesmente
uvicorn src.main:app --reload
```

Acesse `http://localhost:8000/docs` para a documentação interativa (Swagger UI).

---

## Pipeline visual passo a passo

### 1. Prepare o brief

Crie um arquivo `brief.json` (veja [Formato do brief](#formato-do-brief) abaixo).

### 2. Gere o conteúdo

```bash
python -m src.main generate --brief brief.json
```

### 3a. Se `status: completo`

Os slides HTML estão em `tmp/{client_slug}/slides/` e os PNGs em `tmp/{client_slug}/slides/png/`.

### 3b. Se `status: aguardando_imagens`

1. Leia o prompt impresso no terminal
2. Cole no serviço de sua escolha (Midjourney, Ideogram, etc.)
3. Baixe a imagem gerada
4. Rode o comando `upload-image` indicado
5. Repita para cada slide pendente
6. Ao registrar o último, o pipeline renderiza automaticamente

### 4. Encontre os arquivos

```
tmp/
  {client_slug}/
    slides/
      slide-01.html
      slide-02.html
      ...
      image-slide-01.jpg   ← imagem injetada (quando houver)
      png/
        slide-01.png
        slide-02.png
        ...
    status/
      {content_id}.json    ← estado persistido do pipeline
```

---

## Formato do brief

O brief é um JSON com a descrição completa do cliente e do conteúdo.

```json
{
  "nicho": "marketing digital",
  "tema": "Como usar IA para aumentar engajamento",
  "objetivo": "awareness",
  "plataforma": "instagram",
  "tom": "thought_leader",
  "audiencia": "Empreendedores e profissionais de marketing",
  "format": "4:5",
  "client_slug": "minha-empresa",
  "contexto_cliente": {
    "nome": "Minha Empresa",
    "palette": {
      "primary":    "#0a0a0a",
      "secondary":  "#1a1a2e",
      "accent":     "#e94560",
      "background": "#0a0a0a",
      "text":       "#ffffff",
      "text_light": "#aaaaaa"
    },
    "typography": {
      "heading": "Playfair Display",
      "body":    "Inter"
    }
  }
}
```

### Campos do brief

| Campo | Obrigatório | Valores aceitos |
|-------|-------------|-----------------|
| `nicho` | sim | qualquer string |
| `tema` | não | string — deixar em branco = agente decide |
| `objetivo` | não | `awareness` · `autoridade` · `conversao` |
| `plataforma` | não | `linkedin` · `instagram` · `tiktok` · `youtube` · `twitter` |
| `tom` | não | `thought_leader` · `educativo` · `provocativo` |
| `audiencia` | não | descrição da audiência alvo |
| `format` | não | `1:1` · `4:5` · `9:16` |
| `client_slug` | não | identificador curto do cliente (ex: `acme`) |
| `contexto_cliente` | não | objeto com paleta e tipografia (ativa o pipeline visual) |

> Sem `contexto_cliente`, o pipeline gera apenas copy (sem slides).

### Paleta e tipografia

A paleta aceita qualquer cor CSS (`#hex`, `rgb()`, etc.).

Para tipografia, recomenda-se fontes disponíveis no Google Fonts.  
Padrões: `Playfair Display` (heading) · `Inter` (body) · `Syne Mono` (mono).

### Estilos visuais automáticos

O `VisualSpecAgent` escolhe o estilo automaticamente com base na hierarquia:

1. **Estilo explícito do cliente** (se configurado como diferente de `CLEAN`)
2. **Hint por nicho** — ex: `tech` e `saas` → `TECHNICAL`; `bem-estar` → `WARM`
3. **Posição editorial** — ex: `PROVOCACAO` → `BOLD`; `EDUCACAO` → `CLEAN`

| Estilo | Descrição |
|--------|-----------|
| `CLEAN` | Muito espaço, elegante, premium |
| `DARK` | Fundo escuro, contraste alto |
| `BOLD` | Tipografia grande, impacto direto |
| `EDITORIAL` | Estilo revista, foto + texto |
| `TECHNICAL` | Grid, monospace, dados, terminal |
| `WARM` | Cores quentes, humano, próximo |

---

## API REST

Com o servidor rodando em `http://localhost:8000`:

### `GET /health`
```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}
```

### `POST /content/generate`
```bash
curl -X POST http://localhost:8000/content/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "IA no marketing digital",
    "platform": "linkedin",
    "variations": 3
  }'
```

### `POST /campaign/build`
```bash
curl -X POST http://localhost:8000/campaign/build \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Campanha Q3",
    "topic": "Produtividade com IA",
    "platforms": ["linkedin", "instagram"],
    "variations_per_platform": 2
  }'
```

Documentação interativa completa em `http://localhost:8000/docs`.

---

## Uso via Python

```python
import asyncio
from src.workflows.content_factory import ContentFactory

async def main():
    factory = ContentFactory()
    result = await factory.run_from_brief({
        "nicho": "marketing digital",
        "tema": "Como usar IA para triplicar sua produção de conteúdo",
        "objetivo": "awareness",
        "plataforma": "instagram",
        "format": "4:5",
        "client_slug": "acme",
        "contexto_cliente": {
            "nome": "ACME Marketing",
            "palette": {
                "primary": "#0a0a0a",
                "secondary": "#1a1a2e",
                "accent": "#e94560",
                "background": "#0a0a0a",
                "text": "#ffffff",
                "text_light": "#aaaaaa",
            },
            "typography": {"heading": "Playfair Display", "body": "Inter"},
        },
    })

    print(f"Status: {result.status}")
    print(f"Copies: {len(result.copies)}")
    print(f"Slides HTML: {result.html_paths}")

asyncio.run(main())
```

### Retomar pipeline após imagem (Python)

```python
from src.skills.image_integrator import ImageIntegrator
from pathlib import Path

integrator = ImageIntegrator()
updated_status = await integrator.integrate(
    status=pipeline_status,
    slide_number=1,
    image_path="/caminho/para/imagem.jpg",
    html_dir=Path("tmp/acme/slides"),
)
```

---

## Rodando os testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=src --cov-report=term-missing

# Apenas um módulo
pytest tests/test_prompt_engineer.py -v
pytest tests/test_visual_pipeline.py -v
pytest tests/test_niche_discovery.py -v
```

Suite atual: **33 testes**, cobrindo:
- Geração e cache de perfis de nicho
- Pipeline visual (derivação de estilo, roles de slides, geração de HTML)
- Lógica híbrida do PromptEngineerAgent (gate de 3 condições + 3 cenários de análise)

---

## Docker

```bash
# Build e subir todos os serviços
docker-compose up --build

# Apenas a API
docker-compose up api

# Em background
docker-compose up -d
```

A API ficará disponível em `http://localhost:8000`.

---

## Estrutura do projeto

```
social-content-agents/
├── src/
│   ├── main.py                     # Entrypoint CLI + FastAPI
│   ├── core/
│   │   ├── agent.py                # Classe base Agent (ABC)
│   │   ├── config.py               # Settings via pydantic-settings + .env
│   │   ├── llm.py                  # LLMProvider: ClaudeCodeProvider | AnthropicProvider
│   │   ├── memory.py               # Memória deslizante por sessão
│   │   ├── models.py               # Todos os dataclasses compartilhados
│   │   ├── orchestrator.py         # run_sequential / run_parallel
│   │   └── skill.py                # Classe base Skill (ABC)
│   ├── agents/
│   │   ├── niche_intelligence_agent.py   # Descobre nicho, ângulo e posição editorial
│   │   ├── visual_spec_agent.py          # Gera VisualSpec completo
│   │   ├── prompt_engineer_agent.py      # Decide HTML-only vs imagem externa
│   │   ├── copy_agent.py                 # Gera copies niche-aware
│   │   ├── research_agent.py             # Pesquisa contexto e fontes
│   │   ├── trend_agent.py                # Identifica tendências
│   │   ├── prospecting_agent.py          # Audiências e oportunidades
│   │   ├── performance_agent.py          # Análise de métricas + aprendizado
│   │   ├── publishing_agent.py           # Publicação via APIs oficiais
│   │   └── design_agent.py               # Prompts visuais para geração de imagem
│   ├── skills/
│   │   ├── niche_discovery.py            # Cache + descoberta LLM de perfis de nicho
│   │   ├── html_renderer.py              # HTML → slides responsivos por role
│   │   ├── puppeteer_exporter.py         # HTML → PNG (pyppeteer, opcional)
│   │   ├── image_integrator.py           # Injeta imagem externa no slide HTML
│   │   ├── operator_notifier.py          # Formata notificação com prompt e instrução
│   │   ├── viral_hook/                   # 5 tipos de gancho viral
│   │   ├── copywriting/
│   │   ├── design_prompt/
│   │   ├── platform_formatter/
│   │   ├── trend_research/
│   │   └── analytics_insights/
│   ├── platforms/
│   │   ├── instagram.py
│   │   ├── linkedin.py
│   │   ├── tiktok.py
│   │   ├── x_twitter.py
│   │   └── youtube.py
│   ├── workflows/
│   │   ├── content_factory.py      # Pipeline principal
│   │   ├── campaign_builder.py     # Multi-plataforma em lote
│   │   └── auto_publish.py         # Publicação automática
│   └── storage/
│       ├── db.py
│       └── models.py
├── tests/
│   ├── test_niche_discovery.py     # 8 testes
│   ├── test_visual_pipeline.py     # 14 testes
│   └── test_prompt_engineer.py     # 11 testes
├── data/
│   └── niches/                     # Cache JSON de perfis de nicho (gerado automaticamente)
├── tmp/                            # Output dos pipelines (não versionado)
├── .env.example
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

---

## Variáveis de ambiente — referência completa

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `LLM_PROVIDER` | `claude_code` | `claude_code` usa o CLI; `anthropic` usa SDK |
| `LLM_MODEL` | _(vazio)_ | Modelo específico; vazio = padrão do provider |
| `ANTHROPIC_API_KEY` | — | Só necessário com `LLM_PROVIDER=anthropic` |
| `OPENAI_API_KEY` | — | Reservado para provider OpenAI |
| `GOOGLE_API_KEY` | — | Reservado para provider Google |
| `DATABASE_URL` | `sqlite:///./data/agents.db` | SQLite (dev) ou PostgreSQL (prod) |
| `APP_ENV` | `development` | `development` \| `production` |
| `LOG_LEVEL` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |
| `API_HOST` | `0.0.0.0` | Host do servidor FastAPI |
| `API_PORT` | `8000` | Porta do servidor FastAPI |
| `LINKEDIN_ACCESS_TOKEN` | — | Token OAuth do LinkedIn (PublishingAgent) |
| `META_ACCESS_TOKEN` | — | Token da Meta (Instagram/Facebook) |
| `TIKTOK_ACCESS_TOKEN` | — | Token do TikTok |
| `TWITTER_ACCESS_TOKEN` | — | Token do X/Twitter |

---

## Roadmap

- [x] Core: Agent, Skill, Orchestrator, Memory, Config
- [x] NicheIntelligenceAgent — descoberta dinâmica de nicho com cache e aprendizado
- [x] VisualSpecAgent — derivação automática de estilo, paleta, tipografia e layout
- [x] HTMLRenderer — slides responsivos por role com CSS puro
- [x] PuppeteerExporter — PNG de alta resolução (2×) via pyppeteer
- [x] PromptEngineerAgent — pipeline híbrido: HTML automático + imagem externa on demand
- [x] ImageIntegrator + OperatorNotifier — fluxo completo de imagem externa
- [x] CLI completo: `generate`, `upload-image`, `serve`
- [x] Agents: Research, Trend, Copy, Design, Prospecting, Performance, Publishing
- [x] Skills: copywriting, design_prompt, trend_research, platform_formatter, viral_hook, analytics_insights
- [x] Plataformas: LinkedIn, Instagram, TikTok, YouTube, X/Twitter
- [ ] API REST completa com autenticação
- [ ] Dashboard de métricas e performance
- [ ] Integração com APIs de publicação (LinkedIn, Meta, TikTok)
- [ ] Scheduler de posts com recorrência
- [ ] Fine-tuning do CopyAgent por performance histórica
- [ ] Suporte a OpenAI e Gemini como providers alternativos
