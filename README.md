# Investment Risk Lab

Um MVP didático para catalogar operações de crédito estruturado e produzir uma
avaliação de risco **explicável**. O recorte inicial é CRI/CRA disponibilizado
publicamente pela INCO; a arquitetura permite adicionar CDB, ações, ETFs e
imóveis mais adiante.

> Este projeto organiza evidências e apoia análise. Ele não é recomendação de
> investimento, não prevê inadimplência e não substitui a leitura dos documentos
> da oferta.

## Comece aqui

```powershell
python -m src.invest_risk.cli init
python -m src.invest_risk.cli seed
python -m src.invest_risk.cli assess
python -m src.invest_risk.cli report honu-habitat
```

Os comandos criam `data/investment_risk.db`, um arquivo SQLite local. Não há
servidor, conta ou dependência externa no MVP.

## O que cada comando faz

| Comando | Efeito |
| --- | --- |
| `init` | cria as tabelas vazias no banco SQLite |
| `seed` | carrega a fotografia pública inicial das ofertas da INCO |
| `assess` | aplica as regras explicáveis de risco às ofertas com dados suficientes |
| `report <slug>` | mostra a avaliação, evidências e lacunas de dados de uma oferta |

## Documentação

- [Arquitetura e decisões](docs/architecture.md)
- [Modelo de dados](docs/data-model.md)
- [Como estudar o projeto por etapas](docs/learning-path.md)
- [Fontes e limites dos dados iniciais](docs/data-sources.md)

## Estrutura

```text
data/                 dados de entrada versionados e banco local gerado
docs/                 decisões e material didático
src/invest_risk/      código da aplicação
tests/                testes automatizados
```

## API FastAPI

A aplicação também expõe uma API REST com FastAPI. Inicie:

```powershell
.\.venv\Scripts\uvicorn.exe src.invest_risk.api:app --reload
```

Acesse http://127.0.0.1:8000/docs para testar as rotas. Veja a arquitetura em docs/api-architecture.md.
