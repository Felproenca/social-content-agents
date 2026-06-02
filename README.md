# Social Content Agents

Framework de deep agents e skills para automação inteligente de criação de conteúdo em escala.

## Objetivo

Criar, adaptar, otimizar e publicar conteúdos para redes sociais usando agentes especializados, skills reutilizáveis, análise de tendências e melhoria contínua por performance.

## Arquitetura

```
src/
  core/           # Motor do framework: Agent, Skill, Orchestrator, Memory, Config
  agents/         # Agentes especializados por função
  skills/         # Skills reutilizáveis com SKILL.md + implementação
  platforms/      # Adaptadores por rede social
  workflows/      # Pipelines de alto nível
  storage/        # Modelos e persistência
```

## Agentes

| Agente | Responsabilidade |
|--------|-----------------|
| `ResearchAgent` | Pesquisa tópicos, fontes e contexto |
| `TrendAgent` | Identifica tendências por plataforma e nicho |
| `CopyAgent` | Gera e itera variações de copy |
| `DesignAgent` | Cria prompts visuais para geração de imagens |
| `ProspectingAgent` | Identifica audiências e oportunidades |
| `PerformanceAgent` | Analisa métricas e retroalimenta o sistema |
| `PublishingAgent` | Publica e agenda conteúdo via APIs oficiais |

## Skills

| Skill | Função |
|-------|--------|
| `copywriting` | Escreve copies por plataforma, tom e objetivo |
| `design_prompt` | Engenharia de prompts para geração de imagens |
| `trend_research` | Pesquisa tendências em tempo real |
| `platform_formatter` | Formata conteúdo para cada plataforma |
| `viral_hook` | Gera ganchos virais para abertura de conteúdo |
| `analytics_insights` | Extrai insights acionáveis de métricas |

## Plataformas suportadas

LinkedIn · Instagram · TikTok · YouTube · X/Twitter

## Stack

- **Runtime**: Python 3.11+
- **Orquestração**: LangGraph (padrão) ou CrewAI (plugável)
- **LLMs**: Claude (padrão), OpenAI, Gemini — configurável por `.env`
- **Storage**: SQLite (MVP) → PostgreSQL (produção)
- **API**: FastAPI
- **Deploy**: Docker + docker-compose

## Início rápido

```bash
# 1. Instalar dependências
pip install -e ".[dev]"

# 2. Configurar variáveis de ambiente
cp .env.example .env
# edite .env com suas chaves

# 3. Rodar o agente principal
python -m src.main

# 4. Ou via API
uvicorn src.main:app --reload
```

## Exemplo de uso

```python
from src.core.orchestrator import Orchestrator
from src.workflows.content_factory import ContentFactory

orchestrator = Orchestrator()
factory = ContentFactory(orchestrator)

result = await factory.run(
    topic="IA no marketing digital",
    platforms=["linkedin", "instagram"],
    tone="thought_leader",
    variations=3,
)
print(result.posts)
```

## Variáveis de ambiente

Ver `.env.example` para lista completa. Mínimo necessário:

```
ANTHROPIC_API_KEY=...   # LLM padrão
```

## Roadmap

- [x] Core: Agent, Skill, Orchestrator, Memory
- [x] Agents: Research, Trend, Copy, Design, Prospecting, Performance, Publishing
- [x] Skills: copywriting, design_prompt, trend_research, platform_formatter, viral_hook, analytics_insights
- [x] Platforms: LinkedIn, Instagram, TikTok, YouTube, X/Twitter
- [x] Workflows: ContentFactory, CampaignBuilder, AutoPublish
- [ ] API REST completa (FastAPI)
- [ ] Dashboard de métricas
- [ ] Integração com APIs de publicação (LinkedIn, Meta, TikTok)
- [ ] Scheduler de posts
- [ ] Fine-tuning por performance histórica
