"""
Backup semanal de PostgreSQL.
Guarda dumps en backups/ y mantiene solo los ultimos 4.
Uso: python backup.py
"""
import os
import sys
import subprocess
from datetime import datetime

if getattr(sys, 'frozen', False):
    _ROOT = os.path.dirname(sys.executable)
else:
    _ROOT = os.path.dirname(os.path.abspath(__file__))

BACKUP_DIR = os.path.join(_ROOT, "backups")
MAX_BACKUPS = 4

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "BDP-Nutrición"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "Leonard0"),
}


def crear_backup() -> str:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"backup_{fecha}.sql"
    filepath = os.path.join(BACKUP_DIR, filename)

    env = os.environ.copy()
    env["PGPASSWORD"] = DB_CONFIG["password"]

    cmd = [
        "pg_dump",
        "-h", DB_CONFIG["host"],
        "-p", str(DB_CONFIG["port"]),
        "-U", DB_CONFIG["user"],
        "-d", DB_CONFIG["dbname"],
        "-F", "p",
        "-f", filepath,
    ]

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed: {result.stderr}")

    return filepath


def limpiar_viejos():
    if not os.path.exists(BACKUP_DIR):
        return
    archivos = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_") and f.endswith(".sql")],
        reverse=True,
    )
    for viejo in archivos[MAX_BACKUPS:]:
        ruta = os.path.join(BACKUP_DIR, viejo)
        os.remove(ruta)
        print(f"  Eliminado: {viejo}")


if __name__ == "__main__":
    print("=== Backup PostgreSQL ===")
    try:
        ruta = crear_backup()
        tamano = os.path.getsize(ruta)
        print(f"  Backup creado: {os.path.basename(ruta)} ({tamano / 1024:.1f} KB)")
        limpiar_viejos()
        print("  Backup completado exitosamente.")
    except FileNotFoundError:
        print("  ERROR: pg_dump no encontrado. Asegurate de que PostgreSQL/bin este en PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"  ERROR: {e}")
        sys.exit(1)
