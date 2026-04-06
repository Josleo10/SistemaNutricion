import psycopg2
from datetime import date
from config import DB_CONFIG


def conectar():
    return psycopg2.connect(**DB_CONFIG)


def crear_tabla_comidas():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comidas_detalle (
            id SERIAL PRIMARY KEY,
            fecha DATE NOT NULL,
            tipo_comida VARCHAR(20) NOT NULL,
            alimento VARCHAR(100) NOT NULL,
            gramos INTEGER DEFAULT 100,
            proteina FLOAT,
            grasa FLOAT,
            carbos FLOAT,
            kcal FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(fecha, tipo_comida, alimento)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def guardar_comidas(registros: list[tuple]) -> int:
    if not registros:
        return 0
    crear_tabla_comidas()
    conn = conectar()
    cur = conn.cursor()
    for reg in registros:
        cur.execute("""
            INSERT INTO comidas_detalle (fecha, tipo_comida, alimento, gramos, proteina, grasa, carbos, kcal)
            VALUES (%s, UPPER(%s), %s, %s, %s, %s, %s, %s)
            ON CONFLICT (fecha, tipo_comida, alimento) DO NOTHING
        """, reg)
    conn.commit()
    count = len(registros)
    cur.close()
    conn.close()
    return count


def obtener_datos_semana(fecha_inicio, fecha_fin) -> list[dict]:
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT fecha,
               SUM(kcal) as kcal,
               SUM(proteina) as proteina,
               SUM(grasa) as grasa,
               SUM(carbos) as carbos,
               COUNT(DISTINCT CASE WHEN tipo_comida = 'EXTRAS' THEN alimento END) as count_extras
        FROM comidas_detalle
        WHERE fecha BETWEEN %s AND %s
        GROUP BY fecha
        ORDER BY fecha
    """, (fecha_inicio, fecha_fin))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "fecha": r[0],
            "kcal": r[1] or 0,
            "proteina": r[2] or 0,
            "grasa": r[3] or 0,
            "carbos": r[4] or 0,
            "count_extras": r[5] or 0,
        }
        for r in rows
    ]


def obtener_comidas_semana(fecha_inicio, fecha_fin) -> list[dict]:
    """Returns meals grouped by date, same format as old leer_comidas_excel.
    Each dict: {fecha, desayuno:[], almuerzo:[], cena:[], extras:[]}"""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT fecha, tipo_comida, ARRAY_AGG(alimento ORDER BY id) as alimentos
        FROM comidas_detalle
        WHERE fecha BETWEEN %s AND %s
        GROUP BY fecha, tipo_comida
        ORDER BY fecha, tipo_comida
    """, (fecha_inicio, fecha_fin))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    from collections import defaultdict
    por_fecha = defaultdict(lambda: {"desayuno": [], "almuerzo": [], "cena": [], "extras": []})
    for fecha, tipo, alimentos in rows:
        key = fecha
        tipo_lower = tipo.lower()
        if tipo_lower in por_fecha[key]:
            por_fecha[key][tipo_lower].extend(alimentos)

    resultado = [
        {"fecha": fecha, **comidas}
        for fecha, comidas in sorted(por_fecha.items())
    ]
    return resultado


def obtener_comidas_dia(fecha) -> dict:
    """Returns meals for a single date, same format as old leer_dia_excel."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT tipo_comida, ARRAY_AGG(alimento ORDER BY id) as alimentos
        FROM comidas_detalle
        WHERE fecha = %s
        GROUP BY tipo_comida
    """, (fecha,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    resultado = {"desayuno": [], "almuerzo": [], "cena": [], "extras": []}
    for tipo, alimentos in rows:
        tipo_lower = tipo.lower()
        if tipo_lower in resultado:
            resultado[tipo_lower] = alimentos
    return resultado


def eliminar_comidas_dia(fecha: date):
    """Removes all meal entries for a given date (for re-save scenarios)."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM comidas_detalle WHERE fecha = %s", (fecha,))
    conn.commit()
    cur.close()
    conn.close()


def eliminar_comidas_por_tipo(fecha: date, tipos: list[str]):
    """Removes only specific meal types for a given date (partial update)."""
    if not tipos:
        return
    conn = conectar()
    cur = conn.cursor()
    placeholders = ", ".join(["%s"] * len(tipos))
    cur.execute(f"DELETE FROM comidas_detalle WHERE fecha = %s AND tipo_comida IN ({placeholders})",
                [fecha] + [t.upper() for t in tipos])
    conn.commit()
    cur.close()
    conn.close()
