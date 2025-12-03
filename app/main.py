from fastapi import FastAPI, HTTPException

from app.classifier import classify_risk
from app.models import create_release

app = FastAPI(title="Release Radar API", version="0.1.0")

releases_db = {}


@app.get("/")
def read_root():
    return {"message": "Release Radar API en funcionamiento. Visita /docs"}


@app.get("/health")
def health_check():
    from datetime import datetime

    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/releases")
def create_release_endpoint(release: dict):
    """
    Crea un release. Body esperado:
    {
        "version": "v1.0.0",
        "commit": "abc123",
        "metrics": {"error_rate": 0.005, "latency_p95": 220, "throughput": 1200}
    }
    """
    version = release.get("version")
    if not version:
        raise HTTPException(status_code=400, detail="Se requiere el campo 'version'")

    if version in releases_db:
        raise HTTPException(status_code=409, detail=f"El release {version} ya existe")

    new_release = create_release(
        version=version,
        commit=release.get("commit", "unknown"),
        metrics=release.get("metrics"),
    )

    if new_release["metrics"]:
        status, _ = classify_risk(new_release["metrics"])
        new_release["status"] = status

    releases_db[version] = new_release
    return new_release


@app.get("/releases")
def list_releases():
    releases = list(releases_db.values())
    releases.sort(key=lambda r: r["timestamp"], reverse=True)
    return releases


@app.get("/releases/{version}")
def get_release(version: str):
    if version not in releases_db:
        raise HTTPException(status_code=404, detail=f"Release {version} no encontrado")
    return releases_db[version]


@app.get("/analysis/{version}")
def analyze_release(version: str):
    if version not in releases_db:
        raise HTTPException(status_code=404, detail=f"Release {version} no encontrado")

    release = releases_db[version]

    if not release["metrics"]:
        return {
            "version": version,
            "status": "DESCONOCIDO",
            "metrics": None,
            "reasons": ["No hay métricas disponibles"],
        }

    status, reasons = classify_risk(release["metrics"])
    return {
        "version": version,
        "status": status,
        "metrics": release["metrics"],
        "reasons": reasons,
    }
