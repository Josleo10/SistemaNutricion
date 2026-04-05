import pytest
from datetime import date
from domain.entities import RegistroDiario, Comida
from domain.models import Alimento
from domain.usuario import Usuario


class TestRegistroDiario:
    def test_todas_las_comidas(self):
        r = RegistroDiario(date(2026, 4, 1), ["Huevo"], ["Arroz", "Pollo"], ["Pan"], ["Galleta"])
        comidas = r.todas_las_comidas()
        assert len(comidas) == 4
        assert comidas[0].tipo == "desayuno"
        assert comidas[1].tipo == "almuerzo"

    def test_tiene_tres_comidas_true(self):
        r = RegistroDiario(date(2026, 4, 1), ["Huevo"], ["Arroz"], ["Pan"], [])
        assert r.tiene_tres_comidas() is True

    def test_tiene_tres_comidas_false(self):
        r = RegistroDiario(date(2026, 4, 1), ["Huevo"], [], ["Pan"], [])
        assert r.tiene_tres_comidas() is False

    def test_comidas_faltantes(self):
        r = RegistroDiario(date(2026, 4, 1), ["Huevo"], [], [], [])
        assert r.comidas_faltantes() == ["Almuerzo", "Cena"]

    def test_todos_los_alimentos(self):
        r = RegistroDiario(date(2026, 4, 1), ["Huevo"], ["Arroz", "Pollo"], [], [])
        assert r.todos_los_alimentos() == ["Huevo", "Arroz", "Pollo"]


class TestAlimento:
    def test_macros_por_gramos_default(self):
        a = Alimento("Huevo", proteina=13, grasa=11, carbos=1.1, kcal=155)
        macros = a.macros_por_gramos()
        assert macros["proteina"] == 13
        assert macros["kcal"] == 155

    def test_macros_por_gramos_200(self):
        a = Alimento("Huevo", proteina=13, grasa=11, carbos=1.1, kcal=155)
        macros = a.macros_por_gramos(200)
        assert macros["proteina"] == 26
        assert macros["kcal"] == 310

    def test_macros_con_none(self):
        a = Alimento("Agua")
        macros = a.macros_por_gramos()
        assert macros["proteina"] == 0
        assert macros["kcal"] == 0


class TestUsuario:
    def test_datos_completos(self):
        u = Usuario(peso_kg=70, altura_cm=175, edad=30, sexo="hombre")
        assert u.tiene_datos_completos() is True

    def test_datos_incompletos(self):
        u = Usuario(peso_kg=70, altura_cm=175)
        assert u.tiene_datos_completos() is False

    def test_datos_vacios(self):
        u = Usuario()
        assert u.tiene_datos_completos() is False


class TestComida:
    def test_tipo_lower(self):
        c = Comida("DESAYUNO", ["Huevo"])
        assert c.tipo == "desayuno"
