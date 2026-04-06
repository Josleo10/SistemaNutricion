"""
Migration script: Excel -> PostgreSQL
Reads ALIMENTOS sheet and MAPEO_NOMBRES, populates new tables in PostgreSQL.
Run once: python migrate_excel_to_pg.py
"""
import sys
import os

# Ensure project root is importable
if getattr(sys, 'frozen', False):
    _ROOT = os.path.dirname(sys.executable)
else:
    _ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import psycopg2
from config import DB_CONFIG
from domain.normalizer import MAPEO_NOMBRES


def conectar():
    return psycopg2.connect(**DB_CONFIG)


def crear_tablas():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS alimentos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL UNIQUE,
            tipo VARCHAR(50),
            proteina FLOAT,
            grasa FLOAT,
            carbos FLOAT,
            kcal FLOAT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS alimentos_alias (
            id SERIAL PRIMARY KEY,
            alias VARCHAR(100) NOT NULL UNIQUE,
            alimento_id INTEGER NOT NULL REFERENCES alimentos(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Tablas creadas: alimentos, alimentos_alias")


def migrar_alimentos_desde_excel(ruta_excel=None):
    """Lee la hoja ALIMENTOS del Excel y la inserta en PostgreSQL."""
    try:
        import openpyxl
    except ImportError:
        print("ERROR: openpyxl no instalado. Instalar con: pip install openpyxl")
        sys.exit(1)

    if ruta_excel is None:
        from config import get_ruta_excel
        ruta_excel = get_ruta_excel()
    if not os.path.exists(ruta_excel):
        print(f"ERROR: No se encontro el Excel en: {ruta_excel}")
        print(f"Uso: python migrate_excel_to_pg.py <ruta_al_excel>")
        sys.exit(1)

    wb = openpyxl.load_workbook(ruta_excel)
    ws = wb["ALIMENTOS"]
    wb.close()

    conn = conectar()
    cur = conn.cursor()

    insertados = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        nombre, tipo, proteina, grasa, carbos, kcal = row
        if nombre is None:
            continue
        nombre = str(nombre).strip()
        tipo_val = str(tipo).strip() if tipo else None
        prot = float(proteina) if proteina is not None else None
        gra = float(grasa) if grasa is not None else None
        car = float(carbos) if carbos is not None else None
        kal = float(kcal) if kcal is not None else None

        cur.execute("""
            INSERT INTO alimentos (nombre, tipo, proteina, grasa, carbos, kcal)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (nombre) DO UPDATE SET
                tipo = EXCLUDED.tipo,
                proteina = EXCLUDED.proteina,
                grasa = EXCLUDED.grasa,
                carbos = EXCLUDED.carbos,
                kcal = EXCLUDED.kcal
        """, (nombre, tipo_val, prot, gra, car, kal))
        insertados += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Alimentos migrados: {insertados}")


def migrar_mapeo_nombres():
    """Inserta MAPEO_NOMBRES como aliases en PostgreSQL."""
    conn = conectar()
    cur = conn.cursor()

    insertados = 0
    skipped = 0

    for alias, nombre_canonico in MAPEO_NOMBRES.items():
        alias_norm = alias.lower().strip()

        cur.execute("SELECT id FROM alimentos WHERE nombre = %s", (nombre_canonico,))
        row = cur.fetchone()

        if row is None:
            skipped += 1
            continue

        alimento_id = row[0]
        cur.execute("""
            INSERT INTO alimentos_alias (alias, alimento_id)
            VALUES (%s, %s)
            ON CONFLICT (alias) DO UPDATE SET alimento_id = EXCLUDED.alimento_id
        """, (alias_norm, alimento_id))
        insertados += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Aliases migrados: {insertados} (omitidos: {skipped} - alimento canonico no encontrado)")


def verificar():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM alimentos")
    count_alimentos = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM alimentos_alias")
    count_alias = cur.fetchone()[0]

    cur.close()
    conn.close()

    print(f"\nVerificacion:")
    print(f"  alimentos: {count_alimentos}")
    print(f"  alimentos_alias: {count_alias}")


if __name__ == "__main__":
    import sys
    ruta = sys.argv[1] if len(sys.argv) > 1 else None
    print("=== Migracion Excel -> PostgreSQL ===\n")
    crear_tablas()
    migrar_alimentos_desde_excel(ruta)
    migrar_mapeo_nombres()
    verificar()
    print("\nMigracion completada.")
