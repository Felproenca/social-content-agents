# Skill: Viral Hook Generator

## Função
Gerar a primeira linha/frase de impacto que força o usuário a parar o scroll
e consumir o conteúdo.

## Inputs
- `topic` (str): assunto do conteúdo
- `platform` (str): plataforma (influencia o estilo do gancho)
- `hook_type` (str): curiosity | pain | controversy | data | story | challenge
- `audience` (str): quem vai ler

## Outputs
- `hooks` (list[str]): 5 variações de gancho
- `best_hook` (str): gancho recomendado
- `hook_type_used` (str): tipo de gancho da melhor opção

## Fórmulas de gancho
- **Curiosidade**: "O que 97% dos [profissão] não sabem sobre [tema]"
- **Dor**: "Se você [situação ruim], este post é para você"
- **Dado**: "[Número]% das empresas falham em [tema]. Aqui está o porquê."
- **Controvérsia**: "Pare de [conselho popular]. Faça isso em vez disso."
- **História**: "Em [ano], eu [situação difícil]. Hoje [resultado}"
- **Desafio**: "Me desafio a [meta]. Acompanhe."
