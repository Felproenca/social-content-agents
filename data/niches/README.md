# data/niches/

Perfis de nicho descobertos automaticamente pelo `NicheDiscoverySkill`.

## Como funciona

Quando o sistema recebe um nicho pela primeira vez:
1. `NicheDiscoverySkill.discover(nicho)` verifica se `[slug].json` existe aqui
2. Se não existe: chama o LLM com o `RESEARCH_PROMPT` e salva o resultado
3. Se existe: carrega direto, sem chamar o LLM novamente
4. `PerformanceAgent.process_and_learn()` atualiza o perfil com métricas reais

## Estrutura de um perfil

```json
{
  "nicho": "Nome do nicho",
  "slug": "nome-do-nicho",
  "descricao": "...",
  "audiencia_primaria": "...",
  "audiencia_secundaria": "...",
  "linguagem": {
    "usa": ["termos de especialista"],
    "evita": ["clichês do setor"],
    "tom": "...",
    "nivel_tecnico": "..."
  },
  "temas_evergreen": [],
  "temas_trend": [],
  "angulos_inexplorados": [],
  "cliches_a_evitar": [],
  "referencias_setor": [],
  "posicoes_editoriais": [],
  "gatilhos_emocionais": {},
  "formato_por_plataforma": {},
  "source": "descoberto",
  "updated_at": "2026-...",
  "performance_data": {
    "best_angles": []
  }
}
```

## Importante

- Os arquivos `.json` são gerados em runtime e **não devem ser commitados**
- Para forçar redescoberta: delete o `.json` correspondente
- Para editar manualmente: mude `"source": "manual"` no arquivo
