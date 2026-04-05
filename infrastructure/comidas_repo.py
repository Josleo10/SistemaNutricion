import psycopg2
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
