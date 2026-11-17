# Roteiro de aprendizado

## Etapa 1 — banco de dados

Execute os comandos do README e abra `data/investment_risk.db` em um visualizador
SQLite, como DB Browser for SQLite ou a extensão SQLite do VS Code. Observe as
tabelas e tente esta consulta:

```sql
SELECT o.name, o.asset_type, o.benchmark, o.spread_annual,
       i.legal_name, p.role
FROM offerings o
LEFT JOIN offering_parties p ON p.offering_id = o.id
LEFT JOIN issuers i ON i.id = p.issuer_id;
```

Ela mostra por que relacionamos tabelas: uma mesma oferta retorna várias partes,
sem repetir todos os dados da oferta em cada linha.

## Etapa 2 — risco explicável

Leia `src/invest_risk/risk.py`. Cada regra retorna um achado com impacto positivo
ou negativo. O total é limitado entre 0 e 100 e acompanhado por confiança, que
depende da completude de campos críticos.

## Etapa 3 — novas fontes

Para incluir uma oferta, não edite o banco diretamente. Primeiro acrescente os
dados e a evidência em `data/inco_offers.json`; depois execute `seed` e `assess`.
Essa sequência protege a origem dos dados e torna o resultado reproduzível.

## Etapa 4 — quando usar ML

ML exige uma pergunta mensurável e histórico rotulado: por exemplo, "houve atraso
superior a 30 dias nos 12 meses seguintes?". Sem isso, um modelo aprende ruído.
O banco criado agora será o registro necessário para chegar a essa etapa.
