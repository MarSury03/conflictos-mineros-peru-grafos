# Fase 1 — Conflictos sociales mineros 2021–2025

Este repositorio contiene el pipeline reproducible de la Fase 1 de la tesis. El proceso parte de los 60 Reportes Mensuales de Conflictos Sociales de la Defensoría del Pueblo (reportes n.º 203–262) y genera la base longitudinal de relaciones actor–conflicto–mes.

## Flujo del procesamiento

1. Extracción de los reportes PDF y selección de casos con hechos durante el mes.
2. Limpieza de los campos textuales.
3. Selección de conflictos socioambientales vinculados con la minería.
4. Normalización e identificación de actores.
5. Vinculación longitudinal y asignación de IDs de casos.
6. Consolidación de relaciones mensuales únicas y generación de indicadores para resultados.

## Archivos principales

- `pipeline_fase1_unificado.py`: código único que integra las seis etapas del procesamiento.
- `PARES_CASOS_REVISAR.csv`: revisión manual de 39 pares candidatos; contiene 38 decisiones `MISMO` y una decisión `DIFERENTE`.
- `resultados/FASE1_MINERIA_CON_IDS_ACTORES_Y_CASOS.xlsx`: base final en Excel para revisión manual.
- `resultados/FASE1_MINERIA_CON_IDS_ACTORES_Y_CASOS.csv`: la misma base final en CSV para reproducibilidad.
- `resultados/FASE1_RELACIONES_MENSUALES_UNICAS.csv`: una relación por `periodo_reporte`, `id_caso` e `Id_actor`.
- `resultados/RESUMEN_RESULTADOS_FASE1.csv`: indicadores organizados según las cinco subsecciones metodológicas.
- `resultados/RESUMEN_MENSUAL_CASOS_ACTORES_FASE1.csv`: número de registros, casos y actores por mes.
- `resultados/RESULTADOS_NUMERICOS_FASE1.tex`: tablas LaTeX generadas automáticamente.
- `resultados/MANIFIESTO_FASE1.json`: cantidades finales y huella SHA-256 de la base reconstruida.

## Preparación

Instalar Python 3.10 o superior y ejecutar:

```bash
pip install -r requirements.txt
```

Crear la carpeta `reportes_pdf` en la raíz del repositorio y colocar allí los 60 PDF. Los nombres deben permitir identificar los reportes 203–262.

## Ejecución completa

```bash
python pipeline_fase1_unificado.py \
  --pdf-dir reportes_pdf \
  --decisiones PARES_CASOS_REVISAR.csv \
  --out-dir resultados_nueva_ejecucion
```

La ejecución genera una base final nueva en Excel y CSV. No compara ni valida automáticamente los resultados contra ejecuciones anteriores; cualquier comparación se realiza manualmente.

## Reanudación desde el resultado del scraping

Si ya se generó el Excel consolidado del scraping, se puede evitar la lectura de los 60 PDF:

```bash
python pipeline_fase1_unificado.py \
  --entrada-scraping FASE1_scraping_conflictos_sociales_2021_2025_solo_hechos.xlsx \
  --decisiones PARES_CASOS_REVISAR.csv \
  --out-dir resultados_nueva_ejecucion
```

Al finalizar, los archivos principales se encuentran en:

- `resultados_nueva_ejecucion/FASE1_MINERIA_CON_IDS_ACTORES_Y_CASOS.xlsx`
- `resultados_nueva_ejecucion/FASE1_MINERIA_CON_IDS_ACTORES_Y_CASOS.csv`

## Resultado validado

| Indicador | Cantidad |
|---|---:|
| Registros de la base final | 21 327 |
| Actores normalizados | 802 |
| Conflictos longitudinales | 146 |
| Periodos mensuales | 60 |
| Vínculos automáticos de casos | 221 |
| Decisiones manuales aplicadas | 39 |
| Pares pendientes de revisión | 0 |
| Relaciones mensuales únicas | 20 913 |

Los 146 identificadores de conflicto son asignados por el código. La revisión manual no asigna los IDs: únicamente resuelve los 39 pares dudosos antes de que el algoritmo forme los componentes finales y genere los códigos `CAS-0001`, `CAS-0002`, etc.


