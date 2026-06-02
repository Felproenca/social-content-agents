# Skill: Design Prompt Engineering

## Função
Gerar prompts detalhados e otimizados para ferramentas de geração de imagem por IA
(Midjourney, DALL-E 3, Flux, Stable Diffusion).

## Inputs
- `concept` (str): conceito visual principal
- `style` (str): photorealistic | illustration | 3d_render | flat_design | cinematic
- `platform` (str): define as dimensões (ex: instagram = 1:1, linkedin = 1.91:1)
- `mood` (str): sensação desejada (confiança, urgência, inspiração...)
- `brand_colors` (str): cores da marca em hex (opcional)

## Outputs
- `prompt_en` (str): prompt em inglês para o modelo de imagem
- `negative_prompt` (str): o que excluir
- `dimensions` (str): resolução recomendada
- `style_suffix` (str): sufixo de estilo para Midjourney (ex: --ar 16:9 --v 6)

## Boas práticas
- Prompts em inglês performam melhor em todos os modelos
- Especificar iluminação, composição e câmera aumenta qualidade
- Negative prompt elimina artefatos comuns (blur, text, watermark)
- Para Midjourney: adicionar referência de artista ou estilo
