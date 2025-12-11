# tests/test_classifier.py
"""
Tests de la función clasificadora (refactorizado)
"""

import pytest

from app.classifier import (
    classify_risk,
)


@pytest.fixture
def base_metrics():
    # valores por defecto que son "OK"
    return {
        "error_rate": 0.005,
        "latency_p95": 220,
        "throughput": 1200,
    }


def test_classify_risk_ok(base_metrics):
    """Métricas normales -> OK"""
    status, reasons = classify_risk(base_metrics)
    assert status == "OK"
    assert len(reasons) == 1
    assert "aceptables" in reasons[0].lower()


@pytest.mark.parametrize(
    "override, expected_substr",
    [
        ({"error_rate": 0.05}, "error rate"),
        ({"latency_p95": 500}, "latencia"),
        ({"throughput": 500}, "throughput"),
    ],
)
def test_classify_risk_single_problem(base_metrics, override, expected_substr):
    """
    Casos con un único problema -> RIESGOSO
    """
    metrics = {**base_metrics, **override}
    status, reasons = classify_risk(metrics)
    assert status == "RIESGOSO"
    # esperamos exactamente 1 razón en estos casos
    assert len(reasons) == 1
    assert expected_substr in reasons[0].lower()


def test_classify_risk_multiple_problems():
    """Múltiples problemas -> RIESGOSO con varias razones"""
    metrics = {
        "error_rate": 0.05,
        "latency_p95": 500,
        "throughput": 500,
    }
    status, reasons = classify_risk(metrics)
    assert status == "RIESGOSO"
    # verificar que hay 3 razones y que cada tipo aparece
    assert len(reasons) == 3
    joined = " ".join(r.lower() for r in reasons)
    assert "error rate" in joined
    assert "latencia" in joined
    assert "throughput" in joined
