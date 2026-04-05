import psycopg2
from config import DB_CONFIG


def conectar():
    return psycopg2.connect(**DB_CONFIG)


def crear_tabla_usuario():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id SERIAL PRIMARY KEY,
            peso_kg FLOAT,
            altura_cm FLOAT,
            edad INTEGER,
            sexo VARCHAR(10),
            nivel_actividad VARCHAR(20),
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def obtener_datos_usuario() -> dict:
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT peso_kg, altura_cm, edad, sexo, nivel_actividad FROM usuario LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {
            "peso_kg": row[0],
            "altura_cm": row[1],
            "edad": row[2],
            "sexo": row[3],
            "nivel_actividad": row[4],
        }
    return {"peso_kg": None, "altura_cm": None, "edad": None, "sexo": None, "nivel_actividad": None}


def actualizar_usuario(peso_kg: float, altura_cm: float, edad: int, sexo: str, nivel_actividad: str):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO usuario (peso_kg, altura_cm, edad, sexo, nivel_actividad)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            peso_kg = EXCLUDED.peso_kg,
            altura_cm = EXCLUDED.altura_cm,
            edad = EXCLUDED.edad,
            sexo = EXCLUDED.sexo,
            nivel_actividad = EXCLUDED.nivel_actividad,
            fecha_actualizacion = CURRENT_TIMESTAMP
    """, (peso_kg, altura_cm, edad, sexo, nivel_actividad))
    conn.commit()
    cur.close()
    conn.close()
