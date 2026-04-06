import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, timedelta

# In frozen mode, PyInstaller extracts everything to sys._MEIPASS
if getattr(sys, 'frozen', False):
    _MEI = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    if _MEI not in sys.path:
        sys.path.insert(0, _MEI)

from config import NIVELES_ACTIVIDAD, DIAS_SEMANA
from application.services import (
    registrar_comida, obtener_reporte_semanal, analizar_semana,
    calcular_tmb_get, guardar_usuario, cargar_usuario, obtener_vista_previa_dia,
)
from application.report_formatter import formatear_reporte, formatear_analisis
from infrastructure.alimentos_repo import (
    obtener_todos as obtener_referencia_pg,
    obtener_todos_con_detalle,
    insertar_alimento,
    buscar_todos,
    agregar_alias,
)


def obtener_lunes(fecha):
    from datetime import timedelta
    return fecha - timedelta(days=fecha.weekday())


class NutricionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Nutrición")
        self.geometry("750x650")
        self.resizable(False, False)

        self.reporte_actual = ""
        self.referencia = obtener_referencia_pg()
        self.ultima_fecha_reporte = None

        self._crear_interfaz()

    def _crear_interfaz(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        tab_ingresar = ttk.Frame(notebook, padding=15)
        tab_reporte = ttk.Frame(notebook, padding=15)
        tab_analisis = ttk.Frame(notebook, padding=15)
        tab_alimentos = ttk.Frame(notebook, padding=15)
        tab_backup = ttk.Frame(notebook, padding=15)

        notebook.add(tab_ingresar, text="  Ingresar Comidas  ")
        notebook.add(tab_reporte, text="  Generar Reporte  ")
        notebook.add(tab_analisis, text="  Análisis Nutricional  ")
        notebook.add(tab_alimentos, text="  Alimentos  ")
        notebook.add(tab_backup, text="  Backups  ")

        self._tab_ingresar(tab_ingresar)
        self._tab_reporte(tab_reporte)
        self._tab_analisis(tab_analisis)
        self._tab_alimentos(tab_alimentos)
        self._tab_backup(tab_backup)

    # ── TAB: Ingresar Comidas ──────────────────────────────

    def _tab_ingresar(self, parent):
        frame_form = ttk.LabelFrame(parent, text="Datos de comidas", padding=10)
        frame_form.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame_form, text="Fecha (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", pady=3)
        self.entry_fecha = ttk.Entry(frame_form, width=30)
        self.entry_fecha.grid(row=0, column=1, sticky="w", pady=3)
        self.entry_fecha.insert(0, str(datetime.today().date()))
        self.entry_fecha.bind("<FocusOut>", lambda e: self._actualizar_vista_previa())

        campos = [("Desayuno", "entry_desayuno"), ("Almuerzo", "entry_almuerzo"),
                   ("Cena", "entry_cena"), ("Extras (opcional)", "entry_extras")]
        for i, (label, attr) in enumerate(campos, 1):
            ttk.Label(frame_form, text=f"{label}:").grid(row=i, column=0, sticky="w", pady=3)
            entry = ttk.Entry(frame_form, width=40)
            entry.grid(row=i, column=1, sticky="w", pady=3)
            setattr(self, attr, entry)

        ttk.Label(frame_form, text="Formato: Alimento1/Alimento2/Alimento3",
                  foreground="gray").grid(row=5, column=0, columnspan=2, sticky="w", pady=(5, 0))

        frame_btn = ttk.Frame(frame_form)
        frame_btn.grid(row=6, column=0, columnspan=2, pady=10)
        ttk.Button(frame_btn, text="Guardar", command=self._guardar_comidas).pack(side="left", padx=5)
        ttk.Button(frame_btn, text="Ver día", command=self._actualizar_vista_previa).pack(side="left", padx=5)

        self.label_estado = ttk.Label(frame_form, text="", foreground="green")
        self.label_estado.grid(row=7, column=0, columnspan=2)

        frame_vista = ttk.LabelFrame(parent, text="Vista previa del día", padding=10)
        frame_vista.grid(row=1, column=0, sticky="nsew")

        cols = ("Comida", "Alimentos", "Calorías")
        self.tree_vista = ttk.Treeview(frame_vista, columns=cols, show="headings", height=8)
        for col in cols:
            self.tree_vista.heading(col, text=col)
        self.tree_vista.column("Comida", width=80)
        self.tree_vista.column("Alimentos", width=350)
        self.tree_vista.column("Calorías", width=80)
        self.tree_vista.grid(row=0, column=0, sticky="nsew")

        self.label_total_dia = ttk.Label(frame_vista, text="", font=("Consolas", 10, "bold"))
        self.label_total_dia.grid(row=1, column=0, sticky="w", pady=5)

    def _actualizar_vista_previa(self):
        for item in self.tree_vista.get_children():
            self.tree_vista.delete(item)
        try:
            fecha = datetime.strptime(self.entry_fecha.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            return
        vista = obtener_vista_previa_dia(fecha)
        for fila in vista["filas"]:
            self.tree_vista.insert("", "end", values=(fila["comida"], fila["alimentos"], f"{fila['kcal']} kcal"))
        self.label_total_dia.config(text=f"Total del día: {vista['total_kcal']} kcal")

    def _guardar_comidas(self):
        fecha_str = self.entry_fecha.get().strip()
        if not fecha_str:
            messagebox.showwarning("Campo requerido", "Ingrese una fecha.")
            return
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Fecha inválida", "Use el formato YYYY-MM-DD.")
            return

        desayuno = self.entry_desayuno.get().strip() or None
        almuerzo = self.entry_almuerzo.get().strip() or None
        cena = self.entry_cena.get().strip() or None
        extras = self.entry_extras.get().strip() or None

        if not desayuno and not almuerzo and not cena:
            messagebox.showwarning("Campo requerido", "Ingrese al menos una comida.")
            return

        try:
            resultado = registrar_comida(fecha, desayuno, almuerzo, cena, extras, self.referencia)
        except PermissionError:
            messagebox.showerror("Error", "No se pudo guardar. Cierra el archivo Excel e intenta de nuevo.")
            return
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")
            return

        if resultado["postgresql"] > 0:
            self.label_estado.config(text=f"Guardado: Excel + PostgreSQL ({resultado['postgresql']} registros)", foreground="green")
        else:
            self.label_estado.config(text="Guardado en Excel. PostgreSQL no disponible.", foreground="orange")

        self.entry_desayuno.delete(0, "end")
        self.entry_almuerzo.delete(0, "end")
        self.entry_cena.delete(0, "end")
        self.entry_extras.delete(0, "end")
        self._actualizar_vista_previa()

    # ── TAB: Generar Reporte ───────────────────────────────

    def _tab_reporte(self, parent):
        ttk.Label(parent, text="Inicio de semana (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_inicio = ttk.Entry(parent, width=20)
        self.entry_inicio.grid(row=0, column=1, sticky="w", pady=5)
        self.entry_inicio.insert(0, str(obtener_lunes(datetime.today().date())))

        frame_btn = ttk.Frame(parent)
        frame_btn.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Button(frame_btn, text="Generar Reporte", command=self._mostrar_reporte).pack(side="left", padx=(0, 10))
        ttk.Button(frame_btn, text="Guardar .txt", command=self._guardar_txt).pack(side="left")

        self.text_reporte = scrolledtext.ScrolledText(parent, width=85, height=30,
                                                       font=("Consolas", 9), wrap="word")
        self.text_reporte.grid(row=2, column=0, columnspan=2, pady=10, sticky="nsew")

    def _mostrar_reporte(self):
        fecha_str = self.entry_inicio.get().strip()
        if not fecha_str:
            messagebox.showwarning("Campo requerido", "Ingrese una fecha de inicio.")
            return
        try:
            fecha_inicio = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Fecha inválida", "Use el formato YYYY-MM-DD.")
            return

        try:
            reporte = obtener_reporte_semanal(fecha_inicio)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte:\n{e}")
            return

        self.reporte_actual = formatear_reporte(reporte)
        self.ultima_fecha_reporte = fecha_inicio
        self.text_reporte.config(state="normal")
        self.text_reporte.delete("1.0", "end")
        self.text_reporte.insert("1.0", self.reporte_actual)
        self.text_reporte.config(state="disabled")

    def _guardar_txt(self):
        if not self.reporte_actual:
            messagebox.showwarning("Sin reporte", "Primero genere un reporte.")
            return
        try:
            carpeta = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
            ruta = os.path.join(carpeta, "reporte_alimentacion.txt")
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self.reporte_actual)
            messagebox.showinfo("Guardado", f"Reporte guardado en:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    # ── TAB: Análisis Nutricional ──────────────────────────

    def _tab_analisis(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)

        tab_tmb = ttk.Frame(nb, padding=10)
        tab_decision = ttk.Frame(nb, padding=10)
        nb.add(tab_tmb, text="  Calculadora TMB  ")
        nb.add(tab_decision, text="  Análisis Semanal  ")

        self._tab_tmb(tab_tmb)
        self._tab_decision(tab_decision)

    def _tab_tmb(self, parent):
        frame_datos = ttk.LabelFrame(parent, text="Datos Personales", padding=15)
        frame_datos.pack(side="left", fill="y", padx=(0, 10))

        campos = [("Peso (kg):", "entry_peso"), ("Altura (cm):", "entry_altura"), ("Edad (años):", "entry_edad")]
        for i, (label, attr) in enumerate(campos):
            ttk.Label(frame_datos, text=label).grid(row=i, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame_datos, width=15)
            entry.grid(row=i, column=1, sticky="w", pady=5)
            setattr(self, attr, entry)

        ttk.Label(frame_datos, text="Sexo:").grid(row=3, column=0, sticky="w", pady=5)
        self.sexo_var = tk.StringVar(value="hombre")
        ttk.Radiobutton(frame_datos, text="Hombre", variable=self.sexo_var, value="hombre").grid(row=3, column=1, sticky="w")
        ttk.Radiobutton(frame_datos, text="Mujer", variable=self.sexo_var, value="mujer").grid(row=4, column=1, sticky="w")

        ttk.Button(frame_datos, text="Guardar Datos", command=self._guardar_usuario).grid(row=5, column=0, columnspan=2, pady=15)
        self.label_datos_guardados = ttk.Label(frame_datos, text="", foreground="green")
        self.label_datos_guardados.grid(row=6, column=0, columnspan=2)

        frame_res = ttk.LabelFrame(parent, text="Resultados", padding=15)
        frame_res.pack(side="left", fill="both", expand=True)

        self.label_tmb = ttk.Label(frame_res, text="TMB: -- kcal/día", font=("Arial", 14, "bold"))
        self.label_tmb.pack(pady=10)

        ttk.Label(frame_res, text="Nivel de actividad:").pack(pady=(10, 5))
        self.combo_actividad = ttk.Combobox(frame_res, values=list(NIVELES_ACTIVIDAD.keys()), state="readonly", width=20)
        self.combo_actividad.pack(pady=5)
        self.combo_actividad.bind("<<ComboboxSelected>>", lambda e: self._calcular_get())

        self.label_get = ttk.Label(frame_res, text="GET: -- kcal/día", font=("Arial", 14, "bold"))
        self.label_get.pack(pady=10)

        self._cargar_usuario()

    def _guardar_usuario(self):
        try:
            peso = float(self.entry_peso.get())
            altura = float(self.entry_altura.get())
            edad = int(self.entry_edad.get())
            sexo = self.sexo_var.get()
        except ValueError:
            messagebox.showerror("Error", "Ingrese valores numéricos válidos.")
            return
        try:
            guardar_usuario(peso, altura, edad, sexo, "sedentario")
            self.label_datos_guardados.config(text="Datos guardados ✓", foreground="green")
            self._calcular_tmb()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    def _cargar_usuario(self):
        try:
            u = cargar_usuario()
            if u["peso_kg"]: self.entry_peso.insert(0, str(u["peso_kg"]))
            if u["altura_cm"]: self.entry_altura.insert(0, str(u["altura_cm"]))
            if u["edad"]: self.entry_edad.insert(0, str(u["edad"]))
            if u["sexo"]: self.sexo_var.set(u["sexo"])
            if u["nivel_actividad"]: self.combo_actividad.set(u["nivel_actividad"])
            self._calcular_tmb()
        except Exception:
            pass

    def _calcular_tmb(self):
        try:
            peso = float(self.entry_peso.get())
            altura = float(self.entry_altura.get())
            edad = int(self.entry_edad.get())
            sexo = self.sexo_var.get()
        except ValueError:
            return
        resultado = calcular_tmb_get(peso, altura, edad, sexo, self.combo_actividad.get() or "sedentario")
        self.label_tmb.config(text=f"TMB: {resultado['tmb']} kcal/día")
        self._tmb_valor = resultado["tmb"]
        if self.combo_actividad.get():
            self._calcular_get()

    def _calcular_get(self):
        try:
            tmb = getattr(self, "_tmb_valor", 0)
            if not tmb:
                return
            nivel = self.combo_actividad.get()
            factor = NIVELES_ACTIVIDAD.get(nivel, {}).get("factor", 1.2)
            self.label_get.config(text=f"GET: {round(tmb * factor)} kcal/día (x{factor})")
        except Exception:
            pass

    def _tab_decision(self, parent):
        frame_fecha = ttk.Frame(parent)
        frame_fecha.pack(fill="x", pady=5)
        ttk.Label(frame_fecha, text="Semana inicio:").pack(side="left")
        self.entry_semana_inicio = ttk.Entry(frame_fecha, width=15)
        self.entry_semana_inicio.pack(side="left", padx=5)
        self.entry_semana_inicio.insert(0, str(obtener_lunes(datetime.today().date())))
        ttk.Button(frame_fecha, text="Analizar", command=self._analizar_semana).pack(side="left", padx=5)

        self.text_analisis = scrolledtext.ScrolledText(parent, font=("Consolas", 10))
        self.text_analisis.pack(fill="both", expand=True)

    def _analizar_semana(self):
        try:
            fecha_str = self.entry_semana_inicio.get().strip()
            if not fecha_str:
                fecha_str = str(self.ultima_fecha_reporte) if self.ultima_fecha_reporte else str(datetime.today().date())
            fecha_inicio = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            reporte = analizar_semana(fecha_inicio)
            texto = formatear_analisis(reporte)
            self.text_analisis.config(state="normal")
            self.text_analisis.delete("1.0", "end")
            self.text_analisis.insert("1.0", texto)
            self.text_analisis.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo analizar:\n{e}")

    # ── TAB: Alimentos ─────────────────────────────────────

    def _tab_alimentos(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)

        tab_agregar = ttk.Frame(nb, padding=10)
        tab_buscar = ttk.Frame(nb, padding=10)
        nb.add(tab_agregar, text="  Agregar Alimento  ")
        nb.add(tab_buscar, text="  Buscar Alimento  ")

        self._tab_agregar_alimento(tab_agregar)
        self._tab_buscar_alimento(tab_buscar)

    # ── TAB: Backups ───────────────────────────────────────

    def _tab_backup(self, parent):
        # Frame para controles
        frame_controls = ttk.LabelFrame(parent, text="Control de Backups", padding=15)
        frame_controls.pack(fill="x", pady=(0, 10))

        ttk.Button(frame_controls, text="Crear Backup Ahora", 
                  command=self._crear_backup).pack(side="left", padx=(0, 10))
        ttk.Button(frame_controls, text="Ver Historial", 
                  command=self._actualizar_historial_backups).pack(side="left")

        # Frame para el historial
        frame_historial = ttk.LabelFrame(parent, text="Historial de Backups", padding=15)
        frame_historial.pack(fill="both", expand=True)

        cols = ("Fecha", "Tamaño", "Estado")
        self.tree_backup = ttk.Treeview(frame_historial, columns=cols, show="headings", height=10)
        for col in cols:
            self.tree_backup.heading(col, text=col)
        self.tree_backup.column("Fecha", width=150)
        self.tree_backup.column("Tamaño", width=100)
        self.tree_backup.column("Estado", width=200)
        self.tree_backup.pack(fill="both", expand=True)

        # Barra de estado
        self.label_backup_estado = ttk.Label(parent, text="", foreground="blue")
        self.label_backup_estado.pack(fill="x", pady=(5, 0))

        # Cargar historial inicial
        self._actualizar_historial_backups()

    def _crear_backup(self):
        """Crear un backup de la base de datos"""
        self.label_backup_estado.config(text="Creando backup...", foreground="blue")
        self.update_idletasks()  # Forzar actualización de la UI

        try:
            # Importar y ejecutar la función de backup
            from backup import crear_backup, limpiar_viejos
            
            ruta = crear_backup()
            tamano = os.path.getsize(ruta)
            limpiar_viejos()
            
            self.label_backup_estado.config(
                text=f"Backup creado: {os.path.basename(ruta)} ({tamano / 1024:.1f} KB)", 
                foreground="green"
            )
            self._actualizar_historial_backups()
            
        except FileNotFoundError:
            self.label_backup_estado.config(
                text="ERROR: pg_dump no encontrado. Instale PostgreSQL y agregue su bin al PATH.", 
                foreground="red"
            )
            messagebox.showerror(
                "pg_dump no encontrado", 
                "No se pudo encontrar pg_dump. Asegúrese de que PostgreSQL esté instalado y su directorio bin esté en el PATH del sistema."
            )
        except Exception as e:
            self.label_backup_estado.config(
                text=f"Error: {str(e)}", 
                foreground="red"
            )
            messagebox.showerror("Error en Backup", f"No se pudo crear el backup:\n{e}")

    def _actualizar_historial_backups(self):
        """Actualizar la lista de backups disponibles"""
        # Limpiar árbol
        for item in self.tree_backup.get_children():
            self.tree_backup.delete(item)

        try:
            backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "backups")
            backup_dir = os.path.normpath(backup_dir)
            
            if not os.path.exists(backup_dir):
                self.tree_backup.insert("", "end", values=("No hay backups", "", ""))
                return

            archivos = sorted(
                [f for f in os.listdir(backup_dir) if f.startswith("backup_") and f.endswith(".sql")],
                reverse=True,
            )
            
            if not archivos:
                self.tree_backup.insert("", "end", values=("No hay backups", "", ""))
                return

            for archivo in archivos:
                ruta = os.path.join(backup_dir, archivo)
                tamano = os.path.getsize(ruta)
                fecha_str = archivo.replace("backup_", "").replace(".sql", "")
                # Formatear fecha: YYYY-MM-DD_HHMMSS -> DD/MM/YYYY HH:MM:SS
                try:
                    from datetime import datetime
                    fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d_%H%M%S")
                    fecha_formateada = fecha_obj.strftime("%d/%m/%Y %H:%M:%S")
                except:
                    fecha_formateada = fecha_str
                
                self.tree_backup.insert("", "end", values=(
                    fecha_formateada,
                    f"{tamano / 1024:.1f} KB",
                    "Disponible"
                ))
                
        except Exception as e:
            self.tree_backup.insert("", "end", values=("Error al cargar historial", str(e), ""))

    def _tab_agregar_alimento(self, parent):
        frame = ttk.LabelFrame(parent, text="Nuevo Alimento", padding=15)
        frame.pack(fill="x", pady=5)

        ttk.Label(frame, text="Nombre:").grid(row=0, column=0, sticky="w", pady=3)
        self.entry_alim_nombre = ttk.Entry(frame, width=30)
        self.entry_alim_nombre.grid(row=0, column=1, sticky="w", pady=3)

        ttk.Label(frame, text="Tipo:").grid(row=1, column=0, sticky="w", pady=3)
        tipos = ["Fruta", "Verdura", "Proteína", "Carbohidrato", "Grasa", "Lácteo", "Bebida", "Otro"]
        self.combo_alim_tipo = ttk.Combobox(frame, values=tipos, state="readonly", width=20)
        self.combo_alim_tipo.grid(row=1, column=1, sticky="w", pady=3)
        self.combo_alim_tipo.current(0)

        campos_macros = [("Proteína (g):", "entry_alim_prot"), ("Grasa (g):", "entry_alim_grasa"),
                         ("Carbohidratos (g):", "entry_alim_carb"), ("Calorías (kcal):", "entry_alim_kcal")]
        for i, (label, attr) in enumerate(campos_macros, 2):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=3)
            entry = ttk.Entry(frame, width=15)
            entry.grid(row=i, column=1, sticky="w", pady=3)
            setattr(self, attr, entry)

        ttk.Label(frame, text="Alias (opcional, separados por /):").grid(row=6, column=0, columnspan=2, sticky="w", pady=(10, 3))
        self.entry_alim_alias = ttk.Entry(frame, width=40)
        self.entry_alim_alias.grid(row=7, column=0, columnspan=2, sticky="w", pady=3)

        ttk.Button(frame, text="Guardar Alimento", command=self._guardar_alimento).grid(row=8, column=0, columnspan=2, pady=10)
        self.label_alim_estado = ttk.Label(frame, text="", foreground="green")
        self.label_alim_estado.grid(row=9, column=0, columnspan=2)

    def _guardar_alimento(self):
        nombre = self.entry_alim_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Campo requerido", "Ingrese el nombre del alimento.")
            return
        tipo = self.combo_alim_tipo.get()
        try:
            prot = float(self.entry_alim_prot.get().strip()) if self.entry_alim_prot.get().strip() else None
            grasa = float(self.entry_alim_grasa.get().strip()) if self.entry_alim_grasa.get().strip() else None
            carb = float(self.entry_alim_carb.get().strip()) if self.entry_alim_carb.get().strip() else None
            kcal = float(self.entry_alim_kcal.get().strip()) if self.entry_alim_kcal.get().strip() else None
        except ValueError:
            messagebox.showerror("Error", "Los valores de macros deben ser números.")
            return

        alias_str = self.entry_alim_alias.get().strip()
        alias = [a.strip() for a in alias_str.split("/")] if alias_str else None

        try:
            insertar_alimento(nombre, tipo, prot, grasa, carb, kcal, alias)
            self.label_alim_estado.config(text=f"Alimento '{nombre}' guardado exitosamente", foreground="green")
            self.entry_alim_nombre.delete(0, "end")
            self.entry_alim_prot.delete(0, "end")
            self.entry_alim_grasa.delete(0, "end")
            self.entry_alim_carb.delete(0, "end")
            self.entry_alim_kcal.delete(0, "end")
            self.entry_alim_alias.delete(0, "end")
            self.referencia = obtener_referencia_pg()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    def _tab_buscar_alimento(self, parent):
        frame_busq = ttk.Frame(parent)
        frame_busq.pack(fill="x", pady=5)
        ttk.Label(frame_busq, text="Buscar:").pack(side="left")
        self.entry_buscar = ttk.Entry(frame_busq, width=30)
        self.entry_buscar.pack(side="left", padx=5)
        self.entry_buscar.bind("<Return>", lambda e: self._buscar_alimento())
        ttk.Button(frame_busq, text="Buscar", command=self._buscar_alimento).pack(side="left")

        cols = ("Nombre", "Tipo", "Proteína", "Grasa", "Carbos", "kcal")
        self.tree_buscar = ttk.Treeview(parent, columns=cols, show="headings", height=15)
        for col in cols:
            self.tree_buscar.heading(col, text=col)
        self.tree_buscar.column("Nombre", width=150)
        self.tree_buscar.column("Tipo", width=80)
        self.tree_buscar.column("Proteína", width=70)
        self.tree_buscar.column("Grasa", width=70)
        self.tree_buscar.column("Carbos", width=70)
        self.tree_buscar.column("kcal", width=60)
        self.tree_buscar.pack(fill="both", expand=True, pady=5)

        self.tree_buscar.bind("<Double-1>", self._mostrar_detalle_alimento)
        self._cargar_todos_alimentos()

    def _cargar_todos_alimentos(self):
        for item in self.tree_buscar.get_children():
            self.tree_buscar.delete(item)
        alimentos = obtener_todos_con_detalle()
        for alim in alimentos:
            self.tree_buscar.insert("", "end", values=(
                alim["nombre"], alim["tipo"] or "",
                alim["proteina"] or "", alim["grasa"] or "",
                alim["carbos"] or "", alim["kcal"] or "",
            ))

    def _buscar_alimento(self):
        termino = self.entry_buscar.get().strip()
        if not termino:
            self._cargar_todos_alimentos()
            return
        for item in self.tree_buscar.get_children():
            self.tree_buscar.delete(item)
        resultados = buscar_todos(termino)
        for alim in resultados:
            self.tree_buscar.insert("", "end", values=(
                alim["nombre"], alim["tipo"] or "",
                alim["proteina"] or "", alim["grasa"] or "",
                alim["carbos"] or "", alim["kcal"] or "",
            ))
        if not resultados:
            messagebox.showinfo("Sin resultados", f"No se encontraron alimentos con '{termino}'")

    def _mostrar_detalle_alimento(self, event):
        sel = self.tree_buscar.selection()
        if not sel:
            return
        vals = self.tree_buscar.item(sel[0], "values")
        nombre = vals[0]
        detalle = buscar_todos(nombre)
        if not detalle:
            return
        alim = detalle[0]
        texto = f"Nombre: {alim['nombre']}\nTipo: {alim['tipo'] or 'N/A'}\n\n"
        texto += f"Proteína: {alim['proteina'] or 0} g\n"
        texto += f"Grasa: {alim['grasa'] or 0} g\n"
        texto += f"Carbohidratos: {alim['carbos'] or 0} g\n"
        texto += f"Calorías: {alim['kcal'] or 0} kcal"
        messagebox.showinfo(f"Detalle: {nombre}", texto)


if __name__ == "__main__":
    app = NutricionApp()
    app.mainloop()
