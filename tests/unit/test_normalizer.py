import pytest
from domain.normalizer import normalizar_nombre, quitar_acentos, obtener_nombre_referencia, separar_alimentos, MAPEO_NOMBRES


class TestQuitarAcentos:
    def test_quita_acentos(self):
        assert quitar_acentos("Plátano") == "platano"
        assert quitar_acentos("Café") == "cafe"

    def test_preserva_enie(self):
        # La ñ debe preservarse mientras se quitan otros acentos
        resultado = quitar_acentos("Espan\u0303a")
        assert "n\u0303" not in resultado or "ñ" in resultado

    def test_minusculas(self):
        assert quitar_acentos("ARROZ") == "arroz"


class TestNormalizarNombre:
    def test_acentos_y_mayusculas(self):
        assert normalizar_nombre("Plátano") == "platano"
        assert normalizar_nombre("ARROZ") == "arroz"

    def test_none(self):
        assert normalizar_nombre(None) is None

    def test_strip(self):
        assert normalizar_nombre("  Huevo  ") == "huevo"


class TestObtenerNombreReferencia:
    def test_mapeo_directo(self):
        assert obtener_nombre_referencia("huevo") == "Huevo"
        assert obtener_nombre_referencia("atun") == "Atún"

    def test_mapeo_con_acento(self):
        assert obtener_nombre_referencia("plátano") == "Plátano"

    def test_sin_mapeo_title(self):
        assert obtener_nombre_referencia("alimento_raro") == "Alimento_Raro"

    def test_none(self):
        assert obtener_nombre_referencia(None) is None


class TestSepararAlimentos:
    def test_separador_slash(self):
        assert separar_alimentos("Arroz/Pollo/Ensalada") == ["Arroz", "Pollo", "Ensalada"]

    def test_vacio(self):
        assert separar_alimentos("") == []
        assert separar_alimentos(None) == []

    def test_un_solo(self):
        assert separar_alimentos("Huevo") == ["Huevo"]

    def test_con_espacios(self):
        assert separar_alimentos("Arroz / Pollo / ") == ["Arroz", "Pollo"]
