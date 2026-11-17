"""Interface de linha de comando para o laboratório."""

from __future__ import annotations

import argparse

from .db import connect, initialize, offering_by_slug, seed
from .risk import persist_assessment


def command_assess() -> None:
    with connect() as connection:
        offerings = connection.execute("SELECT * FROM offerings ORDER BY name").fetchall()
        for offering in offerings:
            assessment_id = persist_assessment(connection, offering)
            assessment = connection.execute(
                "SELECT score, risk_band, confidence FROM risk_assessments WHERE id = ?", (assessment_id,)
            ).fetchone()
            print(f"{offering['slug']}: score={assessment['score']} faixa={assessment['risk_band']} confiança={assessment['confidence']}")


def command_report(slug: str) -> None:
    with connect() as connection:
        offering = offering_by_slug(connection, slug)
        if offering is None:
            raise SystemExit(f"Oferta não encontrada: {slug}")
        assessment = connection.execute(
            "SELECT * FROM risk_assessments WHERE offering_id = ? ORDER BY id DESC LIMIT 1", (offering["id"],)
        ).fetchone()
        if assessment is None:
            raise SystemExit("Execute 'assess' antes de gerar o relatório.")
        print(f"\n{offering['name']} ({offering['asset_type']})")
        print(f"Observado em: {offering['observed_at']} | Taxa: {offering['benchmark']} + {offering['spread_annual']}% a.a.")
        print(f"Score: {assessment['score']} | Faixa: {assessment['risk_band']} | Confiança: {assessment['confidence']}")
        print("\nAchados:")
        findings = connection.execute(
            "SELECT * FROM assessment_findings WHERE assessment_id = ? ORDER BY id", (assessment["id"],)
        ).fetchall()
        for item in findings:
            sign = "+" if item["score_delta"] > 0 else ""
            print(f"- [{sign}{item['score_delta']}] {item['title']}: {item['rationale']}")
        print("\nEvidências:")
        for item in connection.execute("SELECT * FROM evidence WHERE offering_id = ?", (offering["id"],)):
            print(f"- {item['collected_at']} — {item['source_url']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Laboratório de risco de investimentos")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Cria as tabelas SQLite")
    commands.add_parser("seed", help="Carrega os dados iniciais")
    commands.add_parser("assess", help="Executa as regras de risco")
    report = commands.add_parser("report", help="Exibe relatório de uma oferta")
    report.add_argument("slug")
    args = parser.parse_args()
    if args.command == "init":
        initialize()
        print("Banco inicializado em data/investment_risk.db")
    elif args.command == "seed":
        print(f"{seed()} ofertas carregadas.")
    elif args.command == "assess":
        command_assess()
    elif args.command == "report":
        command_report(args.slug)


if __name__ == "__main__":
    main()
