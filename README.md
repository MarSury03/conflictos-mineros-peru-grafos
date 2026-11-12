# Análisis evolutivo de actores y conflictos sociales vinculados a la actividad minera en el Perú: un enfoque desde la teoría de grafos

**Trabajo de investigación | Ingeniería de la Información | Perú | Periodo de estudio: 2021–2025**

Este repositorio reúne los **códigos, documentación metodológica, datos derivados que puedan compartirse, resultados, grafos y visualizaciones** de la investigación. El estudio analiza la evolución de las participaciones **documentadas** de actores en conflictos sociales vinculados con la minería en el Perú mediante redes bipartitas actor–conflicto y sus proyecciones.

> **Importante:** una arista actor–conflicto indica que un actor figura como participante en la ficha de un conflicto en un periodo determinado. **No implica necesariamente interacción directa, cooperación, oposición ni participación individual en los hechos de ese mes.**

## Fuente y alcance

- **Fuente principal:** Reportes Mensuales de Conflictos Sociales de la **Defensoría del Pueblo (Perú)**.
- **Periodo:** enero de 2021 a diciembre de 2025 (60 reportes, n.º 203–262).
- **Unidad analítica:** combinación única `periodo_reporte` + `id_caso` + `Id_actor`.
- **Criterio de inclusión:** casos socioambientales vinculados con la actividad minera y clasificados con hechos durante el mes, de acuerdo con las reglas de procesamiento documentadas.
- **Herramientas utilizadas en la investigación:** Python, pandas, PyMuPDF, NetworkX, NumPy, Plotly y scikit-learn, entre otras dependencias que deberán precisarse a partir de los scripts definitivos.

## Objetivos y fases del proyecto

| Fase | Objetivo | Contenido del código y resultados |
|---|---|---|
| **OE1** | Construcción y depuración de la base longitudinal | Extracción de PDF, selección de hechos del mes, limpieza, clasificación minera, normalización de actores, vinculación de casos, trazabilidad y deduplicación |
| **OE2** | Construcción de redes | Grafos bipartitos mensuales, anuales e histórico; proyecciones ponderadas actor–actor y conflicto–conflicto |
| **OE3** | Caracterización estructural | Grado, intermediación, densidad, componentes, centralidades, rankings y comunidades |
| **OE4** | Evolución temporal | Incorporaciones, salidas, persistencia, duración documental, Jaccard, evolución de rankings y comunidades (ARI) |
| **OE5** | Validación y sensibilidad | Pruebas programáticas, escenarios de exclusión institucional, revisión documental y reproducibilidad |

## Estructura del repositorio

```text
conflictos-mineros-peru-redes/
├── README.md
├── GUIA_GITHUB.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── 01_original/                 # PDFs y archivos fuente; normalmente no publicados
│   ├── 02_intermedia/               # Extracción, casos con hechos, selección minera
│   └── 03_final/                    # Relaciones únicas y maestros, si son publicables
├── src/
│   ├── fase1_base_longitudinal/
│   ├── fase2_construccion_redes/
│   ├── fase3_metricas_comunidades/
│   ├── fase4_evolucion_temporal/
│   └── fase5_validacion_sensibilidad/
├── resultados/
│   ├── oe1_base_longitudinal/
│   ├── oe2_redes/
│   ├── oe3_metricas/
│   ├── oe4_evolucion/
│   └── oe5_validacion/
├── grafos/
│   ├── bipartitos/                 # .graphml, .gpickle, .pkl (ver seguridad)
│   ├── proyeccion_actores/        # GraphML de actores
│   └── proyeccion_conflictos/     # GraphML de conflictos
├── figuras/
│   ├── diagramas_metodologia/
│   ├── visualizaciones_redes/
│   ├── graficos_metricas/
│   └── graficos_temporales/
├── notebooks/                     # Exploraciones .ipynb
├── docs/
│   ├── metodologia/
│   ├── diccionario_datos/
│   ├── decisiones_manuales/
│   └── registro_ejecuciones/
└── tests/                         # Pruebas reproducibles
```

Las carpetas tienen archivos `.gitkeep` para que Git las conserve incluso si todavía no tienen resultados. **La plantilla no incluye scripts ni datos reales**: agrega allí los archivos definitivos verificados.

## Cómo empezar

1. Instalar Python (preferentemente en un entorno virtual).
2. Incorporar los scripts definitivos a `src/` y revisar sus rutas de entrada y salida.
3. Completar y fijar versiones de `requirements.txt` a partir del entorno **efectivamente utilizado**.
4. Colocar las fuentes en `data/01_original/` (carpeta local excluida de Git por defecto) o adaptar las rutas de lectura.
5. Ejecutar los scripts **en el orden real que exijan sus dependencias**: OE1 → OE2 → OE3 → OE4 → OE5.
6. Exportar salidas tabulares a `resultados/`, redes serializadas a `grafos/` y material gráfico a `figuras/`.
7. Documentar comandos, parámetros, versiones y controles efectivamente ejecutados en `docs/registro_ejecuciones/`.

**Nota:** todavía no se incluyen comandos específicos de ejecución, porque los scripts actuales no forman parte de esta plantilla y no se deben inventar sus nombres, parámetros ni dependencias.

## Indicadores de referencia de la versión de trabajo

De acuerdo con el resumen de procesamiento proporcionado para esta versión:

| Indicador | Valor |
|---|---:|
| Reportes mensuales | 60 |
| Registros extraídos antes del filtro de hechos | 98 723 |
| Registros después de seleccionar casos con hechos | 44 744 |
| Registros mineros antes de expandir actores compuestos | 20 908 |
| Registros tras expansión y normalización | 21 327 |
| Relaciones actor–conflicto–periodo únicas | 20 913 |
| Actores normalizados | 802 |
| Conflictos longitudinales | 146 |
| Redes bipartitas (60 mensuales + 5 anuales + 1 histórica) | 66 |
| Grafos totales incluyendo ambas proyecciones | 198 |

Estos valores son **referencias de una versión de trabajo**. Deben actualizarse cuando se confirme la ejecución final y no sustituyen las tablas auditables de resultados.

## Resultados, figuras y reproducibilidad

- `resultados/` conserva tablas `CSV` o `XLSX` por objetivo.
- `grafos/` conserva representaciones de redes para análisis posterior; se recomienda GraphML para intercambio.
- `figuras/` conserva imágenes publicables (`PNG`, `SVG`) y visualizaciones (`HTML`, cuando corresponda).
- `docs/decisiones_manuales/` registra criterios y decisiones de equivalencia de actores y conflictos.
- `docs/registro_ejecuciones/` conserva fecha, entorno, parámetros, fuente y resultados de cada corrida final.

Los archivos `pickle` (`.pkl`, `.pickle`, `.gpickle`) **solo deben abrirse si provienen de una fuente confiable**, pues pueden ejecutar código al deserializarse.

## Fuente, atribución y límites

La información documental procede de la **Defensoría del Pueblo del Perú**. Los datos derivados, los criterios de clasificación, las normalizaciones y los gráficos son productos del procesamiento de esta investigación y deben distinguirse de las publicaciones institucionales originales.

Las redes representan **asociaciones documentales**. Sus centralidades y comunidades no demuestran por sí mismas influencia, coordinación o interacción directa entre actores. Antes de publicar archivos, verificar posibles datos personales, condiciones de uso de las fuentes y requisitos institucionales de publicación.

## Estado del repositorio

**Plantilla inicial de organización.** Pendiente de incorporar y comprobar los códigos, archivos y comandos correspondientes a cada fase. El estado de la investigación debe reflejarse con evidencias, sin marcar pruebas o validaciones pendientes como completadas.

## Citación y licencia

Para citar este trabajo, utilizar los datos bibliográficos de la versión final aprobada del documento académico. **No se incorpora una licencia por defecto**; debe acordarse con el equipo de autores y revisarse la política institucional antes de publicar código o datos.
