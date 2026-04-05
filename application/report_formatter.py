from config import METAS_DIARIAS, DIAS_SEMANA
from domain.report import ReporteSemanal


def formatear_reporte(reporte: ReporteSemanal) -> str:
    if reporte.estado_general == "SIN DATOS":
        return "No se encontraron datos para el período seleccionado."

    lineas = []
    lineas.append("=" * 60)
    lineas.append("  REPORTE ALIMENTACIÓN SEMANAL")
    lineas.append(f"  Período: {reporte.fecha_inicio} al {reporte.fecha_fin}")
    lineas.append("=" * 60)

    lineas.append("")
    lineas.append("--- RESUMEN POR DÍA ---")

    for dia in reporte.registros:
        nombre_dia = DIAS_SEMANA[dia.fecha.weekday()]
        lineas.append("")
        lineas.append(f"[{nombre_dia} {dia.fecha}]")

        for comida, alimentos in dia.comidas_con_nombres():
            if alimentos:
                from domain.calculator import calcular_macros_comida
                from infrastructure.excel_repo import leer_alimentos_referencia
                ref = leer_alimentos_referencia()
                macros = calcular_macros_comida(alimentos, ref)
                kcal_str = f"{int(macros['kcal'])} kcal" if macros['kcal'] > 0 else ""
                lineas.append(f"  {comida:10}: {', '.join(alimentos)}  {kcal_str}")
            else:
                lineas.append(f"  {comida:10}: (ninguno)")

        macros_dia = None
        for d in reporte.detalles_dia:
            if d.fecha == dia.fecha:
                macros_dia = d
                break
        if macros_dia:
            lineas.append(f"  Total día : {int(macros_dia.kcal)} kcal | P:{int(macros_dia.proteina)}g | G:{int(macros_dia.grasa)}g | C:{int(macros_dia.carbos)}g")

    lineas.append("")
    lineas.append("-" * 60)
    lineas.append("--- ESTADÍSTICAS SEMANALES ---")
    lineas.append("")
    lineas.append(f"  Días con 3 comidas: {reporte.estadisticas['dias_con_3_comidas']}/7")

    if reporte.estadisticas["dias_saltados"]:
        lineas.append("  Días con comidas saltadas:")
        for s in reporte.estadisticas["dias_saltados"]:
            lineas.append(f"    - {s}")
    else:
        lineas.append("  No se saltó ninguna comida.")

    lineas.append(f"  Variedad de alimentos: {reporte.estadisticas['alimentos_unicos']} únicos")

    lineas.append("")
    lineas.append("-" * 60)
    lineas.append("--- TOP 5 ALIMENTOS ---")
    lineas.append("")
    for i, (alim, freq) in enumerate(reporte.estadisticas["top5"], 1):
        lineas.append(f"  {i}. {alim} ({freq} veces)")

    lineas.append("")
    lineas.append("-" * 60)
    lineas.append("--- RESUMEN NUTRICIONAL SEMANAL ---")
    lineas.append("")
    lineas.append("  Promedio diario:")

    prom = reporte.promedios
    for nutriente, meta in METAS_DIARIAS.items():
        valor = prom.get(nutriente, 0)
        minimo, maximo = meta
        unidad = "kcal" if nutriente == "kcal" else "g"
        ok = "✓" if minimo <= valor <= maximo else "✗"
        nombre = nutriente.capitalize().ljust(12)
        lineas.append(f"    {nombre}: {int(valor):>5} {unidad}  (meta: {minimo}-{maximo})  {ok}")

    lineas.append("")
    lineas.append("  Detalle por día:")
    for d in reporte.detalles_dia:
        nombre_dia = DIAS_SEMANA[d.fecha.weekday()]
        min_k, max_k = METAS_DIARIAS["kcal"]
        ok = "✓" if min_k <= d.kcal <= max_k else "✗"
        lineas.append(f"    {nombre_dia:10}: {int(d.kcal):>5} kcal | P:{int(d.proteina):>3}g | G:{int(d.grasa):>3}g | C:{int(d.carbos):>3}g  {ok}")

    lineas.append("")
    lineas.append("-" * 60)
    lineas.append("--- FRECUENCIA DE ALIMENTOS ---")
    lineas.append("")

    freq = reporte.estadisticas.get("frecuencia")
    if freq:
        max_freq = max(freq.values())
        max_nombre = max(len(n) for n in freq.keys())
        for alimento, f in freq.most_common():
            barra_len = int((f / max_freq) * 20)
            barra = "#" * barra_len
            lineas.append(f"  {alimento:<{max_nombre}} : {barra} {f}")
    else:
        lineas.append("  No hay alimentos registrados.")

    lineas.append("")
    lineas.append("=" * 60)

    return "\n".join(lineas)


def formatear_analisis(reporte: ReporteSemanal) -> str:
    if reporte.estado_general == "SIN DATOS":
        return "No hay datos registrados para esta semana."

    texto = []
    texto.append("=" * 60)
    texto.append("  ANÁLISIS NUTRICIONAL SEMANAL")
    texto.append("=" * 60)
    texto.append(f"\nEstado General: {reporte.estado_general}")

    texto.append("\n\n--- PROMEDIOS DIARIOS ---")
    p = reporte.promedios
    texto.append(f"  Calorías   : {int(p.get('kcal', 0))} kcal")
    texto.append(f"  Proteína   : {int(p.get('proteina', 0))}g")
    texto.append(f"  Grasa      : {int(p.get('grasa', 0))}g")
    texto.append(f"  Carbohidratos: {int(p.get('carbos', 0))}g")

    if reporte.evaluaciones:
        texto.append("\n--- EVALUACIÓN ---")
        for ev in reporte.evaluaciones:
            estado = "✓" if ev.estado == "ok" else "✗"
            texto.append(f"  {ev.metrica.upper()}: {ev.mensaje} {estado}")

    if reporte.recomendaciones:
        texto.append("\n--- RECOMENDACIONES ---")
        for rec in reporte.recomendaciones:
            texto.append(f"  • {rec}")

    return "\n".join(texto)
