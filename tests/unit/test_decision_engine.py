import pytest
from datetime import date
from application.services import obtener_reporte_semanal, _evaluar_nutricional, _generar_recomendaciones
from domain.report import EvaluacionNutricional


class TestAnalisisSemanal:
    def test_evaluacion_dentro_rango(self):
        promedios = {"kcal": 2200, "proteina": 75, "grasa": 60, "carbos": 250}
        evaluaciones = _evaluar_nutricional(promedios)
        assert all(e.estado == "ok" for e in evaluaciones)

    def test_evaluacion_fuera_rango(self):
        promedios = {"kcal": 1500, "proteina": 30, "grasa": 90, "carbos": 200}
        evaluaciones = _evaluar_nutricional(promedios)
        kcal_eval = [e for e in evaluaciones if e.metrica == "kcal"][0]
        assert kcal_eval.estado == "bajo"

    def test_recomendaciones(self):
        evaluaciones = [
            EvaluacionNutricional("kcal", "bajo", "Calorias bajas"),
            EvaluacionNutricional("proteina", "ok", "Proteina suficiente"),
        ]
        recs = _generar_recomendaciones(evaluaciones)
        assert "Aumentar consumo calorico" in recs
        assert len(recs) == 1
