import pytest
from domain.calculator import obtener_macros, calcular_calorias_comida, calcular_macros_comida


class TestObtenerMacros:
    def test_alimento_en_referencia(self):
        ref = {"Huevo": {"proteina": 13, "grasa": 11, "carbos": 1.1, "kcal": 155}}
        resultado = obtener_macros("Huevo", ref)
        assert resultado["kcal"] == 155
        assert resultado["proteina"] == 13

    def test_alimento_con_mapeo(self):
        ref = {"Huevo": {"proteina": 13, "grasa": 11, "carbos": 1.1, "kcal": 155}}
        resultado = obtener_macros("huevo", ref)
        assert resultado["kcal"] == 155

    def test_alimento_no_encontrado(self):
        ref = {}
        resultado = obtener_macros("AlimentoInexistente", ref)
        assert resultado["proteina"] is None
        assert resultado["kcal"] is None


class TestCalcularCaloriasComida:
    def test_lista_vacia(self):
        assert calcular_calorias_comida([], {}) == 0

    def test_un_alimento(self):
        ref = {"Huevo": {"kcal": 155}}
        assert calcular_calorias_comida(["Huevo"], ref) == 155

    def test_varios_alimentos(self):
        ref = {"Huevo": {"kcal": 155}, "Pan": {"kcal": 265}}
        assert calcular_calorias_comida(["Huevo", "Pan"], ref) == 420

    def test_alimento_sin_kcal(self):
        ref = {"Agua": {"kcal": None}}
        assert calcular_calorias_comida(["Agua"], ref) == 0


class TestCalcularMacrosComida:
    def test_lista_vacia(self):
        esperado = {"proteina": 0, "grasa": 0, "carbos": 0, "kcal": 0}
        assert calcular_macros_comida([], {}) == esperado

    def test_un_alimento_completo(self):
        ref = {"Huevo": {"proteina": 13, "grasa": 11, "carbos": 1.1, "kcal": 155}}
        resultado = calcular_macros_comida(["Huevo"], ref)
        assert resultado["proteina"] == 13
        assert resultado["grasa"] == 11
        assert resultado["carbos"] == 1.1
        assert resultado["kcal"] == 155

    def test_acumulacion(self):
        ref = {
            "Huevo": {"proteina": 13, "grasa": 11, "carbos": 1.1, "kcal": 155},
            "Pan": {"proteina": 9, "grasa": 3.2, "carbos": 49, "kcal": 265},
        }
        resultado = calcular_macros_comida(["Huevo", "Pan"], ref)
        assert resultado["proteina"] == 22
        assert resultado["grasa"] == 14.2
        assert resultado["carbos"] == 50.1
        assert resultado["kcal"] == 420
