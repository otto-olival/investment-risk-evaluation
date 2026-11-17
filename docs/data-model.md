# Modelo de dados

Um banco relacional armazena entidades em tabelas e conecta seus registros por
chaves. A chave primária (`id`) identifica uma linha; a chave estrangeira
(`offering_id`, por exemplo) aponta para uma linha de outra tabela.

```text
offerings 1---N offering_parties N---1 issuers
     |
     +---N guarantees
     +---N evidence
     +---N risk_assessments 1---N assessment_findings
```

## Tabelas

| Tabela | Guarda | Por quê |
| --- | --- | --- |
| `offerings` | título/oferta: tipo, taxa, prazo e fluxo | é o objeto central da análise |
| `issuers` | empresas ou pessoas vinculadas | a mesma empresa pode aparecer em mais de uma oferta |
| `offering_parties` | papel de cada parte (devedora, avalista etc.) | representa a relação muitos-para-muitos |
| `guarantees` | garantia e seu status de registro | garantias afetam recuperação em caso de problema |
| `evidence` | URL, trecho e data de coleta | permite verificar de onde veio cada fato |
| `risk_assessments` | resultado de uma execução das regras | preserva histórico de avaliações |
| `assessment_findings` | fatores, impacto e justificativa | explica como o resultado foi formado |

Uma fonte pode apoiar vários fatos. No MVP associamos a evidência à oferta para
manter o modelo simples; ao importar prospectos completos podemos ligá-la a
garantias e campos específicos.
