# Sistema de Nutrición

Aplicación de escritorio para seguimiento y análisis nutricional semanal.

## Arquitectura

El proyecto sigue el patrón **Clean Architecture** con 4 capas:

```
├── domain/              # Lógica pura de negocio (sin dependencias externas)
│   ├── models.py        # Modelo Alimento
│   ├── entities.py      # RegistroDiario, Comida
│   ├── report.py        # MacrosDia, EvaluacionNutricional, ReporteSemanal
│   ├── usuario.py       # Modelo Usuario
│   ├── normalizer.py    # Normalización de texto y mapeo de alimentos
│   ├── calculator.py    # Cálculo de macros y calorías
│   └── tmb_calculator.py # TMB/GET (Mifflin-St Jeor)
│
├── application/         # Casos de uso (coordinan dominio + infraestructura)
│   ├── services.py      # registrar_comida, obtener_reporte_semanal, analizar_semana, etc.
│   └── report_formatter.py # Formateo de reportes a texto
│
├── infrastructure/      # Acceso a datos
│   ├── user_repo.py     # Repositorio PostgreSQL para usuario
│   ├── comidas_repo.py  # Repositorio PostgreSQL para comidas
│   └── excel_repo.py    # Repositorio Excel (lectura/escritura)
│
├── presentation/        # Interfaz gráfica (Tkinter)
│   └── gui.py           # Aplicación GUI principal
│
├── config.py            # Configuración centralizada (usa .env)
├── .env                 # Credenciales (NO versionar)
├── requirements.txt     # Dependencias Python
└── pytest.ini           # Configuración de tests
```

### Reglas de dependencias

- **domain** → no importa nada del proyecto
- **application** → importa domain + infrastructure
- **infrastructure** → importa config
- **presentation** → importa application + config

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

Crear un archivo `.env` en la raíz del proyecto:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=BDP-Nutrición
DB_USER=postgres
DB_PASSWORD=tu_password
EXCEL_PATH_DEFAULT=C:\MIS DOCUMENTOS\IMPORTANTE\PROYECTOS\BD-Nutrición.xlsx
```

## Ejecución

### Desde código fuente

```bash
python presentation/gui.py
```

### Ejecutable compilado

```bash
dist/Sistema_Nutricion.exe
```

## Compilación

```bash
pyinstaller --noconfirm SistemaNutricion.spec
```

## Tests

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=domain --cov=application --cov-report=term-missing

# Solo unitarios
pytest tests/unit/

# Solo integración
pytest tests/integration/

# Solo e2e
pytest tests/e2e/
```

## Funcionalidades

- **Ingresar comidas**: Registro de desayuno, almuerzo, cena y extras por fecha
- **Generar reporte**: Reporte semanal con estadísticas, top alimentos, resumen nutricional vs metas
- **Análisis nutricional**: Evaluación de promedios diarios contra metas con recomendaciones
- **Calculadora TMB/GET**: Cálculo de Tasa Metabólica Basal y Gasto Energético Total
- **Doble almacenamiento**: Excel + PostgreSQL simultáneamente
