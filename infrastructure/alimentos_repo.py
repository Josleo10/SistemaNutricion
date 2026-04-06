"""Repository for alimentos table (nutritional reference + alias lookup)."""
import psycopg2
from config import DB_CONFIG


def _conectar():
    return psycopg2.connect(**DB_CONFIG)


def crear_tablas():
    conn = _conectar()
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


def obtener_todos() -> dict:
    """Returns full reference dict keyed by nombre (same format as old leer_alimentos_referencia)."""
    conn = _conectar()
    cur = conn.cursor()
    cur.execute("SELECT nombre, tipo, proteina, grasa, carbos, kcal FROM alimentos ORDER BY nombre")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {
        r[0]: {"tipo": r[1], "proteina": r[2], "grasa": r[3], "carbos": r[4], "kcal": r[5]}
        for r in rows
    }


def buscar_por_nombre_o_alias(termino: str) -> dict | None:
    """Looks up food by canonical name or alias. Returns macros dict or None."""
    conn = _conectar()
    cur = conn.cursor()
    termino_lower = termino.strip().lower()

    cur.execute("""
        SELECT a.nombre, a.tipo, a.proteina, a.grasa, a.carbos, a.kcal
        FROM alimentos a
        WHERE LOWER(a.nombre) = %s
    """, (termino_lower,))
    row = cur.fetchone()

    if row is None:
        cur.execute("""
            SELECT a.nombre, a.tipo, a.proteina, a.grasa, a.carbos, a.kcal
            FROM alimentos_alias al
            JOIN alimentos a ON a.id = al.alimento_id
            WHERE LOWER(al.alias) = %s
        """, (termino_lower,))
        row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return {"nombre": row[0], "tipo": row[1], "proteina": row[2], "grasa": row[3], "carbos": row[4], "kcal": row[5]}
    return None


def buscar_todos(termino: str) -> list[dict]:
    """Search foods by name or alias (LIKE). Returns list of matching foods."""
    conn = _conectar()
    cur = conn.cursor()
    patron = f"%{termino.strip().lower()}%"

    cur.execute("""
        SELECT DISTINCT a.nombre, a.tipo, a.proteina, a.grasa, a.carbos, a.kcal
        FROM alimentos a
        LEFT JOIN alimentos_alias al ON al.alimento_id = a.id
        WHERE LOWER(a.nombre) LIKE %s OR LOWER(al.alias) LIKE %s
        ORDER BY a.nombre
    """, (patron, patron))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"nombre": r[0], "tipo": r[1], "proteina": r[2], "grasa": r[3], "carbos": r[4], "kcal": r[5]}
        for r in rows
    ]


def insertar_alimento(nombre: str, tipo: str = None, proteina: float = None,
                      grasa: float = None, carbos: float = None, kcal: float = None,
                      alias: list[str] = None) -> int:
    """Inserts a new food with optional aliases. Returns alimento id."""
    conn = _conectar()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO alimentos (nombre, tipo, proteina, grasa, carbos, kcal)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (nombre, tipo, proteina, grasa, carbos, kcal))
    alimento_id = cur.fetchone()[0]

    if alias:
        for a in alias:
            cur.execute("""
                INSERT INTO alimentos_alias (alias, alimento_id)
                VALUES (%s, %s)
                ON CONFLICT (alias) DO NOTHING
            """, (a.strip().lower(), alimento_id))

    conn.commit()
    cur.close()
    conn.close()
    return alimento_id


def actualizar_alimento(alimento_id: int, nombre: str = None, tipo: str = None,
                        proteina: float = None, grasa: float = None,
                        carbos: float = None, kcal: float = None):
    """Updates an existing food entry."""
    conn = _conectar()
    cur = conn.cursor()
    cur.execute("""
        UPDATE alimentos SET
            nombre = COALESCE(%s, nombre),
            tipo = COALESCE(%s, tipo),
            proteina = COALESCE(%s, proteina),
            grasa = COALESCE(%s, grasa),
            carbos = COALESCE(%s, carbos),
            kcal = COALESCE(%s, kcal)
        WHERE id = %s
    """, (nombre, tipo, proteina, grasa, carbos, kcal, alimento_id))
    conn.commit()
    cur.close()
    conn.close()


def eliminar_alimento(alimento_id: int):
    """Deletes a food and its aliases."""
    conn = _conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM alimentos WHERE id = %s", (alimento_id,))
    conn.commit()
    cur.close()
    conn.close()


def agregar_alias(alimento_id: int, alias: str):
    """Adds an alias to an existing food."""
    conn = _conectar()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO alimentos_alias (alias, alimento_id)
        VALUES (%s, %s)
        ON CONFLICT (alias) DO UPDATE SET alimento_id = EXCLUDED.alimento_id
    """, (alias.strip().lower(), alimento_id))
    conn.commit()
    cur.close()
    conn.close()


def obtener_alias(alimento_id: int) -> list[str]:
    """Returns list of aliases for a food."""
    conn = _conectar()
    cur = conn.cursor()
    cur.execute("SELECT alias FROM alimentos_alias WHERE alimento_id = %s ORDER BY alias", (alimento_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]


def obtener_todos_con_detalle() -> list[dict]:
    """Returns all foods with their aliases for display."""
    conn = _conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, a.nombre, a.tipo, a.proteina, a.grasa, a.carbos, a.kcal,
               ARRAY_AGG(al.alias ORDER BY al.alias) FILTER (WHERE al.alias IS NOT NULL) as alias_list
        FROM alimentos a
        LEFT JOIN alimentos_alias al ON al.alimento_id = a.id
        GROUP BY a.id, a.nombre, a.tipo, a.proteina, a.grasa, a.carbos, a.kcal
        ORDER BY a.nombre
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "id": r[0], "nombre": r[1], "tipo": r[2],
            "proteina": r[3], "grasa": r[4], "carbos": r[5], "kcal": r[6],
            "alias": r[7] or [],
        }
        for r in rows
    ]
