from datetime import date, timedelta
from collections import Counter
from config import METAS_DIARIAS, DIAS_SEMANA, NIVELES_ACTIVIDAD
from domain.normalizer import obtener_nombre_referencia
from domain.calculator import calcular_macros_comida, calcular_calorias_comida
from domain.entities import RegistroDiario
from domain.report import MacrosDia, EvaluacionNutricional, ReporteSemanal
from infrastructure.excel_repo import leer_comidas_excel, leer_dia_excel, leer_alimentos_referencia, guardar_comidas_excel
from infrastructure.comidas_repo import guardar_comidas as pg_guardar_comidas
from infrastructure.user_repo import crear_tabla_usuario, actualizar_usuario, obtener_datos_usuario


def registrar_comida(fecha: date, desayuno: str | None, almuerzo: str | None,
                     cena: str | None, extras: str | None, referencia: dict) -> dict:
    """Guarda las comidas en Excel y PostgreSQL. Retorna status."""
    guardar_comidas_excel(fecha, desayuno, almuerzo, cena, extras)

    registros_pg = []
    for tipo_comida, alimentos_str in [("desayuno", desayuno), ("almuerzo", almuerzo),
                                        ("cena", cena), ("extras", extras)]:
        if alimentos_str is None:
            continue
        alimentos = [a.strip() for a in alimentos_str.split("/") if a.strip()]
        for alim in alimentos:
            nombre_ref = obtener_nombre_referencia(alim)
            macros = referencia.get(nombre_ref, {}) if nombre_ref else {}
            registros_pg.append((
                fecha, tipo_comida, nombre_ref if nombre_ref else alim,
                100, macros.get("proteina"), macros.get("grasa"),
                macros.get("carbos"), macros.get("kcal"),
            ))

    num_pg = pg_guardar_comidas(registros_pg) if registros_pg else 0
    return {"excel": True, "postgresql": num_pg}


def obtener_reporte_semanal(fecha_inicio: date) -> ReporteSemanal:
    """Genera un reporte semanal completo desde Excel."""
    fecha_fin = fecha_inicio + timedelta(days=6)
    datos_raw = leer_comidas_excel(fecha_inicio, fecha_fin)
    referencia = leer_alimentos_referencia()

    if not datos_raw:
        return ReporteSemanal(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, registros=[],
            totales={}, promedios={}, detalles_dia=[], estadisticas={},
            evaluaciones=[], recomendaciones=[], estado_general="SIN DATOS",
        )

    registros = [
        RegistroDiario(
            fecha=d["fecha"], desayuno=d["desayuno"], almuerzo=d["almuerzo"],
            cena=d["cena"], extras=d["extras"],
        ) for d in datos_raw
    ]

    totales = {"kcal": 0, "proteina": 0, "grasa": 0, "carbos": 0}
    detalles_dia = []

    for dia in registros:
        macros_dia = {"kcal": 0, "proteina": 0, "grasa": 0, "carbos": 0}
        for _, alimentos in dia.comidas_con_nombres():
            m = calcular_macros_comida(alimentos, referencia)
            for k in macros_dia:
                macros_dia[k] += m.get(k, 0) or 0
        for k in totales:
            totales[k] += macros_dia[k]
        detalles_dia.append(MacrosDia(fecha=dia.fecha, **macros_dia))

    num_dias = len(registros)
    promedios = {k: v / num_dias for k, v in totales.items()}

    estadisticas = _calcular_estadisticas(registros)
    evaluaciones = _evaluar_nutricional(promedios)
    recomendaciones = _generar_recomendaciones(evaluaciones)
    estados = [e.estado for e in evaluaciones]
    estado_general = "OK" if all(s == "ok" for s in estados) else "AJUSTAR"

    return ReporteSemanal(
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, registros=registros,
        totales=totales, promedios=promedios, detalles_dia=detalles_dia,
        estadisticas=estadisticas, evaluaciones=evaluaciones,
        recomendaciones=recomendaciones, estado_general=estado_general,
    )


def _calcular_estadisticas(registros: list[RegistroDiario]) -> dict:
    dias_con_3 = sum(1 for r in registros if r.tiene_tres_comidas())
    dias_saltados = []
    for r in registros:
        faltantes = r.comidas_faltantes()
        if faltantes:
            nombre_dia = DIAS_SEMANA[r.fecha.weekday()]
            dias_saltados.append(f"{nombre_dia} {r.fecha}: falta {', '.join(faltantes)}")

    todos = []
    for r in registros:
        todos.extend(r.todos_los_alimentos())

    contador = Counter(todos)
    return {
        "dias_con_3_comidas": dias_con_3,
        "dias_saltados": dias_saltados,
        "alimentos_unicos": len(set(todos)),
        "top5": contador.most_common(5),
        "frecuencia": contador,
    }


def _evaluar_nutricional(promedios: dict) -> list[EvaluacionNutricional]:
    evaluaciones = []
    for nutriente, (minimo, maximo) in METAS_DIARIAS.items():
        valor = promedios.get(nutriente, 0)
        if nutriente == "kcal":
            if valor < minimo:
                evaluaciones.append(EvaluacionNutricional("kcal", "bajo", f"Calorias bajas. Necesitas aumentar ~{int(minimo - valor)} kcal/dia", valor, (minimo, maximo), minimo - valor))
            elif valor > maximo:
                evaluaciones.append(EvaluacionNutricional("kcal", "alto", f"Calorias altas. Necesitas reducir ~{int(valor - maximo)} kcal/dia", valor, (minimo, maximo), valor - maximo))
            else:
                evaluaciones.append(EvaluacionNutricional("kcal", "ok", "Calorias dentro del rango objetivo", valor, (minimo, maximo)))
        elif nutriente == "proteina":
            if valor < minimo:
                evaluaciones.append(EvaluacionNutricional("proteina", "bajo", f"Proteina baja. Aumentar ~{int(minimo - valor)}g diarios", valor, (minimo, maximo), minimo - valor))
            else:
                evaluaciones.append(EvaluacionNutricional("proteina", "ok", "Proteina suficiente", valor, (minimo, maximo)))
        elif nutriente == "grasa":
            if valor < minimo:
                evaluaciones.append(EvaluacionNutricional("grasa", "bajo", "Grasa baja. Considerar incrementar", valor, (minimo, maximo)))
            elif valor > maximo:
                evaluaciones.append(EvaluacionNutricional("grasa", "alto", "Grasa elevada. Reducir consumo", valor, (minimo, maximo)))
            else:
                evaluaciones.append(EvaluacionNutricional("grasa", "ok", "Grasa dentro del rango", valor, (minimo, maximo)))
        elif nutriente == "carbos":
            if valor < minimo:
                evaluaciones.append(EvaluacionNutricional("carbos", "bajo", "Carbohidratos bajos. Considerar incrementar", valor, (minimo, maximo)))
            elif valor > maximo:
                evaluaciones.append(EvaluacionNutricional("carbos", "alto", "Carbohidratos elevados. Reducir consumo", valor, (minimo, maximo)))
            else:
                evaluaciones.append(EvaluacionNutricional("carbos", "ok", "Carbohidratos dentro del rango", valor, (minimo, maximo)))
    return evaluaciones


def _generar_recomendaciones(evaluaciones: list[EvaluacionNutricional]) -> list[str]:
    recs = []
    for ev in evaluaciones:
        if ev.estado != "ok":
            if ev.metrica == "kcal":
                recs.append("Aumentar consumo calorico" if ev.estado == "bajo" else "Reducir consumo calorico")
            elif ev.metrica == "proteina":
                recs.append("Incorporar mas alimentos ricos en proteina")
            elif ev.metrica == "grasa":
                recs.append("Incrementar consumo de grasas saludables" if ev.estado == "bajo" else "Reducir consumo de grasas")
            elif ev.metrica == "carbos":
                recs.append("Incrementar carbohidratos" if ev.estado == "bajo" else "Reducir carbohidratos")
    return list(set(recs))


def analizar_semana(fecha_inicio: date) -> ReporteSemanal:
    """Analisis semanal con evaluaciones y recomendaciones."""
    return obtener_reporte_semanal(fecha_inicio)


def calcular_tmb_get(peso: float, altura: float, edad: int, sexo: str, nivel: str) -> dict:
    from domain.tmb_calculator import calcular_tmb, calcular_get
    tmb = calcular_tmb(peso, altura, edad, sexo)
    get, factor = calcular_get(tmb, nivel, NIVELES_ACTIVIDAD)
    return {"tmb": tmb, "get": get, "factor": factor}


def guardar_usuario(peso: float, altura: float, edad: int, sexo: str, nivel: str):
    crear_tabla_usuario()
    actualizar_usuario(peso, altura, edad, sexo, nivel)


def cargar_usuario() -> dict:
    try:
        return obtener_datos_usuario()
    except Exception:
        return {"peso_kg": None, "altura_cm": None, "edad": None, "sexo": None, "nivel_actividad": None}


def obtener_vista_previa_dia(fecha: date) -> dict:
    datos = leer_dia_excel(fecha)
    referencia = leer_alimentos_referencia()
    total_kcal = 0
    filas = []
    for comida, alimentos in [("Desayuno", datos["desayuno"]), ("Almuerzo", datos["almuerzo"]),
                               ("Cena", datos["cena"]), ("Extras", datos["extras"])]:
        if alimentos:
            kcal = calcular_calorias_comida(alimentos, referencia)
            total_kcal += kcal
            filas.append({"comida": comida, "alimentos": ", ".join(alimentos), "kcal": int(kcal)})
    return {"filas": filas, "total_kcal": int(total_kcal)}
