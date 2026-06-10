# Identidades de Clientes

Cada cliente tem seu próprio subdiretório com um arquivo `identity.json`.

## Como adicionar um cliente

```bash
mkdir references/identities/nome-do-cliente
cp references/identities/_schema.json references/identities/nome-do-cliente/identity.json
# edite o arquivo com as informações do cliente
```

## Estrutura

```
identities/
  _schema.json          ← template
  nome-do-cliente/
    identity.json       ← identidade completa
```

## Campos obrigatórios

| Campo | Descrição |
|-------|-----------|
| `client_slug` | Identificador único (kebab-case, ex: `acme-corp`) |
| `name` | Nome do cliente |
| `sector` | Setor (ex: `tech`, `finance`, `wellness`) |
| `palette` | 7 cores com hex |
| `typography.heading` | Fonte de título (Google Fonts) |
| `typography.body` | Fonte de corpo (Google Fonts) |
| `tone.voice` | Descrição do tom de voz em 1 frase |

## Como o MarketingOS usa

Ao receber um brief com `client_slug`, o MarketingOS:
1. Carrega `references/index.json` para localizar o arquivo
2. Lê `identity.json` do cliente
3. Usa `visual_style_ref` e `color_system_ref` para buscar as referências de estilo e cor correspondentes
4. Combina tudo para gerar conteúdo com identidade precisa
