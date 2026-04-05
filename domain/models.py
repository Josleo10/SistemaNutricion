from dataclasses import dataclass
from typing import Optional


@dataclass
class Alimento:
    nombre: str
    tipo: Optional[str] = None
    proteina: Optional[float] = None
    grasa: Optional[float] = None
    carbos: Optional[float] = None
    kcal: Optional[float] = None

    def macros_por_gramos(self, gramos: float = 100) -> dict:
        factor = gramos / 100.0
        return {
            "proteina": (self.proteina or 0) * factor,
            "grasa": (self.grasa or 0) * factor,
            "carbos": (self.carbos or 0) * factor,
            "kcal": (self.kcal or 0) * factor,
        }
