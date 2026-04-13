import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, timedelta
import tkinter.font as tkfont

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
from infrastructure.comidas_repo import obtener_comidas_semana, obtener_datos_semana


def obtener_lunes(fecha):
    from datetime import timedelta
    return fecha - timedelta(days=fecha.weekday())


# ==================== THEME ====================
COLORS = {
    "bg_main": "#0D0D0D",
    "bg_card": "#1A1A1A",
    "bg_input": "#1A1A1A",
    "border": "#2A2A2A",
    "text": "#FFFFFF",
    "text_secondary": "#B0B0B0",
    "green": "#00C853",
    "green_hover": "#00E676",
    "accent": "#C0C0C0",
    "error": "#FF5252",
}

# Try to use Poppins, fallback to Segoe UI
def get_font(family, size, weight=""):
    try:
        if weight:
            return tkfont.Font(family=family, size=size, weight=weight)
        return tkfont.Font(family=family, size=size)
    except:
        fallback = "Segoe UI" if family == "Poppins" else "Arial"
        if weight:
            return tkfont.Font(family=fallback, size=size, weight=weight)
        return tkfont.Font(family=fallback, size=size)

# Try to create fonts, if Poppins not available use fallback
try:
    test_font = tkfont.Font(family="Poppins", size=10)
    DEFAULT_FONT = ("Poppins", 10)
    TITLE_FONT = ("Poppins", 24, "bold")
    SUBTITLE_FONT = ("Poppins", 14, "bold")
    BUTTON_FONT = ("Poppins", 10, "bold")
    LABEL_FONT = ("Poppins", 10)
    TABLE_FONT = ("Poppins", 9)
except:
    DEFAULT_FONT = ("Segoe UI", 10)
    TITLE_FONT = ("Segoe UI", 24, "bold")
    SUBTITLE_FONT = ("Segoe UI", 14, "bold")
    BUTTON_FONT = ("Segoe UI", 10, "bold")
    LABEL_FONT = ("Segoe UI", 10)
    TABLE_FONT = ("Segoe UI", 9)


class NutricionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Nutrición")
        self.geometry("900x750")
        self.resizable(True, True)
        
        # Allow maximizing but not fullscreen (shows taskbar)
        self.bind("<Map>", self._on_window_map)
        
        # Force dark background on root
        self.configure(bg=COLORS["bg_main"])
        
        self._setup_styles()
        
        self.reporte_actual = ""
        self.referencia = obtener_referencia_pg()
        self.ultima_fecha_reporte = None

        self._crear_interfaz()

    def _on_window_map(self, event):
        # Prevent going fullscreen by limiting max size
        self.maxsize(2000, 1500)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # ==================== FRAMES ====================
        style.configure("TFrame", background=COLORS["bg_main"])
        style.configure("Card.TFrame", background=COLORS["bg_card"], borderwidth=0)
        
        # ==================== LABELS ====================
        style.configure("TLabel", 
            background=COLORS["bg_main"], 
            foreground=COLORS["text"],
            font=LABEL_FONT
        )
        style.configure("Card.TLabel",
            background=COLORS["bg_card"],
            foreground=COLORS["text"],
            font=LABEL_FONT
        )
        style.configure("Title.TLabel",
            background=COLORS["bg_main"],
            foreground=COLORS["green"],
            font=TITLE_FONT
        )
        
        # ==================== BUTTONS ====================
        style.configure("TButton",
            background=COLORS["bg_card"],
            foreground=COLORS["text"],
            font=BUTTON_FONT,
            borderwidth=1,
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            bordercolor=COLORS["border"],
            relief="flat"
        )
        style.map("TButton",
            background=[("active", COLORS["border"])],
            foreground=[("active", COLORS["text"])]
        )
        
        style.configure("Primary.TButton",
            background=COLORS["green"],
            foreground=COLORS["bg_main"],
            font=BUTTON_FONT,
            borderwidth=0,
            relief="flat"
        )
        style.map("Primary.TButton",
            background=[("active", COLORS["green_hover"])],
            foreground=[("active", COLORS["bg_main"])]
        )
        
        # ==================== ENTRIES ====================
        style.configure("TEntry",
            fieldbackground=COLORS["bg_input"],
            foreground=COLORS["text"],
            background=COLORS["bg_input"],
            borderwidth=1,
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            relief="flat",
            font=DEFAULT_FONT
        )
        
        # ==================== COMBOBOX ====================
        style.configure("TCombobox",
            fieldbackground=COLORS["bg_input"],
            foreground=COLORS["text"],
            background=COLORS["bg_input"],
            borderwidth=1,
            lightcolor=COLORS["border"],
            relief="flat",
            font=DEFAULT_FONT
        )
        style.map("TCombobox",
            fieldbackground=[("readonly", COLORS["bg_input"])],
            foreground=[("readonly", COLORS["text"])]
        )
        
        # ==================== RADIOBUTTON ====================
        style.configure("TRadiobutton",
            background=COLORS["bg_main"],
            foreground=COLORS["text"],
            font=LABEL_FONT,
            indicatorforeground=COLORS["green"]
        )
        
        # ==================== NOTEBOOK ====================
        style.configure("TNotebook",
            background=COLORS["bg_main"],
            borderwidth=0
        )
        style.configure("TNotebook.Tab",
            background=COLORS["bg_card"],
            foreground=COLORS["text_secondary"],
            font=LABEL_FONT,
            padding=(20, 10),
            borderwidth=0,
            lightcolor=COLORS["bg_card"],
            darkcolor=COLORS["bg_card"]
        )
        style.map("TNotebook.Tab",
            background=[("selected", COLORS["green"])],
            foreground=[("selected", COLORS["bg_main"])],
            lightcolor=[("selected", COLORS["green"])],
            darkcolor=[("selected", COLORS["green"])]
        )
        
        # ==================== LABELED FRAME ====================
        style.configure("TLabelframe",
            background=COLORS["bg_card"],
            borderwidth=0,
            relief="flat"
        )
        style.configure("TLabelframe.Label",
            background=COLORS["bg_card"],
            foreground=COLORS["text"],
            font=SUBTITLE_FONT,
            padding=(0, 0, 0, 8)
        )
        
        # ==================== TREEVIEW ====================
        style.configure("Treeview",
            background=COLORS["bg_card"],
            fieldbackground=COLORS["bg_card"],
            foreground=COLORS["text"],
            font=TABLE_FONT,
            rowheight=28,
            borderwidth=0,
            relief="flat"
        )
        style.configure("Treeview.Heading",
            background=COLORS["green"],
            foreground=COLORS["bg_main"],
            font=LABEL_FONT,
            padding=(10, 8),
            relief="flat"
        )
        style.map("Treeview",
            background=[("selected", COLORS["green"])],
            foreground=[("selected", COLORS["bg_main"])]
        )
        
        # ==================== SCROLLBAR ====================
        style.configure("Vertical.TScrollbar",
            background=COLORS["bg_card"],
            troughcolor=COLORS["bg_main"],
            borderwidth=0,
            relief="flat"
        )
        style.configure("Horizontal.TScrollbar",
            background=COLORS["bg_card"],
            troughcolor=COLORS["bg_main"],
            borderwidth=0,
            relief="flat"
        )

    def _crear_interfaz(self):
        # ==================== HEADER ====================
        self.header_frame = tk.Frame(self, bg=COLORS["bg_main"], height=80)
        self.header_frame.pack(fill="x", padx=24, pady=(24, 12))
        self.header_frame.pack_propagate(False)
        
        self.header_label = tk.Label(
            self.header_frame,
            text="Sistema de Nutrición",
            font=TITLE_FONT,
            bg=COLORS["bg_main"],
            fg=COLORS["green"]
        )
        self.header_label.pack(side="left", fill="y")
        
        # ==================== NOTEBOOK ====================
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        
        tab_ingresar = ttk.Frame(notebook, padding=24)
        tab_reporte = ttk.Frame(notebook, padding=24)
        tab_analisis = ttk.Frame(notebook, padding=24)
        tab_alimentos = ttk.Frame(notebook, padding=24)
        tab_backup = ttk.Frame(notebook, padding=24)
        tab_historial = ttk.Frame(notebook, padding=24)
        
        # Force background on tabs
        for tab in [tab_ingresar, tab_reporte, tab_analisis, tab_alimentos, tab_backup, tab_historial]:
            self._force_dark_background(tab)
        
        notebook.add(tab_ingresar, text="  Ingresar Comidas  ")
        notebook.add(tab_reporte, text="  Generar Reporte  ")
        notebook.add(tab_analisis, text="  Análisis Nutricional  ")
        notebook.add(tab_alimentos, text="  Alimentos  ")
        notebook.add(tab_backup, text="  Backups  ")
        notebook.add(tab_historial, text="  Historial Semanal  ")
        
        self._tab_ingresar(tab_ingresar)
        self._tab_reporte(tab_reporte)
        self._tab_analisis(tab_analisis)
        self._tab_alimentos(tab_alimentos)
        self._tab_backup(tab_backup)
        self._tab_historial(tab_historial)

    def _force_dark_background(self, widget):
        """Recursively force dark background on all widgets"""
        try:
            widget.configure(bg=COLORS["bg_main"])
        except:
            pass
        
        for child in widget.winfo_children():
            try:
                child.configure(bg=COLORS["bg_main"])
            except:
                pass
            try:
                self._force_dark_background(child)
            except:
                pass

    # ─────────────────────────────────────────────────────────
    # TAB: Ingresar Comidas
    # ─────────────────────────────────────────────────────────
    
    def _tab_ingresar(self, parent):
        # Card: Datos de comidas
        card_datos = ttk.LabelFrame(parent, text="Datos de comidas")
        card_datos.pack(fill="x", pady=(0, 24))
        
        # Force dark on card
        self._force_dark_on_labelframe(card_datos)
        
        # Fecha
        fecha_label = tk.Label(card_datos, text="Fecha (YYYY-MM-DD):", 
                              bg=COLORS["bg_card"], fg=COLORS["text_secondary"], font=LABEL_FONT)
        fecha_label.grid(row=0, column=0, sticky="w", pady=(0, 8), padx=20)
        
        self.entry_fecha = tk.Entry(card_datos, bg=COLORS["bg_input"], fg=COLORS["text"],
                                    font=DEFAULT_FONT, bd=1, highlightthickness=1,
                                    highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                                    insertbackground=COLORS["text"], width=30)
        self.entry_fecha.grid(row=0, column=1, sticky="w", pady=(0, 8), padx=(0, 20))
        self.entry_fecha.insert(0, str(datetime.today().date()))
        self.entry_fecha.bind("<FocusOut>", lambda e: self._actualizar_vista_previa())
        
        # Comidas
        campos = [("Desayuno", "entry_desayuno"), ("Almuerzo", "entry_almuerzo"),
                 ("Cena", "entry_cena"), ("Extras (opcional)", "entry_extras")]
        for i, (label, attr) in enumerate(campos, 1):
            lbl = tk.Label(card_datos, text=f"{label}:", bg=COLORS["bg_card"], 
                          fg=COLORS["text_secondary"], font=LABEL_FONT)
            lbl.grid(row=i, column=0, sticky="w", pady=(0, 8), padx=20)
            
            entry = tk.Entry(card_datos, bg=COLORS["bg_input"], fg=COLORS["text"],
                            font=DEFAULT_FONT, bd=1, highlightthickness=1,
                            highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                            insertbackground=COLORS["text"], width=35)
            entry.grid(row=i, column=1, sticky="w", pady=(0, 8), padx=(0, 20))
            setattr(self, attr, entry)
        
        # Hint
        hint = tk.Label(card_datos, text="Formato: Alimento1/Alimento2/Alimento3", 
                       bg=COLORS["bg_card"], fg=COLORS["green"], font=LABEL_FONT)
        hint.grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 0), padx=20)
        
        # Buttons
        btn_frame = tk.Frame(card_datos, bg=COLORS["bg_card"])
        btn_frame.grid(row=6, column=0, columnspan=2, pady=16)
        
        btn_guardar = tk.Button(btn_frame, text="Guardar", bg=COLORS["green"], fg=COLORS["bg_main"],
                              font=BUTTON_FONT, bd=0, padx=20, pady=8, cursor="hand2",
                              command=self._guardar_comidas)
        btn_guardar.pack(side="left", padx=(0, 12))
        
        btn_ver = tk.Button(btn_frame, text="Ver día", bg=COLORS["bg_card"], fg=COLORS["text"],
                          font=BUTTON_FONT, bd=1, padx=20, pady=8, cursor="hand2",
                          highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                          command=self._actualizar_vista_previa)
        btn_ver.pack(side="left")
        
        self.label_estado = tk.Label(card_datos, text="", bg=COLORS["bg_card"], 
                                     fg=COLORS["green"], font=LABEL_FONT)
        self.label_estado.grid(row=7, column=0, columnspan=2)
        
        # Card: Vista previa del día
        card_vista = ttk.LabelFrame(parent, text="Vista previa del día")
        card_vista.pack(fill="both", expand=True)
        self._force_dark_on_labelframe(card_vista)
        
        cols = ("Comida", "Alimentos", "Calorías")
        self.tree_vista = ttk.Treeview(card_vista, columns=cols, show="headings", height=8, selectmode="none",
                                        style="Treeview")
        for col in cols:
            self.tree_vista.heading(col, text=col, anchor="w")
        self.tree_vista.column("Comida", width=80, minwidth=60, anchor="w")
        self.tree_vista.column("Alimentos", width=550, minwidth=300, anchor="w")
        self.tree_vista.column("Calorías", width=80, minwidth=60, anchor="e")
        
        # Create container with visible border
        tree_container = tk.Frame(card_vista, bg=COLORS["border"], padx=1, pady=1)
        tree_container.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        # Pack treeview directly in the card (without using in_)
        self.tree_vista.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Style
        style = ttk.Style()
        style.configure("Treeview", rowheight=32)
        style.map("Treeview", background=[("selected", COLORS["green"])])
        
        # Separator and total label below the table
        sep = ttk.Separator(card_vista, orient="horizontal")
        sep.pack(fill="x", padx=10, pady=5)
        
        self.label_total_dia = tk.Label(card_vista, text="", bg=COLORS["bg_card"],
                                      fg=COLORS["green"], font=("Poppins", 11, "bold"))
        self.label_total_dia.pack(anchor="w", pady=(5, 10), padx=10)

    def _force_dark_on_labelframe(self, widget):
        """Force dark background on labelframe and its children"""
        try:
            widget.configure(style="TLabelframe")
        except:
            pass

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
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")
            return

        if resultado["postgresql"] > 0:
            self.label_estado.config(text=f"Guardado: PostgreSQL ({resultado['postgresql']} registros)", fg=COLORS["green"])
        else:
            self.label_estado.config(text="Guardado en Excel. PostgreSQL no disponible.", fg="orange")

        self.entry_desayuno.delete(0, "end")
        self.entry_almuerzo.delete(0, "end")
        self.entry_cena.delete(0, "end")
        self.entry_extras.delete(0, "end")
        self._actualizar_vista_previa()

    # ─────────────────────────────────────────────────────────
    # TAB: Generar Reporte
    # ─────────────────────────────────────────────────────────
    
    def _tab_reporte(self, parent):
        # Input section
        input_frame = tk.Frame(parent, bg=COLORS["bg_main"])
        input_frame.pack(fill="x", pady=(0, 16))
        
        fecha_label = tk.Label(input_frame, text="Inicio de semana (YYYY-MM-DD):", 
                             bg=COLORS["bg_main"], fg=COLORS["text_secondary"], font=LABEL_FONT)
        fecha_label.pack(side="left", pady=5)
        
        self.entry_inicio = tk.Entry(input_frame, bg=COLORS["bg_input"], fg=COLORS["text"],
                                    font=DEFAULT_FONT, bd=1, highlightthickness=1,
                                    highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                                    insertbackground=COLORS["text"], width=20)
        self.entry_inicio.pack(side="left", padx=(12, 24), pady=5)
        self.entry_inicio.insert(0, str(obtener_lunes(datetime.today().date())))
        
        btn_generar = tk.Button(input_frame, text="Generar Reporte", bg=COLORS["green"], fg=COLORS["bg_main"],
                               font=BUTTON_FONT, bd=0, padx=20, pady=8, cursor="hand2",
                               command=self._mostrar_reporte)
        btn_generar.pack(side="left", padx=(0, 8))
        
        btn_guardar = tk.Button(input_frame, text="Guardar .txt", bg=COLORS["bg_card"], fg=COLORS["text"],
                               font=BUTTON_FONT, bd=1, padx=20, pady=8, cursor="hand2",
                               highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                               command=self._guardar_txt)
        btn_guardar.pack(side="left")
        
        # Report text - using tk.Text instead of ScrolledText for better control
        self.text_reporte = tk.Text(parent, bg=COLORS["bg_input"], fg=COLORS["text"],
                                   font=TABLE_FONT, wrap="word", bd=0, 
                                   highlightthickness=0, insertbackground=COLORS["text"])
        self.text_reporter_scroll = ttk.Scrollbar(parent, command=self.text_reporte.yview)
        self.text_reporte.configure(yscrollcommand=self.text_reporter_scroll.set)
        self.text_reporter_scroll.pack(side="right", fill="y", pady=(16, 0))
        self.text_reporte.pack(fill="both", expand=True, pady=(16, 0))

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
        self.text_reporte.delete("1.0", "end")
        self.text_reporte.insert("1.0", self.reporte_actual)

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

    # ─────────────────────────────────────────────────────────
    # TAB: Análisis Nutricional
    # ─────────────────────────────────────────────────────────
    
    def _tab_analisis(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)
        
        # Force dark on notebook
        self._force_dark_background(nb)

        tab_tmb = ttk.Frame(nb, padding=20)
        tab_decision = ttk.Frame(nb, padding=20)
        self._force_dark_background(tab_tmb)
        self._force_dark_background(tab_decision)
        
        nb.add(tab_tmb, text="  Calculadora TMB  ")
        nb.add(tab_decision, text="  Análisis Semanal  ")

        self._tab_tmb(tab_tmb)
        self._tab_decision(tab_decision)

    def _tab_tmb(self, parent):
        # Card: Datos Personales
        card_datos = ttk.LabelFrame(parent, text="Datos Personales")
        card_datos.pack(side="left", fill="y", padx=(0, 20))
        self._force_dark_on_labelframe(card_datos)
        
        campos = [("Peso (kg):", "entry_peso"), ("Altura (cm):", "entry_altura"), ("Edad (años):", "entry_edad")]
        for i, (label, attr) in enumerate(campos):
            lbl = tk.Label(card_datos, text=label, bg=COLORS["bg_card"], 
                          fg=COLORS["text_secondary"], font=LABEL_FONT)
            lbl.grid(row=i, column=0, sticky="w", pady=8, padx=20)
            
            entry = tk.Entry(card_datos, bg=COLORS["bg_input"], fg=COLORS["text"],
                            font=DEFAULT_FONT, bd=1, highlightthickness=1,
                            highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                            insertbackground=COLORS["text"], width=15)
            entry.grid(row=i, column=1, sticky="w", pady=8, padx=(12, 20))
            setattr(self, attr, entry)

        lbl_sexo = tk.Label(card_datos, text="Sexo:", bg=COLORS["bg_card"], 
                          fg=COLORS["text_secondary"], font=LABEL_FONT)
        lbl_sexo.grid(row=3, column=0, sticky="w", pady=8, padx=20)
        
        self.sexo_var = tk.StringVar(value="hombre")
        radio_hombre = tk.Radiobutton(card_datos, text="Hombre", variable=self.sexo_var, value="hombre",
                                      bg=COLORS["bg_card"], fg=COLORS["text"], font=LABEL_FONT,
                                      selectcolor=COLORS["bg_card"], activebackground=COLORS["bg_card"])
        radio_hombre.grid(row=3, column=1, sticky="w", pady=8)
        
        radio_mujer = tk.Radiobutton(card_datos, text="Mujer", variable=self.sexo_var, value="mujer",
                                    bg=COLORS["bg_card"], fg=COLORS["text"], font=LABEL_FONT,
                                    selectcolor=COLORS["bg_card"], activebackground=COLORS["bg_card"])
        radio_mujer.grid(row=4, column=1, sticky="w", pady=8)

        btn_guardar = tk.Button(card_datos, text="Guardar Datos", bg=COLORS["green"], fg=COLORS["bg_main"],
                              font=BUTTON_FONT, bd=0, padx=20, pady=8, cursor="hand2",
                              command=self._guardar_usuario)
        btn_guardar.grid(row=5, column=0, columnspan=2, pady=16)
        
        self.label_datos_guardados = tk.Label(card_datos, text="", bg=COLORS["bg_card"], 
                                             fg=COLORS["green"], font=LABEL_FONT)
        self.label_datos_guardados.grid(row=6, column=0, columnspan=2)

        # Card: Resultados
        card_res = ttk.LabelFrame(parent, text="Resultados")
        card_res.pack(side="left", fill="both", expand=True)
        self._force_dark_on_labelframe(card_res)
        
        self.label_tmb = tk.Label(card_res, text="TMB: -- kcal/día", 
                              bg=COLORS["bg_card"], fg=COLORS["green"], font=("Poppins", 16, "bold"))
        self.label_tmb.pack(pady=(0, 16))

        lbl_actividad = tk.Label(card_res, text="Nivel de actividad:", bg=COLORS["bg_card"], 
                               fg=COLORS["text_secondary"], font=LABEL_FONT)
        lbl_actividad.pack(pady=(0, 8))
        
        self.combo_actividad = ttk.Combobox(card_res, values=list(NIVELES_ACTIVIDAD.keys()), 
                                         state="readonly", width=20, font=DEFAULT_FONT)
        self.combo_actividad.pack(pady=(0, 16))
        self.combo_actividad.bind("<<ComboboxSelected>>", lambda e: self._calcular_get())

        self.label_get = tk.Label(card_res, text="GET: -- kcal/día", 
                              bg=COLORS["bg_card"], fg=COLORS["green"], font=("Poppins", 16, "bold"))
        self.label_get.pack()

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
            self.label_datos_guardados.config(text="Datos guardados ✓", fg=COLORS["green"])
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
        frame_fecha = tk.Frame(parent, bg=COLORS["bg_main"])
        frame_fecha.pack(fill="x", pady=(0, 16))
        
        lbl = tk.Label(frame_fecha, text="Semana inicio:", bg=COLORS["bg_main"], 
                      fg=COLORS["text_secondary"], font=LABEL_FONT)
        lbl.pack(side="left")
        
        self.entry_semana_inicio = tk.Entry(frame_fecha, bg=COLORS["bg_input"], fg=COLORS["text"],
                                           font=DEFAULT_FONT, bd=1, highlightthickness=1,
                                           highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                                           insertbackground=COLORS["text"], width=15)
        self.entry_semana_inicio.pack(side="left", padx=12)
        self.entry_semana_inicio.insert(0, str(obtener_lunes(datetime.today().date())))
        
        btn = tk.Button(frame_fecha, text="Analizar", bg=COLORS["green"], fg=COLORS["bg_main"],
                       font=BUTTON_FONT, bd=0, padx=20, pady=8, cursor="hand2",
                       command=self._analizar_semana)
        btn.pack(side="left", padx=12)

        self.text_analisis = tk.Text(parent, bg=COLORS["bg_input"], fg=COLORS["text"],
                                    font=TABLE_FONT, wrap="word", bd=0, 
                                    highlightthickness=0, insertbackground=COLORS["text"])
        self.text_analisis.pack(fill="both", expand=True)

    def _analizar_semana(self):
        try:
            fecha_str = self.entry_semana_inicio.get().strip()
            if not fecha_str:
                fecha_str = str(self.ultima_fecha_reporte) if self.ultima_fecha_reporte else str(datetime.today().date())
            fecha_inicio = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            reporte = analizar_semana(fecha_inicio)
            texto = formatear_analisis(reporte)
            self.text_analisis.delete("1.0", "end")
            self.text_analisis.insert("1.0", texto)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo analizar:\n{e}")

    # ─────────────────────────────────────────────────────────
    # TAB: Alimentos
    # ─────────────────────────────────────────────────────────
    
    def _tab_alimentos(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)
        self._force_dark_background(nb)

        tab_agregar = ttk.Frame(nb, padding=20)
        tab_buscar = ttk.Frame(nb, padding=20)
        self._force_dark_background(tab_agregar)
        self._force_dark_background(tab_buscar)
        
        nb.add(tab_agregar, text="  Agregar Alimento  ")
        nb.add(tab_buscar, text="  Buscar Alimento  ")

        self._tab_agregar_alimento(tab_agregar)
        self._tab_buscar_alimento(tab_buscar)

    def _tab_agregar_alimento(self, parent):
        frame = ttk.LabelFrame(parent, text="Nuevo Alimento")
        frame.pack(fill="x", pady=(0, 16))
        self._force_dark_on_labelframe(frame)
        
        lbl_nombre = tk.Label(frame, text="Nombre:", bg=COLORS["bg_card"], 
                            fg=COLORS["text_secondary"], font=LABEL_FONT)
        lbl_nombre.grid(row=0, column=0, sticky="w", pady=8, padx=20)
        
        self.entry_alim_nombre = tk.Entry(frame, bg=COLORS["bg_input"], fg=COLORS["text"],
                                         font=DEFAULT_FONT, bd=1, highlightthickness=1,
                                         highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                                         insertbackground=COLORS["text"], width=35)
        self.entry_alim_nombre.grid(row=0, column=1, sticky="w", pady=8)

        lbl_tipo = tk.Label(frame, text="Tipo:", bg=COLORS["bg_card"], 
                          fg=COLORS["text_secondary"], font=LABEL_FONT)
        lbl_tipo.grid(row=1, column=0, sticky="w", pady=8, padx=20)
        
        tipos = ["Fruta", "Verdura", "Proteína", "Carbohidrato", "Grasa", "Lácteo", "Bebida", "Otro"]
        self.combo_alim_tipo = ttk.Combobox(frame, values=tipos, state="readonly", width=25, font=DEFAULT_FONT)
        self.combo_alim_tipo.grid(row=1, column=1, sticky="w", pady=8)
        self.combo_alim_tipo.current(0)

        campos_macros = [("Proteína (g):", "entry_alim_prot"), ("Grasa (g):", "entry_alim_grasa"),
                      ("Carbohidratos (g):", "entry_alim_carb"), ("Calorías (kcal):", "entry_alim_kcal")]
        for i, (label, attr) in enumerate(campos_macros, 2):
            lbl = tk.Label(frame, text=label, bg=COLORS["bg_card"], 
                          fg=COLORS["text_secondary"], font=LABEL_FONT)
            lbl.grid(row=i, column=0, sticky="w", pady=8, padx=20)
            
            entry = tk.Entry(frame, bg=COLORS["bg_input"], fg=COLORS["text"],
                            font=DEFAULT_FONT, bd=1, highlightthickness=1,
                            highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                            insertbackground=COLORS["text"], width=15)
            entry.grid(row=i, column=1, sticky="w", pady=8, padx=(12, 0))
            setattr(self, attr, entry)

        lbl_alias = tk.Label(frame, text="Alias (opcional, separados por /):", 
                           bg=COLORS["bg_card"], fg=COLORS["text_secondary"], font=LABEL_FONT)
        lbl_alias.grid(row=6, column=0, columnspan=2, sticky="w", pady=(16, 8), padx=20)
        
        self.entry_alim_alias = tk.Entry(frame, bg=COLORS["bg_input"], fg=COLORS["text"],
                                        font=DEFAULT_FONT, bd=1, highlightthickness=1,
                                        highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                                        insertbackground=COLORS["text"], width=40)
        self.entry_alim_alias.grid(row=7, column=0, columnspan=2, sticky="w", pady=8, padx=20)

        btn = tk.Button(frame, text="Guardar Alimento", bg=COLORS["green"], fg=COLORS["bg_main"],
                       font=BUTTON_FONT, bd=0, padx=20, pady=8, cursor="hand2",
                       command=self._guardar_alimento)
        btn.grid(row=8, column=0, columnspan=2, pady=16)
        
        self.label_alim_estado = tk.Label(frame, text="", bg=COLORS["bg_card"], 
                                          fg=COLORS["green"], font=LABEL_FONT)
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
            self.label_alim_estado.config(text=f"Alimento '{nombre}' guardado exitosamente", fg=COLORS["green"])
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
        frame_busq = tk.Frame(parent, bg=COLORS["bg_main"])
        frame_busq.pack(fill="x", pady=(0, 16))
        
        lbl = tk.Label(frame_busq, text="Buscar:", bg=COLORS["bg_main"], 
                      fg=COLORS["text_secondary"], font=LABEL_FONT)
        lbl.pack(side="left")
        
        self.entry_buscar = tk.Entry(frame_busq, bg=COLORS["bg_input"], fg=COLORS["text"],
                                    font=DEFAULT_FONT, bd=1, highlightthickness=1,
                                    highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                                    insertbackground=COLORS["text"], width=35)
        self.entry_buscar.pack(side="left", padx=12)
        self.entry_buscar.bind("<Return>", lambda e: self._buscar_alimento())
        
        btn = tk.Button(frame_busq, text="Buscar", bg=COLORS["green"], fg=COLORS["bg_main"],
                       font=BUTTON_FONT, bd=0, padx=20, pady=8, cursor="hand2",
                       command=self._buscar_alimento)
        btn.pack(side="left")

        cols = ("Nombre", "Tipo", "Proteína", "Grasa", "Carbos", "kcal")
        self.tree_buscar = ttk.Treeview(parent, columns=cols, show="headings", height=15)
        
        # Container with border
        tree_container = tk.Frame(parent, bg=COLORS["border"], padx=1, pady=1)
        tree_container.pack(fill="both", expand=True, pady=5)
        
        # Pack treeview directly
        self.tree_buscar.pack(fill="both", expand=True, padx=1, pady=1)
        
        for col in cols:
            self.tree_buscar.heading(col, text=col, anchor="w")
            self.tree_buscar.heading(col, text=col, anchor="w")
        self.tree_buscar.column("Nombre", width=180, minwidth=120)
        self.tree_buscar.column("Tipo", width=100, minwidth=80)
        self.tree_buscar.column("Proteína", width=70, minwidth=50)
        self.tree_buscar.column("Grasa", width=70, minwidth=50)
        self.tree_buscar.column("Carbos", width=70, minwidth=50)
        self.tree_buscar.column("kcal", width=70, minwidth=50)
        
        self.tree_buscar.bind("<Double-1>", self._mostrar_detalle_alimento)
        self._cargar_todos_alimentos()

    def _cargar_todos_alimentos(self):
        for item in self.tree_buscar.get_children():
            self.tree_buscar.delete(item)
        alimentos = obtener_todos_con_detalle()
        for alim in alimentos:
            self.tree_buscar.insert("", "end", values=(
                alim["nombre"], alim["tipo"] or "",
                self._formatear_macro(alim["proteina"]), self._formatear_macro(alim["grasa"]),
                self._formatear_macro(alim["carbos"]), self._formatear_macro(alim["kcal"]),
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
                self._formatear_macro(alim["proteina"]), self._formatear_macro(alim["grasa"]),
                self._formatear_macro(alim["carbos"]), self._formatear_macro(alim["kcal"]),
            ))
        if not resultados:
            messagebox.showinfo("Sin resultados", f"No se encontraron alimentos con '{termino}'")

    def _formatear_macro(self, valor):
        if valor is None:
            return ""
        return str(valor)

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
        texto += f"Proteína: {alim['proteina'] if alim['proteina'] is not None else 0} g\n"
        texto += f"Grasa: {alim['grasa'] if alim['grasa'] is not None else 0} g\n"
        texto += f"Carbohidratos: {alim['carbos'] if alim['carbos'] is not None else 0} g\n"
        texto += f"Calorías: {alim['kcal'] if alim['kcal'] is not None else 0} kcal"
        messagebox.showinfo(f"Detalle: {nombre}", texto)

    # ─────────────────────────────────────────────────────────
    # TAB: Backups
    # ─────────────────────────────────────────────────────────
    
    def _tab_backup(self, parent):
        frame_controls = ttk.LabelFrame(parent, text="Control de Backups")
        frame_controls.pack(fill="x", pady=(0, 16))
        self._force_dark_on_labelframe(frame_controls)
        
        btn_backup = tk.Button(frame_controls, text="Crear Backup Ahora", bg=COLORS["green"], 
                              fg=COLORS["bg_main"], font=BUTTON_FONT, bd=0, padx=20, pady=8, cursor="hand2",
                              command=self._crear_backup)
        btn_backup.pack(side="left", padx=(20, 12), pady=20)
        
        btn_historial = tk.Button(frame_controls, text="Ver Historial", bg=COLORS["bg_card"], 
                                  fg=COLORS["text"], font=BUTTON_FONT, bd=1, padx=20, pady=8, cursor="hand2",
                                  highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                                  command=self._actualizar_historial_backups)
        btn_historial.pack(side="left", pady=20)

        frame_historial = ttk.LabelFrame(parent, text="Historial de Backups")
        frame_historial.pack(fill="both", expand=True)
        self._force_dark_on_labelframe(frame_historial)

        cols = ("Fecha", "Tamaño", "Estado")
        self.tree_backup = ttk.Treeview(frame_historial, columns=cols, show="headings", height=10)
        for col in cols:
            self.tree_backup.heading(col, text=col, anchor="w")
        self.tree_backup.column("Fecha", width=180, minwidth=120)
        self.tree_backup.column("Tamaño", width=120, minwidth=80)
        self.tree_backup.column("Estado", width=200, minwidth=100)
        self.tree_backup.pack(fill="both", expand=True, padx=10, pady=10)

        self.label_backup_estado = tk.Label(parent, text="", bg=COLORS["bg_main"], 
                                           fg=COLORS["green"], font=LABEL_FONT)
        self.label_backup_estado.pack(anchor="w", pady=(12, 0))

        self._actualizar_historial_backups()

    def _crear_backup(self):
        self.label_backup_estado.config(text="Creando backup...", fg=COLORS["text_secondary"])
        self.update_idletasks()

        try:
            from backup import crear_backup, limpiar_viejos
            
            ruta = crear_backup()
            tamano = os.path.getsize(ruta)
            limpiar_viejos()
            
            self.label_backup_estado.config(
                text=f"Backup creado: {os.path.basename(ruta)} ({tamano / 1024:.1f} KB)", 
                fg=COLORS["green"]
            )
            self._actualizar_historial_backups()
            
        except FileNotFoundError as e:
            self.label_backup_estado.config(text=f"ERROR: {e}", fg=COLORS["error"])
            messagebox.showerror("pg_dump no encontrado", "No se encontró pg_dump.")
        except Exception as e:
            self.label_backup_estado.config(text=f"Error: {type(e).__name__}", fg=COLORS["error"])
            messagebox.showerror("Error en Backup", f"{type(e).__name__}: {e}")

    def _actualizar_historial_backups(self):
        for item in self.tree_backup.get_children():
            self.tree_backup.delete(item)

        try:
            if getattr(sys, 'frozen', False):
                _ROOT = os.path.dirname(sys.executable)
            else:
                _ROOT = os.path.dirname(os.path.abspath(__file__))
            backup_dir = os.path.join(_ROOT, "Backups")
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
                try:
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
            self.tree_backup.insert("", "end", values=("Error", str(e), ""))

    # ─────────────────────────────────────────────────────────
    # TAB: Historial Semanal
    # ─────────────────────────────────────────────────────────
    
    def _tab_historial(self, parent):
        frame_fecha = tk.Frame(parent, bg=COLORS["bg_main"])
        frame_fecha.pack(fill="x", pady=(0, 16))
        
        lbl = tk.Label(frame_fecha, text="Semana inicio (YYYY-MM-DD):", bg=COLORS["bg_main"], 
                      fg=COLORS["text_secondary"], font=LABEL_FONT)
        lbl.pack(side="left")
        
        self.entry_historial_fecha = tk.Entry(frame_fecha, bg=COLORS["bg_input"], fg=COLORS["text"],
                                              font=DEFAULT_FONT, bd=1, highlightthickness=1,
                                              highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                                              insertbackground=COLORS["text"], width=15)
        self.entry_historial_fecha.pack(side="left", padx=12)
        self.entry_historial_fecha.insert(0, str(obtener_lunes(datetime.today().date())))
        
        btn_ver = tk.Button(frame_fecha, text="Ver", bg=COLORS["green"], fg=COLORS["bg_main"],
                           font=BUTTON_FONT, bd=0, padx=20, pady=8, cursor="hand2",
                           command=self._cargar_historial)
        btn_ver.pack(side="left", padx=8)
        
        btn_hoy = tk.Button(frame_fecha, text="Hoy", bg=COLORS["bg_card"], fg=COLORS["text"],
                           font=BUTTON_FONT, bd=1, padx=20, pady=8, cursor="hand2",
                           highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                           command=self._ir_hoy)
        btn_hoy.pack(side="left")

        cols = ("Fecha", "Desayuno", "Almuerzo", "Cena", "Extras", "Total kcal")
        self.tree_historial = ttk.Treeview(parent, columns=cols, show="headings", height=18)
        for col in cols:
            self.tree_historial.heading(col, text=col, anchor="w")
        self.tree_historial.column("Fecha", width=100, minwidth=80)
        self.tree_historial.column("Desayuno", width=150, minwidth=100)
        self.tree_historial.column("Almuerzo", width=150, minwidth=100)
        self.tree_historial.column("Cena", width=150, minwidth=100)
        self.tree_historial.column("Extras", width=150, minwidth=100)
        self.tree_historial.column("Total kcal", width=90, minwidth=60)
        self.tree_historial.pack(fill="both", expand=True)

        self._cargar_historial()

    def _ir_hoy(self):
        self.entry_historial_fecha.delete(0, "end")
        self.entry_historial_fecha.insert(0, str(obtener_lunes(datetime.today().date())))
        self._cargar_historial()

    def _cargar_historial(self):
        for item in self.tree_historial.get_children():
            self.tree_historial.delete(item)
        
        fecha_str = self.entry_historial_fecha.get().strip()
        if not fecha_str:
            messagebox.showwarning("Campo requerido", "Ingrese una fecha de inicio.")
            return
        try:
            fecha_inicio = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Fecha inválida", "Use el formato YYYY-MM-DD.")
            return

        fecha_fin = fecha_inicio + timedelta(days=6)

        try:
            comidas = obtener_comidas_semana(fecha_inicio, fecha_fin)
            datos = obtener_datos_semana(fecha_inicio, fecha_fin)
            datos_dict = {d["fecha"]: d for d in datos}
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el historial:\n{e}")
            return

        for comida in comidas:
            fecha = comida["fecha"]
            desayuno = ", ".join(comida.get("desayuno", [])) or "-"
            almuerzo = ", ".join(comida.get("almuerzo", [])) or "-"
            cena = ", ".join(comida.get("cena", [])) or "-"
            extras = ", ".join(comida.get("extras", [])) or "-"
            
            total_kcal = datos_dict.get(fecha, {}).get("kcal", 0)
            
            self.tree_historial.insert("", "end", values=(
                fecha.strftime("%Y-%m-%d"),
                desayuno[:22] + ("..." if len(desayuno) > 22 else ""),
                almuerzo[:22] + ("..." if len(almuerzo) > 22 else ""),
                cena[:22] + ("..." if len(cena) > 22 else ""),
                extras[:22] + ("..." if len(extras) > 22 else ""),
                f"{int(total_kcal)}"
            ))


if __name__ == "__main__":
    app = NutricionApp()
    app.mainloop()