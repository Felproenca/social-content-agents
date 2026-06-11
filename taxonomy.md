# MarketingOS References — Taxonomia

> Este documento define o vocabulário do repositório.
> Nenhuma referência entra no repo sem obedecer esta taxonomia.
> Schema vem depois. Conteúdo vem depois. Vocabulário é a fundação.

---

## Por que este documento existe primeiro

Repositórios de referência sem taxonomia viram acúmulo.
Com taxonomia, viram infraestrutura.

A diferença: um sistema com taxonomia pode ser consultado por um agente
com precisão cirúrgica. Sem ela, o agente adivinha — e erra.

---

## 1. Types — O que uma referência É

O campo `type` define a natureza da referência, não onde ela mora.

| Type | O que é | Exemplo |
|------|---------|---------|
| `site` | Website real, com identidade visual e copy observáveis | linear.app |
| `copy` | Padrão textual — um hook, manifesto, estrutura de oferta | Hook de escassez + autoridade |
| `motion` | Padrão de animação com código ou análise técnica | GSAP scroll reveal |
| `visual` | Padrão visual — estilo, layout, sistema tipográfico | Editorial dark |
| `color-system` | Sistema de paletas por setor ou posicionamento | Fintech — Trust Blue |
| `industry` | Perfil de uma indústria — convenções visuais, copy, tom | Setor jurídico |
| `competitor` | Análise de concorrente — posicionamento, forças, fraquezas | Notion como competidor |
| `framework` | Modelo mental ou metodologia reutilizável | Jobs-to-be-done para copy |

**Regra:** Um arquivo = um tipo. Se um site tem elementos de motion relevantes,
crie uma referência `motion` separada apontando para ele — não misture.

---

## 2. Categories — Onde uma referência VIVE

A category define o caminho no repositório. Formato: `pasta/subpasta`.

```
sites/saas
sites/luxury
sites/webgl
sites/agencies

copy/                    ← arquivos de coleção de padrões

motion/gsap
motion/three-js
motion/framer
motion/vanilla
motion/reels
motion/transitions

visual/styles
visual/color-systems
visual/identities

industries/medical
industries/legal
industries/beauty
industries/local-services

competitors/
frameworks/
```

**Regra:** Novas categorias só são criadas quando pelo menos 3 referências
precisariam existir nela. Antes disso, use `notes` no arquivo mais próximo.

---

## 3. Maturity — O quanto CONFIAR

O campo `maturity` indica o nível de completude e confiabilidade.

| Valor | Significado | Quando usar |
|-------|-------------|-------------|
| `seed` | Entrada existe, campos mínimos preenchidos | Logo após captura |
| `growing` | Campos core preenchidos, ainda sendo enriquecido | Primeira semana |
| `stable` | Completo, revisado, confiável para uso em produção | Após validação |
| `outdated` | Dados desatualizados, precisa revisão | Quando site/copy muda significativamente |
| `deprecated` | Não é mais relevante, mantido só por histórico | Nunca deletar — marcar |

**Regra:** O MarketingOS só usa referências com `maturity: stable` por padrão.
Para exploração, pode usar `growing`. Nunca deve usar `outdated` ou `deprecated`
sem flag explícita no prompt.

**Revisão obrigatória:** Toda referência `stable` de site deve ser revisitada
em até 90 dias. Toda referência de copy, 180 dias.

---

## 4. Tags — Como ENCONTRAR

Tags são o vocabulário de busca. Três domínios obrigatoriamente representados:

### 4.1 Domínio visual/mood
Palavras que descrevem como algo parece e o que comunica.

```
dark | light | minimal | bold | editorial | technical | warm | cold
luxury | premium | accessible | brutalist | clean | maximalist
serif | sans-serif | monospace | typographic
```

### 4.2 Domínio funcional
O que o padrão faz, quando e onde é usado.

```
hero | landing | scroll | transition | hover | loading | modal
reveal | entrance | exit | loop | interactive | static
headline | body | cta | manifesto | hook | proof | offer
```

### 4.3 Domínio setorial
A que indústria ou tipo de produto se aplica.

```
saas | fintech | healthtech | legaltech | edtech | ecommerce
beauty | wellness | fashion | luxury | agency | consulting
b2b | b2c | enterprise | smb | consumer
```

### 4.4 Domínio técnico (para motion e sites)
```
gsap | three-js | webgl | css-only | canvas | rive | lottie
scroll-trigger | parallax | morphing | particles | stagger
```

**Regra:** Toda referência tem no mínimo 3 tags, de pelo menos 2 domínios diferentes.
Máximo recomendado: 10 tags. Acima disso, a referência está mal categorizada.

**Convenção:** Lowercase. Kebab-case para compostos. Sem artigos ou preposições.
Certo: `scroll-trigger`, `high-contrast`. Errado: `ScrollTrigger`, `com_contraste`.

---

## 5. Tensions — O que torna a referência INTERESSANTE

O campo `tensions` é o mais importante e o mais difícil.

**Não é uma descrição. Não é uma tag. É a paradoxo criativo.**

Uma tension captura o que uma referência comunica apesar de si mesma —
a contradição interna que a torna memorável.

### Exemplos corretos

| Referência | Tension |
|------------|---------|
| Linear | "precisão sem alarde" |
| Aesop | "luxury que não precisa dizer que é luxury" |
| Stripe | "confiança por subtração, não por adição" |
| Vercel | "velocidade como estética, não como feature" |
| Glossier | "produto que parece comunidade" |
| Harvey (AI jurídica) | "ruptura vestida de conservadorismo" |

### Exemplos incorretos

| Tentativa | Por que está errada |
|-----------|---------------------|
| "site minimalista escuro" | É uma descrição, não uma tension |
| "bom design" | Não diz nada acionável |
| "usa tipografia serif" | É uma observação, não um paradoxo |

### Como escrever uma tension

1. Identifique o que o objeto comunica
2. Identifique o que normalmente comunicaria esse mesmo resultado
3. Encontre onde os dois divergem
4. Escreva a divergência em menos de 8 palavras

**Regra:** Toda referência tem entre 1 e 3 tensions.
O MarketingOS usa tensions para inferir posicionamento e tom antes de ler o arquivo completo.

---

## 6. Source — De onde VEIO

| Campo | Quando usar |
|-------|-------------|
| `source_url` | Quando a referência tem uma URL verificável |
| `source_context` | Quando não tem URL — ex: análise de identidade off-line, brief de cliente, observação direta |

**Regra:** Toda referência precisa de pelo menos um dos dois.
Nenhuma referência entra no repo sem rastreabilidade de origem.

`source_url` deve ser a URL exata visitada — não a home se a referência veio de uma página específica.

---

## 7. Timestamps — Quando FOI e quando MUDA

| Campo | Formato | Significado |
|-------|---------|-------------|
| `captured_at` | `YYYY-MM-DD` | Quando a referência foi observada pela primeira vez |
| `updated_at` | `YYYY-MM-DD` | Última vez que o conteúdo foi revisado |

**Regra:** `updated_at` deve ser atualizado toda vez que qualquer campo substantivo muda.
Não atualizar só por corrigir typo.

---

## 8. Regras gerais do repositório

1. **Schema antes de conteúdo.** Nenhuma entrada sem validar contra `schema.json`.
2. **Uma referência, um arquivo.** Não agregar referências distintas em um único JSON.
   Exceção: `copy/` usa arquivos de coleção (múltiplos padrões por arquivo).
3. **Nunca deletar — deprecar.** Referências obsoletas ganham `maturity: deprecated`.
   O histórico tem valor para análise de tendência.
4. **Path é relativo à raiz do repo.** `sites/saas/linear.json`, não `./sites/saas/linear.json`.
5. **Competitors é categoria obrigatória.** Toda indústria atendida pelo MarketingOS
   deve ter pelo menos um concorrente mapeado.
6. **Sem vídeo bruto no git.** Motion/reels armazenam análise textual + link externo.
   Screenshots são aceitos se < 500KB.
7. **Index não é opcional.** Toda referência adicionada ao repo deve ter
   entrada correspondente em `index.json` no mesmo commit.
