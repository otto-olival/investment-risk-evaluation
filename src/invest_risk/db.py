"""PersistÃƒÂªncia SQLite. Mantida isolada para que regras nÃƒÂ£o dependam de SQL."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "investment_risk.db"
SEED_FILE = PROJECT_ROOT / "data" / "inco_offers.json"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS offerings (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL CHECK(asset_type IN ('CRI', 'CRA', 'CDB')),
    platform TEXT NOT NULL,
    status TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    benchmark TEXT,
    spread_annual REAL,
    term_months INTEGER,
    payment_structure TEXT
);

CREATE TABLE IF NOT EXISTS issuers (
    id INTEGER PRIMARY KEY,
    legal_name TEXT NOT NULL UNIQUE,
    cnpj TEXT
);

CREATE TABLE IF NOT EXISTS offering_parties (
    offering_id INTEGER NOT NULL REFERENCES offerings(id) ON DELETE CASCADE,
    issuer_id INTEGER NOT NULL REFERENCES issuers(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    PRIMARY KEY (offering_id, issuer_id, role)
);

CREATE TABLE IF NOT EXISTS guarantees (
    id INTEGER PRIMARY KEY,
    offering_id INTEGER NOT NULL REFERENCES offerings(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    description TEXT NOT NULL,
    registration_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY,
    offering_id INTEGER NOT NULL REFERENCES offerings(id) ON DELETE CASCADE,
    source_url TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    excerpt TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id INTEGER PRIMARY KEY,
    offering_id INTEGER NOT NULL REFERENCES offerings(id) ON DELETE CASCADE,
    assessed_at TEXT NOT NULL,
    methodology_version TEXT NOT NULL,
    score INTEGER,
    risk_band TEXT NOT NULL,
    confidence TEXT NOT NULL,
    status TEXT NOT NULL,
    UNIQUE(offering_id, methodology_version, assessed_at)
);

CREATE TABLE IF NOT EXISTS assessment_findings (
    id INTEGER PRIMARY KEY,
    assessment_id INTEGER NOT NULL REFERENCES risk_assessments(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    score_delta INTEGER NOT NULL,
    rationale TEXT NOT NULL
);
"""


def connect(database: Path = DEFAULT_DATABASE) -> sqlite3.Connection:
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(database: Path = DEFAULT_DATABASE) -> None:
    with connect(database) as connection:
        connection.executescript(SCHEMA)


def seed(database: Path = DEFAULT_DATABASE, source: Path = SEED_FILE) -> int:
    """Carrega a fotografia de ofertas. Reexecutar atualiza a mesma oferta pelo slug."""
    initialize(database)
    records: list[dict[str, Any]] = json.loads(source.read_text(encoding="utf-8"))
    with connect(database) as connection:
        for record in records:
            connection.execute(
                """INSERT INTO offerings
                (slug, name, asset_type, platform, status, observed_at, benchmark,
                 spread_annual, term_months, payment_structure)
                VALUES (:slug, :name, :asset_type, :platform, :status, :observed_at,
                        :benchmark, :spread_annual, :term_months, :payment_structure)
                ON CONFLICT(slug) DO UPDATE SET
                    name=excluded.name, asset_type=excluded.asset_type,
                    platform=excluded.platform, status=excluded.status,
                    observed_at=excluded.observed_at, benchmark=excluded.benchmark,
                    spread_annual=excluded.spread_annual, term_months=excluded.term_months,
                    payment_structure=excluded.payment_structure""",
                record,
            )
            offering_id = connection.execute(
                "SELECT id FROM offerings WHERE slug = ?", (record["slug"],)
            ).fetchone()["id"]
            for table in ("offering_parties", "guarantees", "evidence"):
                connection.execute(f"DELETE FROM {table} WHERE offering_id = ?", (offering_id,))
            for party in record["parties"]:
                connection.execute(
                    "INSERT INTO issuers (legal_name) VALUES (?) ON CONFLICT(legal_name) DO NOTHING",
                    (party["legal_name"],),
                )
                issuer_id = connection.execute(
                    "SELECT id FROM issuers WHERE legal_name = ?", (party["legal_name"],)
                ).fetchone()["id"]
                connection.execute(
                    "INSERT INTO offering_parties (offering_id, issuer_id, role) VALUES (?, ?, ?)",
                    (offering_id, issuer_id, party["role"]),
                )
            for guarantee in record["guarantees"]:
                connection.execute(
                    """INSERT INTO guarantees (offering_id, kind, description, registration_status)
                    VALUES (?, :kind, :description, :registration_status)""",
                    (offering_id, guarantee["kind"], guarantee["description"], guarantee["registration_status"]),
                )
            for item in record["evidence"]:
                connection.execute(
                    """INSERT INTO evidence (offering_id, source_url, collected_at, excerpt)
                    VALUES (?, :source_url, :collected_at, :excerpt)""",
                    (offering_id, item["source_url"], item["collected_at"], item["excerpt"]),
                )
    return len(records)


def offering_by_slug(connection: sqlite3.Connection, slug: str) -> sqlite3.Row | None:
    return connection.execute("SELECT * FROM offerings WHERE slug = ?", (slug,)).fetchone()
