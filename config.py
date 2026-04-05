import os
import sys

_frozen = getattr(sys, 'frozen', False)

if not _frozen:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "BDP-Nutrición"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "Leonard0"),
}

METAS_DIARIAS = {
    "kcal": (2000, 2500),
    "proteina": (50, 100),
    "grasa": (44, 78),
    "carbos": (225, 325),
}

NIVELES_ACTIVIDAD = {
    "sedentario": {"factor": 1.2, "descripcion": "Poco ejercicio"},
    "ligero": {"factor": 1.375, "descripcion": "Ejercicio ligero 1-3 días/semana"},
    "moderado": {"factor": 1.55, "descripcion": "Ejercicio moderado 3-5 días/semana"},
    "muy_activo": {"factor": 1.725, "descripcion": "Ejercicio intenso 6-7 días/semana"},
    "extra_activo": {"factor": 1.9, "descripcion": "Ejercicio muy intenso/trabajo físico"},
}

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

_EXCEL_OVERRIDDEN = os.getenv("EXCEL_PATH")
_EXCEL_DEFAULT = r"C:\MIS DOCUMENTOS\IMPORTANTE\PROYECTOS\BD-Nutrición.xlsx"

def get_ruta_excel() -> str:
    if _EXCEL_OVERRIDDEN:
        return _EXCEL_OVERRIDDEN
    if _frozen:
        ruta = os.path.join(os.path.dirname(sys.executable), "BD-Nutricion.xlsx")
        if os.path.exists(ruta):
            return ruta
        if os.path.exists(_EXCEL_DEFAULT):
            return _EXCEL_DEFAULT
        return ruta
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "BD-Nutricion.xlsx")
