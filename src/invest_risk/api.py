"""API HTTP do laboratório de risco."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from .db import connect, initialize, offering_by_slug, seed
from .risk import persist_assessment


class OfferingSummary(BaseModel):
    slug: str
    name: str
    asset_type: str
    status: str
    benchmark: str | None
    spread_annual: float | None


class AssessmentFinding(BaseModel):
    code: str
    title: str
    score_delta: int
    rationale: str


class AssessmentResponse(BaseModel):
    score: int | None
    risk_band: str
    confidence: str
    methodology_version: str
    findings: list[AssessmentFinding]


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize()
    seed()
    yield


app = FastAPI(
    title="Investment Risk Evaluation API",
    version="0.1.0",
    description="API didática para catalogar evidências e avaliar risco de CRIs/CRAs.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/offerings", response_model=list[OfferingSummary])
def list_offerings() -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT slug, name, asset_type, status, benchmark, spread_annual FROM offerings ORDER BY name"
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/offerings/{slug}")
def get_offering(slug: str) -> dict[str, Any]:
    with connect() as connection:
        offering = offering_by_slug(connection, slug)
        if offering is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oferta não encontrada")
        result = dict(offering)
        result["parties"] = [dict(row) for row in connection.execute(
            """SELECT i.legal_name, i.cnpj, p.role FROM offering_parties p
            JOIN issuers i ON i.id = p.issuer_id WHERE p.offering_id = ?""", (offering["id"],)
        )]
        result["guarantees"] = [dict(row) for row in connection.execute(
            "SELECT kind, description, registration_status FROM guarantees WHERE offering_id = ?", (offering["id"],)
        )]
        result["evidence"] = [dict(row) for row in connection.execute(
            "SELECT source_url, collected_at, excerpt FROM evidence WHERE offering_id = ?", (offering["id"],)
        )]
    return result


def latest_assessment_payload(slug: str, create: bool) -> AssessmentResponse:
    with connect() as connection:
        offering = offering_by_slug(connection, slug)
        if offering is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oferta não encontrada")
        if create:
            assessment_id = persist_assessment(connection, offering)
        else:
            row = connection.execute(
                "SELECT id FROM risk_assessments WHERE offering_id = ? ORDER BY id DESC LIMIT 1", (offering["id"],)
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avaliação ainda não gerada")
            assessment_id = row["id"]
        assessment = connection.execute("SELECT * FROM risk_assessments WHERE id = ?", (assessment_id,)).fetchone()
        findings = connection.execute(
            "SELECT code, title, score_delta, rationale FROM assessment_findings WHERE assessment_id = ? ORDER BY id", (assessment_id,)
        ).fetchall()
    return AssessmentResponse(
        score=assessment["score"], risk_band=assessment["risk_band"], confidence=assessment["confidence"],
        methodology_version=assessment["methodology_version"], findings=[dict(item) for item in findings],
    )


@app.post("/offerings/{slug}/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(slug: str) -> AssessmentResponse:
    return latest_assessment_payload(slug, create=True)


@app.get("/offerings/{slug}/assessments/latest", response_model=AssessmentResponse)
def get_latest_assessment(slug: str) -> AssessmentResponse:
    return latest_assessment_payload(slug, create=False)


# The user interface is intentionally static: FastAPI serves it, while JavaScript
# consumes the same JSON endpoints that any other client would use.
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIRECTORY = Path(__file__).parent / "static"
app.mount("/assets", StaticFiles(directory=STATIC_DIRECTORY), name="assets")


@app.get("/", include_in_schema=False)
def web_application() -> FileResponse:
    return FileResponse(STATIC_DIRECTORY / "index.html")


@app.get("/learning/overview")
def learning_overview() -> dict[str, Any]:
    def package_version(name: str) -> str:
        try:
            return version(name)
        except PackageNotFoundError:
            return "not installed"

    return {
        "database": {
            "explanation": "SQLite stores the facts, sources, guarantees and assessments separately so each conclusion remains traceable.",
            "tables": [
                {"name": "offerings", "purpose": "investment terms"},
                {"name": "guarantees", "purpose": "collateral and registration status"},
                {"name": "evidence", "purpose": "source URL and collection date"},
                {"name": "risk_assessments", "purpose": "historical results"},
                {"name": "assessment_findings", "purpose": "score explanation"},
            ],
            "example_query": "SELECT name, benchmark, spread_annual FROM offerings ORDER BY name",
        },
        "api": {
            "flow": ["browser", "FastAPI route", "risk rules", "SQLite", "JSON response"],
            "explanation": "The route validates the HTTP contract. The risk module calculates findings. The database layer persists and retrieves data.",
            "endpoints": [
                {"method": "GET", "path": "/offerings", "purpose": "list available offerings"},
                {"method": "GET", "path": "/offerings/{slug}", "purpose": "show offer, guarantees and sources"},
                {"method": "POST", "path": "/offerings/{slug}/assessments", "purpose": "calculate and save risk evaluation"},
            ],
        },
        "dependencies": [
            {"name": "fastapi", "version": package_version("fastapi"), "purpose": "HTTP routes, validation and interactive docs"},
            {"name": "uvicorn", "version": package_version("uvicorn"), "purpose": "development ASGI server"},
            {"name": "pydantic", "version": package_version("pydantic"), "purpose": "response schemas and validation"},
            {"name": "sqlite3", "version": "Python standard library", "purpose": "embedded relational database"},
        ],
    }
