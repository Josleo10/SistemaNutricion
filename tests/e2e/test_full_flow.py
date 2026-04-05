import pytest
from datetime import date, timedelta
from domain.entities import RegistroDiario
from domain.report import MacrosDia, EvaluacionNutricional, ReporteSemanal
from application.services import _calcular_estadisticas, _evaluar_nutricional, _generar_recomendaciones


class TestE2EFullFlow:
    """Simulación de uso básico del sistema completo."""

    def test_simulacion_semana_completa(self):
        registros = [
            RegistroDiario(date(2026, 3, 30), ["Huevo"], ["Arroz", "Lenteja", "Carne", "Ensalada rusa"], ["Pan", "Palta", "Manzanilla"], ["Pan", "Queso"]),
            RegistroDiario(date(2026, 3, 31), ["Huevo"], ["Arroz", "Frijol", "Pollo"], ["Pan", "Arroz", "Frijol", "Pollo", "Cafe"], []),
            RegistroDiario(date(2026, 4, 1), ["Huevo", "Pan", "Queso"], ["Arroz", "Pollo"], ["Tequeño", "Manzanilla"], []),
        ]

        stats = _calcular_estadisticas(registros)
        assert stats["dias_con_3_comidas"] == 3
        assert len(stats["dias_saltados"]) == 0
        assert stats["alimentos_unicos"] > 0

        evaluaciones = _evaluar_nutricional({"kcal": 1800, "proteina": 80, "grasa": 55, "carbos": 230})
        assert len(evaluaciones) == 4

        recs = _generar_recomendaciones(evaluaciones)
        assert isinstance(recs, list)

    def test_semana_con_dias_saltados(self):
        registros = [
            RegistroDiario(date(2026, 4, 1), ["Huevo"], [], ["Pan"], []),
            RegistroDiario(date(2026, 4, 2), [], ["Arroz"], [], []),
        ]

        stats = _calcular_estadisticas(registros)
        assert stats["dias_con_3_comidas"] == 0
        assert len(stats["dias_saltados"]) == 2

    def test_reporte_semanal_sin_datos(self):
        reporte = ReporteSemanal(
            fecha_inicio=date(2026, 4, 1),
            fecha_fin=date(2026, 4, 7),
            registros=[],
            totales={}, promedios={}, detalles_dia=[],
            estadisticas={}, evaluaciones=[], recomendaciones=[],
            estado_general="SIN DATOS",
        )
        assert reporte.estado_general == "SIN DATOS"
        assert len(reporte.registros) == 0

    def test_reporte_con_datos(self):
        registros = [
            RegistroDiario(date(2026, 4, 1), ["Huevo"], ["Arroz", "Pollo"], ["Pan"], []),
        ]
        stats = _calcular_estadisticas(registros)
        evaluaciones = _evaluar_nutricional({"kcal": 550, "proteina": 50, "grasa": 15, "carbos": 78})
        recs = _generar_recomendaciones(evaluaciones)

        estados = [e.estado for e in evaluaciones]
        estado_general = "OK" if all(s == "ok" for s in estados) else "AJUSTAR"

        assert estado_general == "AJUSTAR"
        assert len(recs) > 0
