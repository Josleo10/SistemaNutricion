from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Comida:
    tipo: str  # desayuno, almuerzo, cena, extras
    alimentos: list[str]

    def __post_init__(self):
        self.tipo = self.tipo.lower()


@dataclass
class RegistroDiario:
    fecha: date
    desayuno: list[str]
    almuerzo: list[str]
    cena: list[str]
    extras: list[str]

    def todas_las_comidas(self) -> list[Comida]:
        return [
            Comida("desayuno", self.desayuno),
            Comida("almuerzo", self.almuerzo),
            Comida("cena", self.cena),
            Comida("extras", self.extras),
        ]

    def comidas_con_nombres(self) -> list[tuple[str, list[str]]]:
        return [
            ("Desayuno", self.desayuno),
            ("Almuerzo", self.almuerzo),
            ("Cena", self.cena),
            ("Extras", self.extras),
        ]

    def todos_los_alimentos(self) -> list[str]:
        return self.desayuno + self.almuerzo + self.cena + self.extras

    def tiene_tres_comidas(self) -> bool:
        return bool(self.desayuno) and bool(self.almuerzo) and bool(self.cena)

    def comidas_faltantes(self) -> list[str]:
        faltantes = []
        if not self.desayuno:
            faltantes.append("Desayuno")
        if not self.almuerzo:
            faltantes.append("Almuerzo")
        if not self.cena:
            faltantes.append("Cena")
        return faltantes
