from dataclasses import dataclass
from typing import Optional


@dataclass
class Usuario:
    peso_kg: Optional[float] = None
    altura_cm: Optional[float] = None
    edad: Optional[int] = None
    sexo: Optional[str] = None
    nivel_actividad: Optional[str] = None

    def tiene_datos_completos(self) -> bool:
        return all([
            self.peso_kg is not None,
            self.altura_cm is not None,
            self.edad is not None,
            self.sexo is not None,
        ])
