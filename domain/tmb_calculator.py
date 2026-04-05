def calcular_tmb(peso_kg: float, altura_cm: float, edad: int, sexo: str) -> float:
    tmb = (10 * peso_kg) + (6.25 * altura_cm) - (5 * edad)
    tmb += 5 if sexo == "hombre" else -161
    return round(tmb)


def calcular_get(tmb: float, nivel_actividad: str, niveles: dict) -> tuple:
    factor = niveles.get(nivel_actividad, {}).get("factor", 1.2)
    get = round(tmb * factor)
    return get, factor
