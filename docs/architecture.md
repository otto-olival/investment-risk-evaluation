# Arquitetura e decisões

## Objetivo do MVP

Responder, com evidências: **quais riscos conhecidos uma operação possui e
quais informações ainda faltam para avaliá-la?** Isso é diferente de prometer
retorno ou estimar uma probabilidade precisa de default.

## Visão da solução

```text
Fonte pública / documento
        |
        v
Dados de entrada versionados (JSON) --> carga --> SQLite
                                                   |
                                                   v
                                          regras de risco explicáveis
                                                   |
                                                   v
                                      relatório + evidências + lacunas
```

Cada seta tem uma responsabilidade única. A fonte não é alterada; o JSON
preserva a fotografia que coletamos; o SQLite permite consultar relações; e as
regras transformam fatos em avaliação auditável.

## Decisões tomadas

| Decisão | Motivo | Consequência |
| --- | --- | --- |
| SQLite no MVP | É um banco relacional real, cabe em um arquivo e vem com Python. | Ótimo para aprender SQL; depois migraremos para PostgreSQL se houver usuários concorrentes. |
| Modelo relacional | Uma oferta pode ter muitos emissores, garantias e evidências. | Evita duplicar texto e torna consultas confiáveis. |
| Dados brutos em JSON versionado | Reprodutibilidade: a oferta pode mudar ou sair do ar. | Toda análise informa a data de coleta e URL da evidência. |
| Regras antes de ML | No início não temos rótulos suficientes de default. | O score é interpretável e as futuras observações poderão calibrá-lo. |
| Score separado de confiança | Pouca informação não deve parecer precisão. | Uma oferta pode ter risco alto e baixa confiança na conclusão. |

## Limites deliberados

O score não mede LTV, cobertura de serviço da dívida, rating ou probabilidade de
default enquanto os documentos não os fornecerem. Ausência de dado vira uma
lacuna explícita, nunca um valor inventado.

## Evolução planejada

1. Extrair campos de prospectos e demonstrações financeiras.
2. Inserir acompanhamento pós-emissão: pagamentos, atrasos, renegociações e
   vencimentos antecipados.
3. Incluir fontes externas por CNPJ (cadastro, processos, demonstrações e
   notícias), sempre guardando URL e data de consulta.
4. Quando houver histórico suficiente, comparar regras com modelos estatísticos
   calibrados e manter explicabilidade.
