from typing import Optional, Callable
from domain.normalizer import obtener_nombre_referencia, normalizar_nombre


def obtener_macros(alimento: str, referencia: dict, resolver: Optional[Callable] = None) -> dict:
    nombre_ref = obtener_nombre_referencia(alimento, resolver=resolver)
    if nombre_ref and nombre_ref in referencia:
        return referencia[nombre_ref]
    return {"tipo": None, "proteina": None, "grasa": None, "carbos": None, "kcal": None}


def calcular_calorias_comida(alimentos: list[str], referencia: dict, resolver: Optional[Callable] = None) -> float:
    total = 0
    for alim in alimentos:
        macros = obtener_macros(alim, referencia, resolver=resolver)
        if macros.get("kcal") is not None:
            total += macros["kcal"]
    return total


def calcular_macros_comida(alimentos: list[str], referencia: dict, resolver: Optional[Callable] = None) -> dict:
    total_p = total_g = total_c = total_k = 0
    for alim in alimentos:
        macros = obtener_macros(alim, referencia, resolver=resolver)
        if macros.get("proteina") is not None:
            total_p += macros["proteina"]
        if macros.get("grasa") is not None:
            total_g += macros["grasa"]
        if macros.get("carbos") is not None:
            total_c += macros["carbos"]
        if macros.get("kcal") is not None:
            total_k += macros["kcal"]
    return {"proteina": total_p, "grasa": total_g, "carbos": total_c, "kcal": total_k}
