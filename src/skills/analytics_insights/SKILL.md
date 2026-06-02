# Skill: Analytics Insights

## Função
Processar métricas de publicações e extrair insights acionáveis para guiar
as próximas criações.

## Inputs
- `metrics` (list): lista de publicações com suas métricas
  - `post_id`, `platform`, `impressions`, `reach`, `likes`, `comments`, `shares`, `clicks`, `saves`
- `period` (str): período de análise

## Outputs
- `top_posts` (list): posts com melhor desempenho e por que
- `worst_posts` (list): posts com pior desempenho e por que
- `patterns` (dict): padrões identificados (horário, formato, tom, tema)
- `recommendations` (list): ações concretas para melhorar performance
- `engagement_rate_avg` (float): taxa média de engajamento

## Fórmulas
- Engagement Rate = (likes + comments + shares + saves) / reach * 100
- Click Rate = clicks / impressions * 100
- Virality Score = shares / reach * 100
