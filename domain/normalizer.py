import unicodedata
from typing import Optional


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


MAPEO_NOMBRES = {
    "platano": "Plátano", "plátano": "Plátano",
    "platano frito": "Plátano", "plátano frito": "Plátano",
    "arandano": "Arándano", "arándano": "Arándano",
    "atun": "Atún", "atún": "Atún",
    "brocoli": "Brócoli", "brócoli": "Brócoli",
    "yogurt": "Yogur", "yogur": "Yogur",
    "anis": "Anís", "anís": "Anís",
    "limon": "Limón", "limón": "Limón",
    "pina": "Piña", "piña": "Piña",
    "maracuya": "Maracuyá", "maracuyá": "Maracuyá",
    "coliflor": "Coliflor", "espinaca": "Espinaca",
    "cebolla": "Cebolla", "zanahoria": "Zanahoria",
    "tomate": "Tomate", "aceituna": "Aceituna",
    "choclo": "Maíz (choclo)", "palta": "Palta",
    "manzana": "Manzana", "sandia": "Sandía", "sandía": "Sandía",
    "mango": "Mango", "papaya": "Papaya",
    "pitahaya": "Pitahaya", "kiwi": "Kiwi",
    "ciruela": "Ciruela", "huevo": "Huevo",
    "papa": "Papa", "arroz": "Arroz",
    "avena": "Avena", "pan": "Pan",
    "quinua": "Quinua", "pollo": "Pollo",
    "hamburguesa": "Hot dog", "queso": "Queso",
    "cafe": "Café", "café": "Café",
    "manzanilla": "Manzanilla", "helado": "Helado",
    "pizza": "Pizza", "galleta": "Galleta",
    "cuy": "Cuy", "coco": "Coco",
    "gaseosa": "Gaseosa", "camote": "Camote",
    "panqueque": "Pan", "panqueques": "Pan",
    "lenteja": "Lenteja", "lentejas": "Lenteja",
    "frejol": "Frijol", "frijol": "Frijol",
    "carne": "Carne de res", "chancho": "Cerdo",
    "chicharron": "Cerdo", "chicharrón": "Cerdo",
    "costilla": "Cerdo", "cecina": "Cecina",
    "higado": "Carne de res", "hígado": "Carne de res",
    "cereal trigo": "Trigo", "queque": "Pastel",
    "papa frita": "Papa", "papas al hilo": "Papa",
    "papa hilo": "Papa", "papa rellena": "Papa",
    "pure papa": "Papa", "puré papa": "Papa",
    "jugo": "Naranja", "jugo especial": "Naranja",
    "jugo fresa": "Fresa", "jugo naranja": "Naranja",
    "jugo papaya": "Papaya", "jugo platano": "Plátano",
    "jugo plátano": "Plátano", "limonada": "Limón",
    "aguadito": "Pollo", "aji de gallina": "Pollo",
    "ají de gallina": "Pollo", "aji de pescado": "Atún",
    "ají de pescado": "Atún", "broaster": "Pollo",
    "ceviche": "Atún", "chilcano": "Atún",
    "crema de verdura": "Zanahoria", "enchilada": "Huevo",
    "ensalada": "Lechuga", "ensalada rusa": "Papa",
    "espesado": "Cerdo", "estofado pollo": "Pollo",
    "guiso": "Cerdo", "hotdog": "Hot dog", "hot dog": "Hot dog",
    "huevo sancochado": "Huevo", "humita": "Maíz (choclo)",
    "lasaña": "Carne de res", "lazana": "Carne de res",
    "lazaña": "Carne de res", "lasana": "Carne de res",
    "menestra": "Frijol", "nuggets": "Pollo",
    "pan pizza": "Pizza", "pepian": "Pollo", "pepián": "Pollo",
    "pollo a la brasa": "Pollo", "pollo broaster": "Pollo",
    "sopa": "Arroz", "sopa de mote": "Maíz (choclo)",
    "tallarines": "Trigo", "tortilla": "Huevo",
    "torta": "Pastel", "tequeños": "Queso",
    "tequenos": "Queso",
    "7 semillas": "Almendra", "almohaditas": "Avena",
    "granola": "Avena", "cereal": "Avena",
    "flan": "Leche", "gelatina": "Miel",
    "kefir": "Leche", "marciano": "Helado",
    "plat": "Plátano", "plata": "Plátano",
    "arandano": "Fresa", "arándano": "Fresa",
    "coliflor": "Brócoli", "kiwi": "Fresa",
    "pitahaya": "Papaya", "arroz chaufa": "Arroz",
    "arroz amarillo": "Arroz", "churro": "Pastel",
    "pescado": "Atún", "toston": "Plátano", "tostón": "Plátano",
}


def obtener_nombre_referencia(nombre_original: str) -> Optional[str]:
    nombre_norm = normalizar_nombre(nombre_original)
    if nombre_norm is None:
        return None
    if nombre_norm in MAPEO_NOMBRES:
        return MAPEO_NOMBRES[nombre_norm]
    return str(nombre_original).strip().title()


def separar_alimentos(texto: str) -> list[str]:
    if texto is None or str(texto).strip() == "":
        return []
    return [a.strip() for a in str(texto).split("/") if a.strip()]
