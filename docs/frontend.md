# Front-end: modo Regular e Didático

## Objetivo

A mesma tela atende dois objetivos distintos:

| Modo | Para quem | Mostra |
| --- | --- | --- |
| Regular | quem quer avaliar uma oferta | taxa, garantias, evidências e score |
| Didática | quem quer aprender o sistema | dados, rotas, dependências e regras aplicadas |

O botão no topo não muda os dados nem o cálculo. Ele muda apenas a profundidade
da explicação apresentada ao usuário.

## Escolha técnica: HTML, CSS e JavaScript sem framework

Os arquivos em `src/invest_risk/static/` são servidos pelo próprio FastAPI. Isso
elimina uma segunda aplicação, ferramentas de build e dependências de Node neste
primeiro momento. A separação ainda existe:

```text
Browser (app.js) --fetch JSON--> FastAPI --SQLite--> dados
```

`app.js` nunca consulta SQLite diretamente. Ele usa as rotas HTTP como faria um
front-end React, Vue ou mobile. Por isso, substituir esta interface por outro
cliente no futuro não exige alterar as regras de risco.

## Abas do modo Didático

- **Por que este score?** Mostra os achados salvos para a avaliação e o impacto
  de cada regra no score.
- **Base de dados:** mostra as tabelas relevantes e uma consulta SQL de exemplo.
- **Processo FastAPI:** mostra o caminho de uma requisição e os contratos HTTP.
- **Dependências:** consulta as versões em execução de FastAPI, Uvicorn e
  Pydantic, além de explicar a biblioteca SQLite.

Os metadados técnicos são fornecidos por `GET /learning/overview`. Isso evita
duplicar fatos de arquitetura no JavaScript e torna essa documentação utilizável
por outros clientes.
