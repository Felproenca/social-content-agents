# Skill: Platform Formatter

## Função
Adaptar um copy genérico para as regras, limites e estilo de cada plataforma.

## Inputs
- `copy` (str): texto base a formatar
- `platform` (str): plataforma destino
- `include_emojis` (bool): adicionar emojis
- `include_hashtags` (bool): adicionar hashtags ao final

## Outputs
- `formatted_copy` (str): texto formatado e pronto para publicar
- `char_count` (int): contagem de caracteres
- `within_limits` (bool): se está dentro dos limites da plataforma

## Limites por plataforma
| Plataforma | Caracteres | Hashtags recomendados |
|------------|-----------|----------------------|
| LinkedIn   | 3000      | 3-5                  |
| Instagram  | 2200      | 5-30                 |
| TikTok     | 2200      | 3-5                  |
| X/Twitter  | 280       | 1-2                  |
| YouTube    | 5000 (desc) | 3-5               |
