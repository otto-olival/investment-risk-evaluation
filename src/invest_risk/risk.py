"""Metodologia v1: regras simples, deliberadamente visíveis e auditáveis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import sqlite3

METHODOLOGY_VERSION = "v1.0"


@dataclass(frozen=True)
class Finding:
    code: str
    title: str
    score_delta: int
    rationale: str


def assess_offering(connection: sqlite3.Connection, offering: sqlite3.Row) -> tuple[int | None, str, str, list[Finding]]:
    """Retorna score, faixa, confiança e achados. Score maior significa risco maior."""
    findings: list[Finding] = []
    required = [offering["term_months"], offering["payment_structure"]]
    guarantees = connection.execute(
        "SELECT * FROM guarantees WHERE offering_id = ?", (offering["id"],)
    ).fetchall()
    if any(value is None for value in required) or not guarantees:
        findings.append(Finding(
            "insufficient_data", "Dados críticos ausentes", 0,
            "Sem prazo, fluxo de pagamento e garantias documentados não é responsável produzir score.",
        ))
        return None, "não avaliado", "baixa", findings

    score = 50
    if offering["payment_structure"] == "monthly_interest_bullet_principal":
        findings.append(Finding(
            "bullet_principal", "Principal concentrado no vencimento", 15,
            "A amortização do principal ocorre no fim, deixando maior exposição de crédito durante o prazo.",
        ))
    if any(item["registration_status"] == "pending" for item in guarantees):
        findings.append(Finding(
            "guarantee_registration_pending", "Garantias com registro pendente", 20,
            "A eficácia e execução das garantias dependem da conclusão dos registros aplicáveis.",
        ))
    kinds = {item["kind"] for item in guarantees}
    if len(kinds) >= 3:
        findings.append(Finding(
            "guarantee_diversification", "Cesta diversificada de garantias", -10,
            "Há mais de três tipos de garantia; isso pode melhorar a recuperação, mas não elimina risco.",
        ))
    if "real_estate_fiduciary_assignment" in kinds:
        findings.append(Finding(
            "real_estate_collateral", "Garantia imobiliária fiduciária", -5,
            "Há garantia real imobiliária declarada, sujeita a valor, ônus e registro que ainda precisam ser verificados.",
        ))
    if "receivables_fiduciary_assignment" in kinds:
        findings.append(Finding(
            "receivables_collateral", "Cessão fiduciária de recebíveis", -3,
            "Os recebíveis podem apoiar o pagamento, mas exigem validação de concentração, adimplência e valor.",
        ))

    # A primeira captação é documentada pela oferta inicial e inserida como fato de origem.
    if offering["slug"] == "honu-habitat":
        findings.append(Finding(
            "first_platform_funding", "Primeira captação na plataforma", 10,
            "Não há histórico anterior da empresa na plataforma para confrontar execução e pagamentos.",
        ))

    score = max(0, min(100, score + sum(item.score_delta for item in findings)))
    band = "alto" if score >= 70 else "moderado" if score >= 40 else "baixo"
    return score, band, "baixa", findings


def persist_assessment(connection: sqlite3.Connection, offering: sqlite3.Row) -> int:
    score, band, confidence, findings = assess_offering(connection, offering)
    assessed_at = date.today().isoformat()
    connection.execute(
        "DELETE FROM risk_assessments WHERE offering_id = ? AND methodology_version = ? AND assessed_at = ?",
        (offering["id"], METHODOLOGY_VERSION, assessed_at),
    )
    cursor = connection.execute(
        """INSERT INTO risk_assessments
        (offering_id, assessed_at, methodology_version, score, risk_band, confidence, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (offering["id"], assessed_at, METHODOLOGY_VERSION, score, band, confidence, "completed"),
    )
    for finding in findings:
        connection.execute(
            """INSERT INTO assessment_findings
            (assessment_id, code, title, score_delta, rationale) VALUES (?, ?, ?, ?, ?)""",
            (cursor.lastrowid, finding.code, finding.title, finding.score_delta, finding.rationale),
        )
    return cursor.lastrowid
