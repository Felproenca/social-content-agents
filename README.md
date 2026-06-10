# MarketingOS Reference Library

Diretório de referências para o MarketingOS — animações Three.js, GSAP, sistemas de cores e identidades visuais. Estruturado para que o agente encontre e use referências precisas ao criar qualquer conteúdo.

---

## Como funciona

O MarketingOS carrega `references/index.json` (leve, ~5KB) para identificar referências relevantes e depois lê o JSON completo de cada uma para obter código, paletas e notas de uso.

```
references/
  index.json                         ← índice flat: IDs, tags, descrições (carrega primeiro)
  animations/
    three-js/
      particle-systems.json          ← código + config + notas de adaptação
      scroll-scene.json
      morphing-geometry.json
    gsap/
      scroll-trigger.json
      text-reveal.json
      stagger-entrance.json
  visual/
    styles/
      editorial-dark.json            ← paleta + tipografia + CSS snippet + princípios
      bold-typographic.json
      clean-minimal.json
    color-systems/
      finance.json                   ← paletas por sub-setor (ex: Trust Blue, Fintech Dark)
      tech-saas.json
      wellness.json
      creative-agency.json
  identities/
    _schema.json                     ← template para adicionar cliente
    {client-slug}/
      identity.json                  ← identidade completa do cliente
```

---

## CLI de busca

```bash
# Busca por keywords
python -m src.query search "particle dark background"
python -m src.query search "scroll reveal typography"
python -m src.query search "fintech color palette"

# Filtrar por categoria
python -m src.query search --category animations/three-js
python -m src.query search --category visual/color-systems --tag finance

# Ver referência completa (JSON)
python -m src.query get three-js-particle-systems
python -m src.query get editorial-dark

# Ver identidade de um cliente
python -m src.query client acme-corp

# Listar tudo
python -m src.query list
python -m src.query list --category animations
```

### Exemplos de saída

```
python -m src.query search "dark luxury editorial"

Encontradas 2 referência(s):

  [visual/styles] Estilo Editorial Dark
  Estilo de revista de luxo — fundo escuro, serif elegante, muito espaço negativo
  Tags: dark, luxury, editorial, serif, high-contrast, premium
  Arquivo: references/visual/styles/editorial-dark.json

  [visual/color-systems] Sistema de Cores — Finanças
  Trust Blue, Fintech Dark, Wealth Gold — paletas para o setor financeiro
  Tags: finance, banking, fintech, investment, trust, money
  Arquivo: references/visual/color-systems/finance.json
```

---

## Uso via Python (para o MarketingOS)

```python
from src.query import search, load_reference, search_for_marketing_os

# Busca por keywords
results = search(["dark", "particle", "three.js"])
for ref in results:
    print(ref["id"], ref["file"])

# Carrega referência completa
ref = load_reference("references/animations/three-js/particle-systems.json")
code = ref["code"]["js"]          # código JavaScript pronto
config = ref["code"]["config_options"]  # opções configuráveis
notes = ref["adaptation_notes"]   # como adaptar para o cliente

# Busca com contexto do brief
refs = search_for_marketing_os({
    "sector": "finance",
    "style": "dark",
    "mood": "luxury premium",
    "category": "visual/color-systems"
})
```

---

## Estrutura de uma referência de animação

```json
{
  "id": "three-js-particle-systems",
  "title": "Particle Systems",
  "description": "...",
  "category": "animations",
  "subcategory": "three-js",
  "tags": ["particles", "background", "ambient", "WebGL"],
  "use_cases": ["hero background", "tech brand"],
  "complexity": "low",
  "performance_cost": "low",
  "dependencies": ["three"],
  "install": "npm install three",
  "visual": {
    "mood": ["tecnológico", "etéreo"],
    "styles_pair_well": ["DARK", "TECHNICAL"],
    "best_on_backgrounds": ["dark", "black"]
  },
  "variants": [
    { "name": "Floating Dust", "description": "..." },
    { "name": "Connected Network", "description": "..." }
  ],
  "code": {
    "html": "...",
    "css": "...",
    "js": "...",
    "config_options": { "COUNT": "...", "size": "..." }
  },
  "adaptation_notes": "Para usar a cor do cliente: ..."
}
```

---

## Estrutura de um sistema de cores

```json
{
  "id": "color-finance",
  "title": "Sistema de Cores — Finanças",
  "category": "visual",
  "subcategory": "color-systems",
  "tags": ["finance", "banking", "fintech"],
  "palettes": [
    {
      "name": "Trust Blue",
      "sub_sector": "Banco tradicional",
      "mood": "Confiança, solidez",
      "colors": {
        "primary": "#1a3a5c",
        "secondary": "#2d5f8a",
        "accent": "#4a9fd4",
        "background": "#f8fafc",
        "text": "#1a2533"
      },
      "usage": "Tom institucional para bancos e gestoras."
    }
  ],
  "typography_recommendations": { "traditional": ["Playfair Display + Inter"] },
  "animation_notes": "Movimentos lentos e suaves para transmitir solidez."
}
```

---

## Adicionando referências

### Nova animação

1. Crie `references/animations/three-js/nome.json` ou `references/animations/gsap/nome.json`
2. Siga a estrutura acima (campos obrigatórios: `id`, `title`, `description`, `category`, `subcategory`, `tags`, `code`)
3. Adicione a entrada em `references/index.json`

### Nova identidade de cliente

```bash
mkdir references/identities/nome-cliente
cp references/identities/_schema.json references/identities/nome-cliente/identity.json
# edite identity.json com os dados do cliente
```

Adicione a entrada no `references/index.json` com category `identities`.

---

## Referências disponíveis

### Animações — Three.js

| ID | Descrição | Complexidade |
|----|-----------|--------------|
| `three-js-particle-systems` | Partículas flutuantes para backgrounds | Baixa |
| `three-js-scroll-scene` | Cena 3D controlada pelo scroll | Média |
| `three-js-morphing-geometry` | Morph entre formas geométricas 3D | Média |

### Animações — GSAP

| ID | Descrição | Complexidade |
|----|-----------|--------------|
| `gsap-scroll-trigger` | Reveal de seções ao scroll (fade, clip, parallax, pin) | Baixa |
| `gsap-text-reveal` | Reveal de texto — linha, palavra, char, contador | Baixa |
| `gsap-stagger-entrance` | Entrada em cascata para cards e grids | Baixa |

### Estilos Visuais

| ID | Descrição |
|----|-----------|
| `editorial-dark` | Revista de luxo — dark, serif, muito espaço negativo |
| `bold-typographic` | A tipografia é o design — fontes grandes e pesadas |
| `clean-minimal` | Elegância pela subtração — SaaS, B2B, healthcare |

### Sistemas de Cores por Setor

| ID | Paletas incluídas |
|----|-------------------|
| `color-finance` | Trust Blue · Fintech Dark · Wealth Gold |
| `color-tech-saas` | Corporate SaaS · Dev Dark · Startup Vibrant · AI Native |
| `color-wellness` | Natural Earth · Clinical Trust · Fitness Energy · Mindful Lavender |
| `color-creative-agency` | Brutalist Pop · Digital Noir · Vibrant Studio |

---

## Instalação

```bash
git clone https://github.com/Felproenca/social-content-agents.git
cd social-content-agents
pip install -e .
```

Sem dependências obrigatórias além de Python 3.11+.
