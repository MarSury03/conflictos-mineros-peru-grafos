# Guía práctica: crear y llenar el repositorio en GitHub

## 1. Datos para copiar al crear el repositorio

**Repository name**: `conflictos-mineros-peru-redes`

**Description** (campo corto de GitHub):

`Código, datos derivados, grafos, métricas y visualizaciones de una investigación sobre conflictos mineros en el Perú (2021–2025).`

**Visibility**: `Private` al inicio; evaluar publicación pública después de revisar datos, autorías y permisos.

**README**: ya está incluido en esta plantilla. Si subes la carpeta completa, evita generar otro README distinto que origine un conflicto.

**.gitignore**: usa el que viene en la plantilla; revisa sus reglas antes de incorporar archivos públicos.

**License**: `None` de momento, hasta definir permisos con coautores e institución.

**Topics** (opcionales): `python`, `network-analysis`, `social-conflicts`, `mining`, `peru`, `graph-theory`, `longitudinal-analysis`.

## 2. Crear el repositorio

1. Inicia sesión en https://github.com/.
2. Ingresa a https://github.com/new.
3. Pega el nombre y la descripción anteriores.
4. Marca **Private**.
5. Si vas a subir el contenido de esta plantilla, puedes dejar **Add a README file** desactivado (la plantilla ya tiene uno).
6. Presiona **Create repository**.

## 3. Subir la plantilla (método sencillo desde navegador)

1. Descarga el ZIP entregado en la conversación y descomprímelo.
2. Abre tu repositorio recién creado.
3. Elige **Add file → Upload files**.
4. Arrastra los archivos y carpetas contenidos **dentro** de la carpeta `conflictos-mineros-peru-redes`.
5. Verifica que `README.md` esté en la raíz del repositorio.
6. Confirma con **Commit changes**.

**Advertencia:** la interfaz web puede omitir archivos ocultos o carpetas si no se seleccionan correctamente. Comprueba la presencia de `.gitignore` y de las carpetas de la plantilla; si no aparecen, usa GitHub Desktop o Git.

## 4. Alternativa recomendada: GitHub Desktop

1. Instala GitHub Desktop desde https://desktop.github.com/ e inicia sesión.
2. Descomprime el ZIP en tu computadora.
3. En GitHub Desktop, elige **File → Add local repository**. Si indica que todavía no es un repositorio Git, elige la opción de crearlo en esa carpeta.
4. Realiza el primer commit.
5. Publica el repositorio con **Publish repository**, marcando **Keep this code private**. Si ya creaste un repositorio remoto vacío, vincúlalo conforme a las opciones disponibles en Desktop en lugar de publicar otro con el mismo nombre.
6. Para actualizarlo después: copia tus archivos en las carpetas → revisa cambios → **Commit to main** → **Push origin**.

## 5. Cómo colocar archivos reales

| Archivo/resultado real | Destino recomendado |
|---|---|
| Script de scraping de PDF | `src/fase1_base_longitudinal/` |
| Script de limpieza y selección minera | `src/fase1_base_longitudinal/` |
| Script de normalización de actores y casos | `src/fase1_base_longitudinal/` |
| PDF originales de la Defensoría | `data/01_original/` (local, no subir por defecto) |
| Excel y CSV intermedios | `data/02_intermedia/` (local por defecto) |
| Relación mensual definitiva | `data/03_final/` (comprobar antes de publicar) |
| Maestros de actores y conflictos | `data/03_final/` (revisar datos identificables) |
| Script para crear redes y proyecciones | `src/fase2_construccion_redes/` |
| Redes .graphml | `grafos/` bajo el subdirectorio correspondiente |
| Excel resumen de OE2 | `resultados/oe2_redes/` |
| Script de centralidades y comunidades | `src/fase3_metricas_comunidades/` |
| Tablas de métricas | `resultados/oe3_metricas/` |
| Script temporal y gráficos de Jaccard | `src/fase4_evolucion_temporal/` |
| Tablas temporales | `resultados/oe4_evolucion/` |
| Script de validación y sensibilidad | `src/fase5_validacion_sensibilidad/` |
| Tablas de pruebas y sensibilidad | `resultados/oe5_validacion/` |
| Imágenes de redes para la tesis | `figuras/visualizaciones_redes/` |
| Diagramas del proceso | `figuras/diagramas_metodologia/` |
| Figuras de evolución temporal | `figuras/graficos_temporales/` |

**Consejo de nombres:** evita `final2.py`, `final_final.xlsx` o `nuevo (3).csv`. Utiliza nombres claros y fechas o versiones únicamente cuando haga falta documentar ejecuciones diferentes.

## 6. Qué conservar fuera del repositorio público

- Archivos PDF originales pesados, salvo que su publicación sea apropiada y permitida.
- Información con datos personales, archivos con acceso restringido, archivos de configuración con contraseñas o tokens.
- Entornos virtuales (`.venv`), `__pycache__`, archivos temporales y exportaciones repetidas.
- Archivos grandes por encima de límites habituales de GitHub (100 MB por archivo para Git regular); evaluar Git LFS u otro repositorio de datos.

**Importante:** `.gitignore` evita agregar accidentalmente archivos no rastreados, pero **no elimina archivos ya subidos**. Si un archivo sensible llegó al historial, quitarlo del último commit no garantiza su eliminación de versiones anteriores.

## 7. Verificaciones antes de compartir

- [ ] `README.md` describe correctamente el objetivo y las fuentes.
- [ ] Los scripts definitivos están organizados por fase.
- [ ] Los nombres de archivos/rutas coinciden con los que usa el código.
- [ ] `requirements.txt` refleja el entorno efectivo.
- [ ] Las salidas de cada fase están separadas por objetivo.
- [ ] Los gráficos incluidos tienen el script o procedimiento que los produce.
- [ ] Las tablas y los resultados finales se pueden relacionar con una ejecución.
- [ ] La documentación diferencia validaciones ejecutadas de las pendientes.
- [ ] No se subieron archivos personales, claves, documentos restringidos ni binarios innecesarios.
- [ ] El equipo acordó visibilidad, licencia y reglas de uso.
