# Arquitetura da API

## Por que uma API?

Uma API é uma porta de entrada padronizada para o sistema. Em vez de uma tela ou
comando acessar o banco diretamente, clientes fazem requisições HTTP. Isso nos
permite criar uma interface web, aplicativo ou automação sem reescrever as
regras de risco.

```text
Cliente (Swagger, web ou app)
             |
             | HTTP / JSON
             v
       Rotas FastAPI (api.py)
             |
             v
    serviço de domínio (risk.py)
             |
             v
      repositório SQLite (db.py)
```

## Responsabilidades

| Camada | Responsabilidade | Não deve fazer |
| --- | --- | --- |
| `api.py` | valida entrada HTTP e define respostas JSON | conter SQL ou fórmula de risco |
| `risk.py` | calcular e explicar a avaliação | saber sobre HTTP |
| `db.py` | criar conexões e persistir dados | decidir o risco financeiro |

FastAPI gera automaticamente uma interface interativa em `/docs`; ela serve
como documentação executável e é a melhor forma de aprender/testar os contratos
no início.
