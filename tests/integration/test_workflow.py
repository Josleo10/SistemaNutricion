import pytest
from datetime import date
from domain.calculator import calcular_macros_comida
from domain.normalizer import obtener_nombre_referencia, separar_alimentos
from domain.entities import RegistroDiario
from config import METAS_DIARIAS


class TestFlujoRegistroComida:
    """Prueba el flujo completo de normalización -> cálculo de macros."""

    def test_registro_comida_completo(self):
        referencia = {
            "Huevo": {"proteina": 13, "grasa": 11, "carbos": 1.1, "kcal": 155},
            "Pan": {"proteina": 9, "grasa": 3.2, "carbos": 49, "kcal": 265},
            "Arroz": {"proteina": 2.7, "grasa": 0.3, "carbos": 28, "kcal": 130},
            "Pollo": {"proteina": 31, "grasa": 3.6, "carbos": 0, "kcal": 165},
        }

        registro = RegistroDiario(
            fecha=date(2026, 4, 1),
            desayuno=["Huevo", "Pan"],
            almuerzo=["Arroz", "Pollo"],
            cena=["Pan"],
            extras=["Galleta"],
        )

        assert registro.tiene_tres_comidas() is True
        assert registro.comidas_faltantes() == []

        macros_desayuno = calcular_macros_comida(registro.desayuno, referencia)
        assert macros_desayuno["kcal"] == 420
        assert macros_desayuno["proteina"] == 22

        macros_almuerzo = calcular_macros_comida(registro.almuerzo, referencia)
        assert macros_almuerzo["kcal"] == 295

        macros_cena = calcular_macros_comida(registro.cena, referencia)
        assert macros_cena["kcal"] == 265

        total_kcal = macros_desayuno["kcal"] + macros_almuerzo["kcal"] + macros_cena["kcal"]
        assert total_kcal == 980

    def test_registro_con_alimentos_no_mapeados(self):
        referencia = {"Huevo": {"kcal": 155}}
        registro = RegistroDiario(
            fecha=date(2026, 4, 1),
            desayuno=["huevo"],
            almuerzo=["Arroz"],
            cena=["Pan"],
            extras=[],
        )
        macros = calcular_macros_comida(registro.desayuno, referencia)
        assert macros["kcal"] == 155

    def test_separar_y_mapear(self):
        texto = "huevo/pan/arroz"
        alimentos = separar_alimentos(texto)
        assert len(alimentos) == 3
        assert obtener_nombre_referencia(alimentos[0]) == "Huevo"


class TestGeneracionReporte:
    """Prueba la generación de reporte con datos simulados."""

    def test_evaluacion_nutricional(self):
        from application.services import _evaluar_nutricional

        promedios = {"kcal": 2200, "proteina": 75, "grasa": 60, "carbos": 250}
        evaluaciones = _evaluar_nutricional(promedios)

        assert len(evaluaciones) == 4
        for ev in evaluaciones:
            assert ev.estado == "ok"

    def test_evaluacion_fuera_de_rango(self):
        from application.services import _evaluar_nutricional

        promedios = {"kcal": 1500, "proteina": 30, "grasa": 90, "carbos": 200}
        evaluaciones = _evaluar_nutricional(promedios)

        kcal_eval = [e for e in evaluaciones if e.metrica == "kcal"][0]
        assert kcal_eval.estado == "bajo"

        grasa_eval = [e for e in evaluaciones if e.metrica == "grasa"][0]
        assert grasa_eval.estado == "alto"

    def test_generar_recomendaciones(self):
        from application.services import _generar_recomendaciones
        from domain.report import EvaluacionNutricional

        evaluaciones = [
            EvaluacionNutricional("kcal", "bajo", "Calorias bajas"),
            EvaluacionNutricional("proteina", "ok", "Proteina suficiente"),
            EvaluacionNutricional("grasa", "alto", "Grasa elevada"),
        ]
        recs = _generar_recomendaciones(evaluaciones)
        assert "Aumentar consumo calorico" in recs
        assert "Reducir consumo de grasas" in recs
        assert len(recs) == 2

    def test_estadisticas(self):
        from application.services import _calcular_estadisticas

        registros = [
            RegistroDiario(date(2026, 4, 1), ["Huevo"], ["Arroz", "Pollo"], ["Pan"], []),
            RegistroDiario(date(2026, 4, 2), ["Huevo"], ["Arroz"], [], []),
            RegistroDiario(date(2026, 4, 3), [], ["Pollo"], ["Pan"], ["Galleta"]),
        ]
        stats = _calcular_estadisticas(registros)
        assert stats["dias_con_3_comidas"] == 1
        assert stats["alimentos_unicos"] == 5
        assert len(stats["dias_saltados"]) == 2
        assert stats["top5"][0][0] in ["Huevo", "Arroz", "Pollo", "Pan"]
