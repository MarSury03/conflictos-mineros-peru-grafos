# Análisis evolutivo de actores y conflictos mineros

Código Python independiente para analizar las redes actor–conflicto del periodo 2021–2025. Conserva los procedimientos y gráficos Plotly del notebook analítico.

## Ejecución

1. Colocar `Base_conflictos.xlsx` en la misma carpeta que `analisis_redes_mineras.py`.
2. Instalar las dependencias:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Ejecutar:

   ```powershell
   python analisis_redes_mineras.py
   ```

Hoja de entrada: `CONFLICTOS_MINERIA_2021_2025`. Los resultados se guardan en `resultados_redes/`, con tablas CSV, redes serializadas, verificaciones y gráficos HTML interactivos.

El programa no requiere Jupyter ni Streamlit. Las figuras HTML se abren en el navegador. Los resultados dependen de la base suministrada. Para los escenarios de sensibilidad, las instituciones deben estar identificadas de forma unívoca en la columna `Actor_normalizado`.
