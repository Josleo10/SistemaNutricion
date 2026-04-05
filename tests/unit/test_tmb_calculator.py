import pytest
from domain.tmb_calculator import calcular_tmb, calcular_get
from config import NIVELES_ACTIVIDAD


class TestCalcularTMB:
    def test_hombre(self):
        tmb = calcular_tmb(70, 175, 30, "hombre")
        assert tmb == round((10 * 70) + (6.25 * 175) - (5 * 30) + 5)

    def test_mujer(self):
        tmb = calcular_tmb(60, 165, 25, "mujer")
        assert tmb == round((10 * 60) + (6.25 * 165) - (5 * 25) - 161)

    def test_redondeo(self):
        tmb = calcular_tmb(70.5, 175.3, 30, "hombre")
        assert isinstance(tmb, int)


class TestCalcularGET:
    def test_sedentario(self):
        get, factor = calcular_get(1500, "sedentario", NIVELES_ACTIVIDAD)
        assert factor == 1.2
        assert get == round(1500 * 1.2)

    def test_moderado(self):
        get, factor = calcular_get(1500, "moderado", NIVELES_ACTIVIDAD)
        assert factor == 1.55
        assert get == round(1500 * 1.55)

    def test_nivel_desconocido_usa_default(self):
        get, factor = calcular_get(1500, "desconocido", NIVELES_ACTIVIDAD)
        assert factor == 1.2
        assert get == round(1500 * 1.2)
