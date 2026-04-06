import unicodedata
from typing import Optional, Callable


def quitar_acentos(texto: str) -> str:
    texto = texto.replace("ñ", "\x00").replace("Ñ", "\x01")
    nfkd = unicodedata.normalize("NFKD", texto)
    resultado = []
    for c in nfkd:
        if unicodedata.combining(c):
            continue
        resultado.append(c)
    texto = "".join(resultado)
    texto = texto.replace("\x00", "ñ").replace("\x01", "Ñ")
    return texto.lower()


def normalizar_nombre(nombre: str) -> Optional[str]:
    if nombre is None:
        return None
    nombre = str(nombre).strip()
    nombre = quitar_acentos(nombre)
    return nombre


MAPEO_NOMBRES = {}


def obtener_nombre_referencia(nombre_original: str, resolver: Optional[Callable] = None) -> Optional[str]:
    if nombre_original is None:
        return None
    nombre_norm = normalizar_nombre(nombre_original)
    if nombre_norm is None:
        return None
    if resolver is not None:
        canonico = resolver(nombre_original)
        if canonico is not None:
            return canonico
    if nombre_norm in MAPEO_NOMBRES:
        return MAPEO_NOMBRES[nombre_norm]
    return str(nombre_original).strip().title()


def separar_alimentos(texto: str) -> list[str]:
    if texto is None or str(texto).strip() == "":
        return []
    return [a.strip() for a in str(texto).split("/") if a.strip()]
