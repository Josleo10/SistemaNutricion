"""
Backup semanal de PostgreSQL.
Guarda dumps en Backups/ y mantiene solo los ultimos 4.
Uso: python backup.py
"""
import os
import sys
import subprocess
from datetime import datetime

BACKUP_DIR = None
MAX_BACKUPS = 4

POSTGRESQL_PATHS = [
    r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe",
    r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
    r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
    r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
    r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe",
    r"C:\Program Files\PostgreSQL\13\bin\pg_dump.exe",
    r"C:\Program Files\PostgreSQL\12\bin\pg_dump.exe",
    r"C:\Program Files (x86)\PostgreSQL\18\bin\pg_dump.exe",
    r"C:\Program Files (x86)\PostgreSQL\17\bin\pg_dump.exe",
    r"C:\Program Files (x86)\PostgreSQL\16\bin\pg_dump.exe",
    r"C:\Program Files (x86)\PostgreSQL\15\bin\pg_dump.exe",
    r"C:\Program Files (x86)\PostgreSQL\14\bin\pg_dump.exe",
    r"C:\Program Files (x86)\PostgreSQL\13\bin\pg_dump.exe",
]

def encontrar_pg_dump():
    for path in POSTGRESQL_PATHS:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("pg_dump no encontrado en las rutas comunes de PostgreSQL")


def get_db_config():
    config = {}
    
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()
    
    possible_paths = [
        os.path.join(exe_dir, ".env"),
        os.path.join(cwd, ".env"),
        os.path.join(os.path.dirname(__file__), ".env"),
    ]
    
    env_path = None
    for path in possible_paths:
        try:
            if os.path.exists(path):
                env_path = path
                break
        except:
            pass
    
    if env_path:
        with open(env_path, "rb") as f:
            content = f.read()
        for line in content.split(b"\n"):
            line = line.decode("utf-8", errors="ignore").strip()
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    
    dbname = config.get("DB_NAME", "")
    if not dbname:
        dbname = "BDP-Nutrición"
    if "Nutri" in dbname and "Ã" in dbname:
        dbname = dbname.replace("Ã³", "ó")
    
    host = config.get("DB_HOST", "")
    port = config.get("DB_PORT", "")
    user = config.get("DB_USER", "")
    password = config.get("DB_PASSWORD", "")
    
    if not host:
        host = "localhost"
    if not port:
        port = "5432"
    if not user:
        user = "postgres"
    
    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
    }


def crear_backup() -> str:
    DB_CONFIG = get_db_config()
    _create_backup_dir()
    
    fecha = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"backup_{fecha}.sql"
    filepath = os.path.join(BACKUP_DIR, filename)

    pg_dump_path = encontrar_pg_dump()

    env = os.environ.copy()
    env["PGPASSWORD"] = DB_CONFIG["password"]
    env["PGCLIENTENCODING"] = "UTF8"
    env["PGDATABASE"] = "BDP-Nutrición"
    env["PGHOST"] = "127.0.0.1" if DB_CONFIG["host"] == "localhost" else DB_CONFIG["host"]
    env["PGPORT"] = str(DB_CONFIG["port"])
    env["PGUSER"] = DB_CONFIG["user"]

    cmd = [
        pg_dump_path,
        "-h", env["PGHOST"],
        "-p", env["PGPORT"],
        "-U", env["PGUSER"],
        "-d", "postgres",
        "-F", "p",
        "-f", filepath,
    ]

    result = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")

    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed: {result.stderr}")

    return filepath


def _create_backup_dir():
    """Create backup directory if it doesn't exist"""
    global BACKUP_DIR
    if BACKUP_DIR is None:
        if getattr(sys, 'frozen', False):
            _root = os.path.dirname(sys.executable)
        else:
            _root = os.path.dirname(os.path.abspath(__file__))
        BACKUP_DIR = os.path.join(_root, "Backups")
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    return BACKUP_DIR


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
    except FileNotFoundError as e:
        print(f"  ERROR: {e}")
        print("  Asegurate de tener PostgreSQL instalado.")
        sys.exit(1)
    except Exception as e:
        print(f"  ERROR: {e}")
        sys.exit(1)