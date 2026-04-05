from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class MacrosDia:
    fecha: date
    proteina: float = 0.0
    grasa: float = 0.0
    carbos: float = 0.0
    kcal: float = 0.0


@dataclass
class EvaluacionNutricional:
    metrica: str
    estado: str  # ok, bajo, alto
    mensaje: str
    valor: float = 0.0
    rango: Optional[tuple] = None
    ajuste: Optional[float] = None


@dataclass
class ReporteSemanal:
    fecha_inicio: date
    fecha_fin: date
    registros: list  # list[RegistroDiario]
    totales: dict
    promedios: dict
    detalles_dia: list  # list[MacrosDia]
    estadisticas: dict
    evaluaciones: list  # list[EvaluacionNutricional]
    recomendaciones: list[str]
    estado_general: str
