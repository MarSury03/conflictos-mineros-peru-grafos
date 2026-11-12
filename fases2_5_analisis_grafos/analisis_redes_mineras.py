"""Análisis longitudinal de redes actor–conflicto (2021–2025)."""

from pathlib import Path

import os

os.chdir(Path(__file__).resolve().parent)


# Preparación de datos
from pathlib import Path
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
RUTA_EXCEL = Path('Base_conflictos.xlsx')
HOJA = 'FASE1_MINERIA_CON_IDS_ACTORES_Y'
CARPETA_RESULTADOS = Path('resultados_redes')
CARPETA_GRAFOS = CARPETA_RESULTADOS / 'grafos'
CARPETA_TABLAS = CARPETA_RESULTADOS / 'tablas'
CARPETA_VALIDACIONES = CARPETA_RESULTADOS / 'validaciones'
CARPETA_GRAFICOS = CARPETA_RESULTADOS / 'graficos'
for carpeta in (CARPETA_GRAFOS, CARPETA_TABLAS, CARPETA_VALIDACIONES, CARPETA_GRAFICOS):
    carpeta.mkdir(parents=True, exist_ok=True)
if not RUTA_EXCEL.is_file():
    raise FileNotFoundError(f'No se encontró {RUTA_EXCEL.resolve()}')
df = pd.read_excel(RUTA_EXCEL, sheet_name=HOJA)
columnas_requeridas = ['periodo_reporte', 'id_caso', 'Id_actor', 'nombre_caso', 'Actor_normalizado']
faltantes = sorted(set(columnas_requeridas) - set(df.columns))
if faltantes:
    raise ValueError(f'Columnas faltantes: {faltantes}')
filas_iniciales = len(df)
df['periodo_reporte'] = pd.to_datetime(df['periodo_reporte'], errors='coerce').dt.to_period('M').astype('string')
for columna in ('id_caso', 'Id_actor', 'nombre_caso', 'Actor_normalizado'):
    df[columna] = df[columna].astype('string').str.strip()
for columna in ('periodo_reporte', 'id_caso', 'Id_actor'):
    if df[columna].isna().any() or df[columna].eq('').any():
        raise ValueError(f'Existen valores vacíos en {columna}')
clave = ['periodo_reporte', 'id_caso', 'Id_actor']
registros_repetidos = int(df.duplicated(clave).sum())
df_limpio = df.drop_duplicates().copy()
relaciones = df_limpio[columnas_requeridas].drop_duplicates(clave).copy()
relaciones = relaciones.sort_values(clave).reset_index(drop=True)
resumen_base = pd.DataFrame([{'filas_entrada': filas_iniciales, 'duplicados_por_clave': registros_repetidos, 'relaciones_mensuales_unicas': len(relaciones), 'actores': relaciones['Id_actor'].nunique(), 'conflictos': relaciones['id_caso'].nunique(), 'meses': relaciones['periodo_reporte'].nunique()}])
resumen_base.to_csv(CARPETA_TABLAS / 'resumen_base_longitudinal.csv', index=False, encoding='utf-8-sig')


# Construcción de redes bipartitas
import pandas as pd
import networkx as nx
from pathlib import Path
import pickle
CARPETA_RESULTADOS = Path('resultados_redes')
CARPETA_GRAFOS = CARPETA_RESULTADOS / 'grafos'
CARPETA_TABLAS = CARPETA_RESULTADOS / 'tablas'
CARPETA_VALIDACIONES = CARPETA_RESULTADOS / 'validaciones'
CARPETA_GRAFICOS = CARPETA_RESULTADOS / 'graficos'
for carpeta in [CARPETA_GRAFOS, CARPETA_TABLAS, CARPETA_VALIDACIONES, CARPETA_GRAFICOS]:
    carpeta.mkdir(parents=True, exist_ok=True)
relaciones_red = relaciones[['periodo_reporte', 'id_caso', 'Id_actor', 'nombre_caso', 'Actor_normalizado']].drop_duplicates(subset=['periodo_reporte', 'id_caso', 'Id_actor']).copy()
relaciones_red['periodo_reporte'] = relaciones_red['periodo_reporte'].astype(str)
relaciones_red['año'] = relaciones_red['periodo_reporte'].str[:4]
relaciones_anuales = relaciones_red.groupby(['año', 'id_caso', 'Id_actor'], as_index=False).agg(meses_activos=('periodo_reporte', 'nunique'), nombre_caso=('nombre_caso', 'first'), Actor_normalizado=('Actor_normalizado', 'first'))
relaciones_historicas = relaciones_red.groupby(['id_caso', 'Id_actor'], as_index=False).agg(meses_activos=('periodo_reporte', 'nunique'), nombre_caso=('nombre_caso', 'first'), Actor_normalizado=('Actor_normalizado', 'first'))

def construir_grafo_bipartito(tabla_relaciones):
    G = nx.Graph()
    for fila in tabla_relaciones.itertuples(index=False):
        actor = ('actor', fila.Id_actor)
        caso = ('caso', fila.id_caso)
        G.add_node(actor, tipo='actor', codigo=fila.Id_actor, etiqueta=fila.Actor_normalizado)
        G.add_node(caso, tipo='caso', codigo=fila.id_caso, etiqueta=fila.nombre_caso)
        atributos_arista = {}
        if hasattr(fila, 'meses_activos'):
            atributos_arista['meses_activos'] = int(fila.meses_activos)
        G.add_edge(actor, caso, **atributos_arista)
    return G
grafos_bipartitos = {}
for periodo, tabla in relaciones_red.groupby('periodo_reporte'):
    grafos_bipartitos[periodo] = construir_grafo_bipartito(tabla)
grafos_bipartitos_anuales = {}
for año, tabla in relaciones_anuales.groupby('año'):
    grafos_bipartitos_anuales[año] = construir_grafo_bipartito(tabla)
grafo_bipartito_historico = construir_grafo_bipartito(relaciones_historicas)
print('Redes mensuales:', len(grafos_bipartitos))
print('Redes anuales:', len(grafos_bipartitos_anuales))
print('Nodos de la red histórica:', grafo_bipartito_historico.number_of_nodes())
print('Aristas de la red histórica:', grafo_bipartito_historico.number_of_edges())


# Resumen y validación de redes bipartitas
def resumir_y_validar_red(nombre, G, tabla_relaciones):
    actores = [n for n, d in G.nodes(data=True) if d['tipo'] == 'actor']
    casos = [n for n, d in G.nodes(data=True) if d['tipo'] == 'caso']
    aristas_correctas = all((G.nodes[u]['tipo'] != G.nodes[v]['tipo'] for u, v in G.edges()))
    conteo_aristas_coincide = G.number_of_edges() == len(tabla_relaciones)
    return {'red': nombre, 'n_actores': len(actores), 'n_casos': len(casos), 'n_nodos': G.number_of_nodes(), 'n_aristas': G.number_of_edges(), 'n_componentes': nx.number_connected_components(G), 'es_bipartita': nx.is_bipartite(G), 'aristas_actor_caso': aristas_correctas, 'conteo_aristas_coincide': conteo_aristas_coincide}
resumen_redes = []
validaciones_redes = []
for periodo, G in grafos_bipartitos.items():
    tabla = relaciones_red[relaciones_red['periodo_reporte'] == periodo]
    resumen_redes.append(resumir_y_validar_red(f'mensual_{periodo}', G, tabla))
for año, G in grafos_bipartitos_anuales.items():
    tabla = relaciones_anuales[relaciones_anuales['año'] == año]
    resumen_redes.append(resumir_y_validar_red(f'anual_{año}', G, tabla))
resumen_redes.append(resumir_y_validar_red('historica_2021_2025', grafo_bipartito_historico, relaciones_historicas))
resumen_redes = pd.DataFrame(resumen_redes)
columnas_validacion = ['red', 'es_bipartita', 'aristas_actor_caso', 'conteo_aristas_coincide']
validaciones_redes = resumen_redes[columnas_validacion].copy()
relaciones_anuales.to_csv(CARPETA_TABLAS / 'relaciones_unicas_anuales.csv', index=False, encoding='utf-8-sig')
relaciones_historicas.to_csv(CARPETA_TABLAS / 'relaciones_unicas_historicas.csv', index=False, encoding='utf-8-sig')
resumen_redes.to_csv(CARPETA_TABLAS / 'resumen_redes_bipartitas.csv', index=False, encoding='utf-8-sig')
validaciones_redes.to_csv(CARPETA_VALIDACIONES / 'validaciones_redes_bipartitas.csv', index=False, encoding='utf-8-sig')
with open(CARPETA_GRAFOS / 'grafos_bipartitos_mensuales.pkl', 'wb') as f:
    pickle.dump(grafos_bipartitos, f)
with open(CARPETA_GRAFOS / 'grafos_bipartitos_anuales.pkl', 'wb') as f:
    pickle.dump(grafos_bipartitos_anuales, f)
with open(CARPETA_GRAFOS / 'grafo_bipartito_historico.pkl', 'wb') as f:
    pickle.dump(grafo_bipartito_historico, f)
print('Todas las validaciones aprobadas:', validaciones_redes[['es_bipartita', 'aristas_actor_caso', 'conteo_aristas_coincide']].all().all())
print('Tablas, validaciones y grafos guardados en:', CARPETA_RESULTADOS.resolve())


# Visualización de muestras bipartitas
import plotly.graph_objects as go

def graficar_muestra_bipartita(G, titulo, archivo_html, n_actores=10, n_casos=5):
    actores = sorted([n for n, d in G.nodes(data=True) if d['tipo'] == 'actor'], key=lambda n: G.degree(n), reverse=True)[:n_actores]
    casos = sorted([n for n, d in G.nodes(data=True) if d['tipo'] == 'caso'], key=lambda n: G.degree(n), reverse=True)[:n_casos]
    G_muestra = G.subgraph(actores + casos).copy()
    actores_muestra = sorted([n for n in G_muestra.nodes if n[0] == 'actor'], key=lambda n: n[1])
    casos_muestra = sorted([n for n in G_muestra.nodes if n[0] == 'caso'], key=lambda n: n[1])
    pos = {}
    for i, nodo in enumerate(actores_muestra):
        y = i / max(len(actores_muestra) - 1, 1)
        pos[nodo] = (0, 1 - y)
    for i, nodo in enumerate(casos_muestra):
        y = i / max(len(casos_muestra) - 1, 1)
        pos[nodo] = (1, 1 - y)
    edge_x, edge_y = ([], [])
    for u, v in G_muestra.edges():
        edge_x.extend([pos[u][0], pos[v][0], None])
        edge_y.extend([pos[u][1], pos[v][1], None])
    traza_aristas = go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(color='#B8C2CE', width=1), hoverinfo='skip', name='Relación actor–caso')

    def traza_nodos(nodos, tipo):
        codigos = [G_muestra.nodes[n]['codigo'] for n in nodos]
        grados = [G_muestra.degree(n) for n in nodos]
        return go.Scatter(x=[pos[n][0] for n in nodos], y=[pos[n][1] for n in nodos], mode='markers+text', text=codigos, textposition='middle left' if tipo == 'actor' else 'middle right', textfont=dict(size=11, color='#1F2937'), marker=dict(size=[10 + 2 * grado for grado in grados], color='#2563EB' if tipo == 'actor' else '#EA580C', symbol='circle' if tipo == 'actor' else 'square', line=dict(width=0.5, color='white')), customdata=[[G_muestra.nodes[n]['etiqueta'], G_muestra.degree(n)] for n in nodos], hovertemplate='Código: %{text}<br>Nombre: %{customdata[0]}<br>Grado en la muestra: %{customdata[1]}<extra></extra>', name='Actores' if tipo == 'actor' else 'Casos')
    fig = go.Figure(data=[traza_aristas, traza_nodos(actores_muestra, 'actor'), traza_nodos(casos_muestra, 'caso')])
    fig.update_layout(title=f'{titulo}<br><sup>Muestra: {len(actores_muestra)} actores y {len(casos_muestra)} casos · {G_muestra.number_of_edges()} relaciones · códigos visibles</sup>', template='plotly_white', showlegend=True, xaxis=dict(tickvals=[0, 1], ticktext=['Actores', 'Casos'], range=[-0.25, 1.25], showgrid=False, zeroline=False), yaxis=dict(visible=False, showgrid=False, zeroline=False), margin=dict(l=120, r=120, t=100, b=50), height=900)
    ruta = CARPETA_GRAFICOS / archivo_html
    fig.write_html(ruta, include_plotlyjs=True)
    print('HTML guardado en:', ruta.resolve())
    print('Relaciones en la muestra:', G_muestra.number_of_edges())
graficar_muestra_bipartita(grafos_bipartitos[sorted(grafos_bipartitos)[0]], 'Red bipartita actor–caso — 2021-01', 'red_bipartita_muestra_2021-01.html')
graficar_muestra_bipartita(grafos_bipartitos_anuales[sorted(grafos_bipartitos_anuales)[0]], 'Red bipartita actor–caso — 2021', 'red_bipartita_muestra_2021_anual.html')
graficar_muestra_bipartita(grafo_bipartito_historico, 'Red bipartita actor–caso — histórica 2021–2025', 'red_bipartita_muestra_historica_2021-2025.html')


# Proyecciones ponderadas
import pandas as pd
import networkx as nx
from pathlib import Path
from itertools import combinations
CARPETA_RESULTADOS = Path('resultados_redes')
CARPETA_TABLAS = CARPETA_RESULTADOS / 'tablas'
CARPETA_VALIDACIONES = CARPETA_RESULTADOS / 'validaciones'
CARPETA_GRAFOS = CARPETA_RESULTADOS / 'grafos'
for carpeta in [CARPETA_TABLAS, CARPETA_VALIDACIONES, CARPETA_GRAFOS]:
    carpeta.mkdir(parents=True, exist_ok=True)
redes_bipartitas = {}
redes_bipartitas.update({f'mensual_{periodo}': G for periodo, G in grafos_bipartitos.items()})
redes_bipartitas.update({f'anual_{año}': G for año, G in grafos_bipartitos_anuales.items()})
redes_bipartitas['historica_2021_2025'] = grafo_bipartito_historico

def proyectar_red_bipartita(G, tipo_proyeccion):
    """
    Proyecta una red bipartita sobre actores o sobre casos.

    Actor–actor:
        peso = número de casos compartidos.

    Caso–caso:
        peso = número de actores compartidos.
    """
    if tipo_proyeccion not in ['actor', 'caso']:
        raise ValueError("tipo_proyeccion debe ser 'actor' o 'caso'.")
    tipo_contraparte = 'caso' if tipo_proyeccion == 'actor' else 'actor'
    nodos = [n for n, datos in G.nodes(data=True) if datos.get('tipo') == tipo_proyeccion]
    G_proyectado = nx.Graph()
    for nodo in nodos:
        G_proyectado.add_node(nodo, tipo=tipo_proyeccion, codigo=G.nodes[nodo].get('codigo', nodo[1]), etiqueta=G.nodes[nodo].get('etiqueta', nodo[1]))
    for nodo_contraparte, datos in G.nodes(data=True):
        if datos.get('tipo') != tipo_contraparte:
            continue
        vecinos_proyectados = [vecino for vecino in G.neighbors(nodo_contraparte) if G.nodes[vecino].get('tipo') == tipo_proyeccion]
        for nodo_1, nodo_2 in combinations(vecinos_proyectados, 2):
            if G_proyectado.has_edge(nodo_1, nodo_2):
                G_proyectado[nodo_1][nodo_2]['peso'] += 1
            else:
                G_proyectado.add_edge(nodo_1, nodo_2, peso=1)
    return G_proyectado

def resumen_grafo_proyectado(nombre_red, tipo_proyeccion, G):
    return {'red': nombre_red, 'proyeccion': tipo_proyeccion, 'n_nodos': G.number_of_nodes(), 'n_aristas': G.number_of_edges(), 'n_componentes': nx.number_connected_components(G) if G.number_of_nodes() > 0 else 0, 'peso_total': sum((datos['peso'] for _, _, datos in G.edges(data=True))), 'peso_minimo': min((datos['peso'] for _, _, datos in G.edges(data=True)), default=0), 'peso_maximo': max((datos['peso'] for _, _, datos in G.edges(data=True)), default=0)}
proyecciones_actores = {}
proyecciones_casos = {}
resumen_proyecciones = []
validaciones_proyecciones = []
for nombre_red, G_bipartita in redes_bipartitas.items():
    G_actores = proyectar_red_bipartita(G_bipartita, 'actor')
    G_casos = proyectar_red_bipartita(G_bipartita, 'caso')
    proyecciones_actores[nombre_red] = G_actores
    proyecciones_casos[nombre_red] = G_casos
    resumen_proyecciones.append(resumen_grafo_proyectado(nombre_red, 'actor_actor', G_actores))
    resumen_proyecciones.append(resumen_grafo_proyectado(nombre_red, 'caso_caso', G_casos))
    pesos_actores_validos = all((isinstance(datos.get('peso'), int) and datos['peso'] > 0 for _, _, datos in G_actores.edges(data=True)))
    pesos_casos_validos = all((isinstance(datos.get('peso'), int) and datos['peso'] > 0 for _, _, datos in G_casos.edges(data=True)))
    nodos_actores_validos = all((datos.get('tipo') == 'actor' for _, datos in G_actores.nodes(data=True)))
    nodos_casos_validos = all((datos.get('tipo') == 'caso' for _, datos in G_casos.nodes(data=True)))
    validaciones_proyecciones.append({'red': nombre_red, 'proyeccion': 'actor_actor', 'nodos_tipo_correcto': nodos_actores_validos, 'pesos_enteros_positivos': pesos_actores_validos, 'sin_aristas_autorreferentes': nx.number_of_selfloops(G_actores) == 0})
    validaciones_proyecciones.append({'red': nombre_red, 'proyeccion': 'caso_caso', 'nodos_tipo_correcto': nodos_casos_validos, 'pesos_enteros_positivos': pesos_casos_validos, 'sin_aristas_autorreferentes': nx.number_of_selfloops(G_casos) == 0})
resumen_proyecciones = pd.DataFrame(resumen_proyecciones)
validaciones_proyecciones = pd.DataFrame(validaciones_proyecciones)
resumen_proyecciones.to_csv(CARPETA_TABLAS / 'resumen_proyecciones_mensuales_anuales_historica.csv', index=False, encoding='utf-8-sig')
validaciones_proyecciones.to_csv(CARPETA_VALIDACIONES / 'validaciones_proyecciones.csv', index=False, encoding='utf-8-sig')

def guardar_grafo_graphml(G, ruta):
    H = nx.Graph()
    for nodo, datos in G.nodes(data=True):
        H.add_node(str(nodo), **{clave: str(valor) for clave, valor in datos.items()})
    for u, v, datos in G.edges(data=True):
        H.add_edge(str(u), str(v), **{clave: int(valor) for clave, valor in datos.items()})
    nx.write_graphml(H, ruta)
for nombre_red, G in proyecciones_actores.items():
    guardar_grafo_graphml(G, CARPETA_GRAFOS / f'{nombre_red}_proyeccion_actor_actor.graphml')
for nombre_red, G in proyecciones_casos.items():
    guardar_grafo_graphml(G, CARPETA_GRAFOS / f'{nombre_red}_proyeccion_caso_caso.graphml')
print('Redes bipartitas procesadas:', len(redes_bipartitas))
print('Proyecciones actor–actor:', len(proyecciones_actores))
print('Proyecciones caso–caso:', len(proyecciones_casos))
print('Todas las validaciones aprobadas:', validaciones_proyecciones[['nodos_tipo_correcto', 'pesos_enteros_positivos', 'sin_aristas_autorreferentes']].all().all())
print('Resúmenes, validaciones y grafos proyectados guardados.')


# Configuración de muestras proyectadas
import plotly.graph_objects as go
import networkx as nx
from pathlib import Path
CARPETA_GRAFICOS = CARPETA_RESULTADOS / 'graficos'
CARPETA_GRAFICOS.mkdir(parents=True, exist_ok=True)
periodo_ejemplo = '2021-01'
nombre_red = f'mensual_{periodo_ejemplo}'
G_actores = proyecciones_actores[nombre_red]
G_casos = proyecciones_casos[nombre_red]
print('Proyección actor–actor:', G_actores.number_of_nodes(), 'nodos y', G_actores.number_of_edges(), 'aristas')
print('Proyección caso–caso:', G_casos.number_of_nodes(), 'nodos y', G_casos.number_of_edges(), 'aristas')


# Visualización de proyecciones
def graficar_proyeccion(G, titulo, subtitulo, tipo, archivo_salida, cantidad_nodos=30):
    nodos_seleccionados = sorted([n for n in G.nodes()], key=lambda n: G.degree(n), reverse=True)[:cantidad_nodos]
    G_muestra = G.subgraph(nodos_seleccionados).copy()
    if G_muestra.number_of_nodes() == 0:
        print(f'No hay nodos para graficar: {titulo}')
        return
    pos = nx.spring_layout(G_muestra, seed=42, weight='peso', k=1.2, iterations=150)
    edge_x, edge_y = ([], [])
    for u, v in G_muestra.edges():
        edge_x.extend([pos[u][0], pos[v][0], None])
        edge_y.extend([pos[u][1], pos[v][1], None])
    traza_aristas = go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(color='#AAB7C4', width=1), hoverinfo='skip', name='Relaciones')
    x_nodos = [pos[n][0] for n in G_muestra.nodes()]
    y_nodos = [pos[n][1] for n in G_muestra.nodes()]
    codigos = [G_muestra.nodes[n].get('codigo', n[1]) for n in G_muestra.nodes()]
    grados = [G_muestra.degree(n) for n in G_muestra.nodes()]
    nombres = [G_muestra.nodes[n].get('etiqueta', n[1]) for n in G_muestra.nodes()]
    tamanos = [12 + 3 * grado for grado in grados]
    traza_nodos = go.Scatter(x=x_nodos, y=y_nodos, mode='markers+text', text=codigos, textposition='top center', textfont=dict(size=11, color='#1F2937'), marker=dict(size=tamanos, color='#2563EB' if tipo == 'actor' else '#EA580C', line=dict(width=1, color='white')), customdata=list(zip(nombres, grados)), hovertemplate='Código: %{text}<br>Nombre: %{customdata[0]}<br>Grado: %{customdata[1]}<extra></extra>', name='Actores' if tipo == 'actor' else 'Casos')
    fig = go.Figure(data=[traza_aristas, traza_nodos])
    for u, v, datos in G_muestra.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        fig.add_shape(type='line', x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color='#AAB7C4', width=min(1 + datos['peso'] * 0.5, 5)), layer='below')
    fig.update_layout(title=f'{titulo}<br><sup>{subtitulo} | Muestra: {G_muestra.number_of_nodes()} nodos y {G_muestra.number_of_edges()} relaciones</sup>', template='plotly_white', showlegend=True, xaxis=dict(visible=False), yaxis=dict(visible=False), margin=dict(l=80, r=80, t=100, b=60), height=850, hovermode='closest')
    fig.write_html(archivo_salida, include_plotlyjs=True)
    print('Gráfico guardado:', archivo_salida)
    print('Nodos en la muestra:', G_muestra.number_of_nodes())
    print('Aristas en la muestra:', G_muestra.number_of_edges())


# Muestras de proyecciones
graficar_proyeccion(G=G_actores, titulo='Proyección actor–actor — 2021-01', subtitulo='Peso: número de casos compartidos', tipo='actor', archivo_salida=CARPETA_GRAFICOS / 'proyeccion_actor_actor_muestra_2021_01.html', cantidad_nodos=30)
graficar_proyeccion(G=G_casos, titulo='Proyección caso–caso — 2021-01', subtitulo='Peso: número de actores compartidos', tipo='caso', archivo_salida=CARPETA_GRAFICOS / 'proyeccion_caso_caso_muestra_2021_01.html', cantidad_nodos=30)
print('\nGráficos HTML del Bloque 2 generados correctamente.')


# Indicadores estructurales
import pandas as pd
import networkx as nx
from pathlib import Path
CARPETA_RESULTADOS = Path('resultados_redes')
CARPETA_TABLAS = CARPETA_RESULTADOS / 'tablas'
CARPETA_VALIDACIONES = CARPETA_RESULTADOS / 'validaciones'
for carpeta in [CARPETA_TABLAS, CARPETA_VALIDACIONES]:
    carpeta.mkdir(parents=True, exist_ok=True)
redes_metricas = {}
for nombre, G in redes_bipartitas.items():
    redes_metricas[nombre] = {'grafo': G, 'tipo_red': 'bipartita', 'ponderada': False}
for nombre, G in proyecciones_actores.items():
    redes_metricas[nombre + '_proyeccion_actor_actor'] = {'grafo': G, 'tipo_red': 'proyeccion_actor_actor', 'ponderada': True}
for nombre, G in proyecciones_casos.items():
    redes_metricas[nombre + '_proyeccion_caso_caso'] = {'grafo': G, 'tipo_red': 'proyeccion_caso_caso', 'ponderada': True}

def calcular_metricas_red(G, tipo_red, nombre_red):
    n_nodos = G.number_of_nodes()
    n_aristas = G.number_of_edges()
    grados = dict(G.degree())
    grado_total = sum(grados.values())
    if n_nodos > 0:
        componentes = list(nx.connected_components(G))
        n_componentes = len(componentes)
        tam_componente_mayor = max((len(c) for c in componentes))
    else:
        componentes = []
        n_componentes = 0
        tam_componente_mayor = 0
    if tipo_red == 'bipartita':
        n_actores = sum((1 for _, d in G.nodes(data=True) if d.get('tipo') == 'actor'))
        n_casos = sum((1 for _, d in G.nodes(data=True) if d.get('tipo') == 'caso'))
        max_aristas_posibles = n_actores * n_casos
        densidad = n_aristas / max_aristas_posibles if max_aristas_posibles > 0 else 0
    else:
        n_actores = None
        n_casos = None
        max_aristas_posibles = n_nodos * (n_nodos - 1) / 2
        densidad = nx.density(G) if n_nodos > 1 else 0
    if tipo_red.startswith('proyeccion'):
        fuerzas = dict(G.degree(weight='peso'))
        fuerza_total_nodos = sum(fuerzas.values())
        peso_total_aristas = sum((datos.get('peso', 0) for _, _, datos in G.edges(data=True)))
        fuerza_media = sum(fuerzas.values()) / n_nodos if n_nodos > 0 else 0
    else:
        fuerzas = {}
        fuerza_total_nodos = None
        peso_total_aristas = None
        fuerza_media = None
    resumen = {'red': nombre_red, 'tipo_red': tipo_red, 'n_nodos': n_nodos, 'n_aristas': n_aristas, 'n_actores': n_actores, 'n_casos': n_casos, 'max_aristas_posibles': max_aristas_posibles, 'densidad': densidad, 'n_componentes': n_componentes, 'tam_componente_mayor': tam_componente_mayor, 'grado_minimo': min(grados.values(), default=0), 'grado_maximo': max(grados.values(), default=0), 'grado_medio': sum(grados.values()) / n_nodos if n_nodos > 0 else 0, 'suma_grados': grado_total, 'ponderada': tipo_red.startswith('proyeccion'), 'peso_total_aristas': peso_total_aristas, 'fuerza_media_nodo': fuerza_media}
    filas_nodos = []
    for nodo, datos in G.nodes(data=True):
        filas_nodos.append({'red': nombre_red, 'tipo_red': tipo_red, 'codigo': datos.get('codigo', nodo[1] if isinstance(nodo, tuple) else str(nodo)), 'tipo_nodo': datos.get('tipo', tipo_red), 'grado': grados.get(nodo, 0), 'fuerza_ponderada': fuerzas.get(nodo, None), 'etiqueta': datos.get('etiqueta', '')})
    tabla_nodos = pd.DataFrame(filas_nodos)
    distribucion_grados = tabla_nodos.groupby(['grado'], as_index=False).size().rename(columns={'size': 'cantidad_nodos'})
    distribucion_grados.insert(0, 'red', nombre_red)
    distribucion_grados.insert(1, 'tipo_red', tipo_red)
    validaciones = {'red': nombre_red, 'suma_grados_igual_2_aristas': grado_total == 2 * n_aristas, 'densidad_entre_0_y_1': 0 <= densidad <= 1, 'componentes_no_superan_nodos': n_componentes <= n_nodos, 'nodos_tabla_coincide': len(tabla_nodos) == n_nodos, 'distribucion_grados_suma_nodos': distribucion_grados['cantidad_nodos'].sum() == n_nodos}
    if tipo_red.startswith('proyeccion'):
        validaciones['peso_total_coincide_con_fuerzas'] = fuerza_total_nodos == 2 * peso_total_aristas
    return (resumen, tabla_nodos, distribucion_grados, validaciones)
resumenes = []
tablas_nodos = []
distribuciones = []
validaciones = []
for nombre_red, info in redes_metricas.items():
    resumen, nodos, distribucion, validacion = calcular_metricas_red(G=info['grafo'], tipo_red=info['tipo_red'], nombre_red=nombre_red)
    resumenes.append(resumen)
    tablas_nodos.append(nodos)
    distribuciones.append(distribucion)
    validaciones.append(validacion)
resumen_metricas = pd.DataFrame(resumenes)
metricas_por_nodo = pd.concat(tablas_nodos, ignore_index=True)
distribucion_grados = pd.concat(distribuciones, ignore_index=True)
validaciones_metricas = pd.DataFrame(validaciones)
resumen_metricas.to_csv(CARPETA_TABLAS / 'metricas_estructurales_todas_las_redes.csv', index=False, encoding='utf-8-sig')
metricas_por_nodo.to_csv(CARPETA_TABLAS / 'metricas_por_nodo_todas_las_redes.csv', index=False, encoding='utf-8-sig')
distribucion_grados.to_csv(CARPETA_TABLAS / 'distribucion_grados_todas_las_redes.csv', index=False, encoding='utf-8-sig')
validaciones_metricas.to_csv(CARPETA_VALIDACIONES / 'validaciones_metricas_estructurales.csv', index=False, encoding='utf-8-sig')
columnas_control = [columna for columna in validaciones_metricas.columns if columna != 'red']
print('Redes evaluadas:', len(redes_metricas))
print('Tablas por nodo:', len(metricas_por_nodo))
print('Todas las validaciones aprobadas:', validaciones_metricas[columnas_control].all().all())
print('Tablas guardadas en:', CARPETA_TABLAS)
print('Validaciones guardadas en:', CARPETA_VALIDACIONES)


# Centralidades y rankings
import pandas as pd
import networkx as nx
import numpy as np
CARPETA_VALIDACIONES = CARPETA_RESULTADOS / 'validaciones'
CARPETA_TABLAS.mkdir(parents=True, exist_ok=True)
CARPETA_VALIDACIONES.mkdir(parents=True, exist_ok=True)
from pathlib import Path
CARPETA_RESULTADOS = Path('resultados_redes')
CARPETA_TABLAS = CARPETA_RESULTADOS / 'tablas'
redes_por_nivel = {'bipartita_mensual': grafos_bipartitos, 'bipartita_anual': grafos_bipartitos_anuales, 'bipartita_historica': {'2021-2025': grafo_bipartito_historico}, 'actor_actor_mensual': {k.replace('mensual_', ''): G for k, G in proyecciones_actores.items() if k.startswith('mensual_')}, 'actor_actor_anual': {k.replace('anual_', ''): G for k, G in proyecciones_actores.items() if k.startswith('anual_')}, 'actor_actor_historica': {'2021-2025': proyecciones_actores.get('historica_2021_2025')}, 'caso_caso_mensual': {k.replace('mensual_', ''): G for k, G in proyecciones_casos.items() if k.startswith('mensual_')}, 'caso_caso_anual': {k.replace('anual_', ''): G for k, G in proyecciones_casos.items() if k.startswith('anual_')}, 'caso_caso_historica': {'2021-2025': proyecciones_casos.get('historica_2021_2025')}}
redes_por_nivel = {familia: {periodo: G for periodo, G in redes.items() if G is not None} for familia, redes in redes_por_nivel.items()}

def codigo_nodo(nodo):
    """Devuelve ACT-... o CAS-... aunque el nodo sea una tupla."""
    if isinstance(nodo, tuple) and len(nodo) > 1:
        return str(nodo[1])
    return str(nodo)

def calcular_centralidades(G, familia_red):
    """
    Calcula centralidades no ponderadas para todas las redes.
    En proyecciones calcula también fuerza y betweenness ponderada.
    El atributo de peso creado en el Bloque 2 se llama 'peso'.
    """
    if G.number_of_nodes() == 0:
        return pd.DataFrame()
    grado = dict(G.degree())
    grado_normalizado = nx.degree_centrality(G) if G.number_of_nodes() > 1 else {n: 0.0 for n in G.nodes()}
    intermediacion = nx.betweenness_centrality(G, normalized=True)
    cercania = nx.closeness_centrality(G)
    es_proyeccion = 'actor_actor' in familia_red or 'caso_caso' in familia_red
    if es_proyeccion:
        fuerza = {n: sum((float(datos.get('peso', 1)) for _, _, datos in G.edges(n, data=True))) for n in G.nodes()}
        H = G.copy()
        for _, _, datos in H.edges(data=True):
            peso = float(datos.get('peso', 1))
            datos['distancia'] = 1 / peso if peso > 0 else np.inf
        intermediacion_ponderada = nx.betweenness_centrality(H, normalized=True, weight='distancia')
    else:
        fuerza = {n: np.nan for n in G.nodes()}
        intermediacion_ponderada = {n: np.nan for n in G.nodes()}
    filas = []
    for n in G.nodes():
        datos = G.nodes[n]
        codigo = codigo_nodo(n)
        tipo = datos.get('tipo', datos.get('bipartite'))
        if tipo is None:
            tipo = 'actor' if codigo.startswith('ACT-') else 'caso' if codigo.startswith('CAS-') else 'no_identificado'
        filas.append({'nodo': str(n), 'codigo': codigo, 'tipo_nodo': tipo, 'grado': grado[n], 'grado_normalizado': grado_normalizado[n], 'grado_ponderado_fuerza': fuerza[n], 'intermediacion': intermediacion[n], 'intermediacion_ponderada': intermediacion_ponderada[n], 'cercania': cercania[n]})
    return pd.DataFrame(filas)
tablas_centralidad = {}
tablas_ranking = {}
validaciones_centralidad = []
for familia, redes in redes_por_nivel.items():
    for periodo, G in redes.items():
        clave = f'{familia}_{periodo}'
        tabla = calcular_centralidades(G, familia)
        if not tabla.empty:
            tabla.insert(0, 'periodo', str(periodo))
            tabla.insert(0, 'familia_red', familia)
            metrica_principal = 'grado_ponderado_fuerza' if 'actor_actor' in familia or 'caso_caso' in familia else 'grado'
            ranking = tabla.sort_values([metrica_principal, 'intermediacion'], ascending=[False, False]).copy()
            ranking.insert(0, 'puesto', range(1, len(ranking) + 1))
            tablas_centralidad[clave] = tabla
            tablas_ranking[clave] = ranking
        validaciones_centralidad.append({'familia_red': familia, 'periodo': str(periodo), 'nodos_grafo': G.number_of_nodes(), 'nodos_tabla': len(tabla), 'coincide_numero_nodos': G.number_of_nodes() == len(tabla), 'sin_codigos_vacios': tabla['codigo'].notna().all() and tabla['codigo'].astype(str).str.strip().ne('').all() if not tabla.empty else True})
if tablas_centralidad:
    pd.concat(tablas_centralidad.values(), ignore_index=True).to_csv(CARPETA_TABLAS / 'centralidades_todas_las_redes.csv', index=False, encoding='utf-8-sig')
if tablas_ranking:
    pd.concat(tablas_ranking.values(), ignore_index=True).to_csv(CARPETA_TABLAS / 'rankings_todas_las_redes.csv', index=False, encoding='utf-8-sig')
validaciones_centralidad = pd.DataFrame(validaciones_centralidad)
validaciones_centralidad.to_csv(CARPETA_VALIDACIONES / 'validaciones_centralidades.csv', index=False, encoding='utf-8-sig')
print('Redes con centralidades calculadas:', len(tablas_centralidad))
print('Todas las validaciones aprobadas:', validaciones_centralidad[['coincide_numero_nodos', 'sin_codigos_vacios']].all().all())


# Comparación de rankings
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from pathlib import Path
CARPETA_RESULTADOS = Path('resultados_redes')
CARPETA_TABLAS = CARPETA_RESULTADOS / 'tablas'
CARPETA_VALIDACIONES = CARPETA_RESULTADOS / 'validaciones'
CARPETA_GRAFOS = CARPETA_RESULTADOS / 'grafos'
for carpeta in [CARPETA_TABLAS, CARPETA_VALIDACIONES, CARPETA_GRAFOS]:
    carpeta.mkdir(parents=True, exist_ok=True)
comparaciones_ranking = []
for familia, redes in redes_por_nivel.items():
    if 'mensual' not in familia and 'anual' not in familia:
        continue
    rankings_familia = []
    for clave, ranking in tablas_ranking.items():
        if not clave.startswith(familia + '_'):
            continue
        tabla = ranking.copy()
        tabla['periodo'] = tabla['periodo'].astype(str)
        rankings_familia.append(tabla)
    if not rankings_familia:
        continue
    ranking_completo = pd.concat(rankings_familia, ignore_index=True)
    ranking_completo['codigo'] = ranking_completo['codigo'].astype(str)
    for codigo, grupo in ranking_completo.groupby('codigo'):
        grupo = grupo.sort_values('periodo')
        if len(grupo) < 2:
            continue
        puestos = grupo['puesto'].astype(int).tolist()
        periodos = grupo['periodo'].tolist()
        for i in range(1, len(grupo)):
            comparaciones_ranking.append({'familia_red': familia, 'codigo': codigo, 'tipo_nodo': grupo.iloc[i]['tipo_nodo'], 'periodo_anterior': periodos[i - 1], 'periodo_actual': periodos[i], 'puesto_anterior': puestos[i - 1], 'puesto_actual': puestos[i], 'cambio_puesto': puestos[i - 1] - puestos[i]})
comparaciones_ranking = pd.DataFrame(comparaciones_ranking)
ruta_comparaciones = CARPETA_TABLAS / 'comparacion_rankings_entre_periodos.csv'
comparaciones_ranking.to_csv(ruta_comparaciones, index=False, encoding='utf-8-sig')
print('Comparaciones de rankings guardadas:', len(comparaciones_ranking))
presencia_top10 = []
for clave, ranking in tablas_ranking.items():
    familia = clave.rsplit('_', 1)[0]
    if 'mensual' not in familia and 'anual' not in familia:
        continue
    top10 = ranking.loc[ranking['puesto'] <= 10].copy()
    if top10.empty:
        continue
    top10['periodo'] = top10['periodo'].astype(str)
    top10['codigo'] = top10['codigo'].astype(str)
    for _, fila in top10.iterrows():
        presencia_top10.append({'familia_red': familia, 'codigo': fila['codigo'], 'tipo_nodo': fila['tipo_nodo'], 'periodo': fila['periodo'], 'puesto': int(fila['puesto'])})
presencia_top10 = pd.DataFrame(presencia_top10)
if not presencia_top10.empty:
    resumen_top10 = presencia_top10.groupby(['familia_red', 'codigo', 'tipo_nodo'], as_index=False).agg(periodos_en_top10=('periodo', 'nunique'), mejor_puesto=('puesto', 'min'), puesto_promedio=('puesto', 'mean')).sort_values(['familia_red', 'periodos_en_top10', 'mejor_puesto'], ascending=[True, False, True])
else:
    resumen_top10 = pd.DataFrame()
resumen_top10.to_csv(CARPETA_TABLAS / 'recurrencia_nodos_top10.csv', index=False, encoding='utf-8-sig')

def codigo_visible(nodo, datos):
    """Obtiene el código ACT-... o CAS-... desde el nodo o sus atributos."""
    codigo = datos.get('codigo')
    if codigo:
        return str(codigo)
    if isinstance(nodo, tuple) and len(nodo) > 1:
        return str(nodo[1])
    return str(nodo)

def graficar_red_ejemplo(G, familia, periodo, max_nodos=35):
    """
    Grafica una muestra de la red:
    - Bipartita: hasta 15 actores y 15 casos, priorizados por grado.
    - Proyección: hasta 35 nodos, priorizados por fuerza si hay pesos.
    Los códigos se muestran como etiquetas.
    """
    if G.number_of_nodes() == 0:
        print(f'Se omite {familia} — {periodo}: red vacía.')
        return None
    es_bipartita = 'bipartita' in familia
    if es_bipartita:
        actores = [n for n, d in G.nodes(data=True) if d.get('tipo', d.get('bipartite')) == 'actor' or codigo_visible(n, d).startswith('ACT-')]
        casos = [n for n, d in G.nodes(data=True) if d.get('tipo', d.get('bipartite')) == 'caso' or codigo_visible(n, d).startswith('CAS-')]
        actores = sorted(actores, key=lambda n: G.degree(n), reverse=True)[:15]
        casos = sorted(casos, key=lambda n: G.degree(n), reverse=True)[:15]
        nodos_muestra = actores + casos
    else:

        def fuerza_nodo(n):
            return sum((float(datos.get('peso', datos.get('weight', 1))) for _, _, datos in G.edges(n, data=True)))
        nodos_muestra = sorted(G.nodes(), key=fuerza_nodo, reverse=True)[:max_nodos]
    H = G.subgraph(nodos_muestra).copy()
    if H.number_of_nodes() == 0:
        print(f'Se omite {familia} — {periodo}: muestra vacía.')
        return None
    if es_bipartita:
        pos = {}
        actores_muestra = [n for n in H.nodes() if codigo_visible(n, H.nodes[n]).startswith('ACT-')]
        casos_muestra = [n for n in H.nodes() if codigo_visible(n, H.nodes[n]).startswith('CAS-')]
        for i, nodo in enumerate(actores_muestra):
            y = 0.5 if len(actores_muestra) == 1 else i / (len(actores_muestra) - 1)
            pos[nodo] = (0, y)
        for i, nodo in enumerate(casos_muestra):
            y = 0.5 if len(casos_muestra) == 1 else i / (len(casos_muestra) - 1)
            pos[nodo] = (1, y)
    else:
        pos = nx.spring_layout(H, seed=42, weight='peso')
    edge_x, edge_y = ([], [])
    for u, v in H.edges():
        edge_x.extend([pos[u][0], pos[v][0], None])
        edge_y.extend([pos[u][1], pos[v][1], None])
    traza_aristas = go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(color='#AAB4C3', width=1), hoverinfo='skip', name='Relaciones')
    trazas_nodos = []
    tipos = {}
    for n in H.nodes():
        codigo = codigo_visible(n, H.nodes[n])
        if codigo.startswith('ACT-'):
            tipo = 'actor'
        elif codigo.startswith('CAS-'):
            tipo = 'caso'
        else:
            tipo = H.nodes[n].get('tipo', 'nodo')
        tipos.setdefault(tipo, []).append(n)
    for tipo, nodos in tipos.items():
        codigos = [codigo_visible(n, H.nodes[n]) for n in nodos]
        grados = [H.degree(n) for n in nodos]
        if not es_bipartita:
            valores = [sum((float(datos.get('peso', datos.get('weight', 1))) for _, _, datos in H.edges(n, data=True))) for n in nodos]
        else:
            valores = grados
        tamanos = [max(9, min(34, 8 + 2 * v)) for v in valores]
        trazas_nodos.append(go.Scatter(x=[pos[n][0] for n in nodos], y=[pos[n][1] for n in nodos], mode='markers+text', text=codigos, textposition='top center', textfont=dict(size=9, color='#1F2937'), marker=dict(size=tamanos, symbol='circle' if tipo == 'actor' else 'square', line=dict(width=0.5, color='white')), customdata=[[grados[i], valores[i]] for i in range(len(nodos))], hovertemplate='Código: %{text}<br>Grado en la muestra: %{customdata[0]}<br>Valor de tamaño: %{customdata[1]}<extra></extra>', name=tipo.capitalize()))
    fig = go.Figure(data=[traza_aristas] + trazas_nodos)
    criterio = 'Muestra: hasta 15 actores y 15 casos con mayor grado' if es_bipartita else f'Muestra: hasta {max_nodos} nodos con mayor fuerza'
    fig.update_layout(title=f"{familia.replace('_', ' ').title()} — {periodo}<br><sup>{criterio}; códigos visibles</sup>", template='plotly_white', showlegend=True, xaxis=dict(visible=es_bipartita, showgrid=False, zeroline=False), yaxis=dict(visible=False, showgrid=False, zeroline=False), margin=dict(l=40, r=40, t=90, b=40), height=800)
    nombre_archivo = f'ejemplo_{familia}_{periodo}'.replace('/', '-')
    ruta_html = CARPETA_GRAFICOS / f'{nombre_archivo}.html'
    fig.write_html(ruta_html, include_plotlyjs=True)
    print('Gráfico guardado en:', ruta_html)
    print('Nodos en la muestra:', H.number_of_nodes())
    print('Aristas en la muestra:', H.number_of_edges())
    return ruta_html
seleccion_graficos = []
for nivel, periodo_preferido in [('mensual', '2021-01'), ('anual', '2021'), ('historica', '2021-2025')]:
    for familia, redes in redes_por_nivel.items():
        if nivel not in familia:
            continue
        if periodo_preferido in redes:
            periodo_elegido = periodo_preferido
        elif redes:
            periodo_elegido = sorted(redes.keys())[0]
        else:
            continue
        seleccion_graficos.append({'familia_red': familia, 'periodo_seleccionado': str(periodo_elegido), 'criterio': 'Periodo representativo por nivel: primer mes disponible, primer año disponible o red histórica acumulada.', 'criterio_muestra': 'Bipartita: hasta 15 actores y 15 casos con mayor grado. Proyección: hasta 35 nodos con mayor fuerza.'})
        graficar_red_ejemplo(redes[periodo_elegido], familia, str(periodo_elegido))
tabla_seleccion_graficos = pd.DataFrame(seleccion_graficos)
tabla_seleccion_graficos.to_csv(CARPETA_TABLAS / 'criterio_seleccion_graficos_bloque4.csv', index=False, encoding='utf-8-sig')
print('Bloque 4 completado: comparaciones, recurrencia y gráficos guardados.')


# Evolución temporal
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
CARPETA_RESULTADOS = Path('resultados_redes')
CARPETA_TABLAS = CARPETA_RESULTADOS / 'tablas'
CARPETA_VALIDACIONES = CARPETA_RESULTADOS / 'validaciones'
CARPETA_GRAFOS = CARPETA_RESULTADOS / 'grafos'
for carpeta in [CARPETA_TABLAS, CARPETA_VALIDACIONES, CARPETA_GRAFOS]:
    carpeta.mkdir(parents=True, exist_ok=True)
columnas_requeridas = ['periodo_reporte', 'id_caso', 'Id_actor']
faltantes = [c for c in columnas_requeridas if c not in relaciones.columns]
if faltantes:
    raise ValueError(f'Faltan columnas en relaciones: {faltantes}')
relaciones_t = relaciones[columnas_requeridas].copy()
relaciones_t['periodo'] = pd.to_datetime(relaciones_t['periodo_reporte'], errors='coerce').dt.to_period('M').astype('string')
for col in ['id_caso', 'Id_actor']:
    relaciones_t[col] = relaciones_t[col].astype('string').str.strip()
n_filas_antes = len(relaciones_t)
relaciones_t = relaciones_t.dropna(subset=['periodo', 'id_caso', 'Id_actor']).copy()
relaciones_t = relaciones_t[relaciones_t['periodo'].str.strip().ne('') & relaciones_t['id_caso'].str.strip().ne('') & relaciones_t['Id_actor'].str.strip().ne('')].copy()
relaciones_t = relaciones_t.drop_duplicates(subset=['periodo', 'id_caso', 'Id_actor']).copy()
periodos = pd.period_range(start=relaciones_t['periodo'].min(), end=relaciones_t['periodo'].max(), freq='M').astype(str).tolist()
if not periodos:
    raise ValueError('No se encontraron periodos válidos para el análisis.')
relaciones_por_mes = {periodo: set(map(tuple, relaciones_t.loc[relaciones_t['periodo'] == periodo, ['id_caso', 'Id_actor']].drop_duplicates().to_numpy())) for periodo in periodos}
periodo_por_relacion = relaciones_t.groupby(['id_caso', 'Id_actor'])['periodo'].agg(primer_mes='min', ultimo_mes='max', meses_activos='nunique').reset_index()
periodo_por_relacion['primer_mes_periodo'] = pd.PeriodIndex(periodo_por_relacion['primer_mes'], freq='M')
periodo_por_relacion['ultimo_mes_periodo'] = pd.PeriodIndex(periodo_por_relacion['ultimo_mes'], freq='M')
periodo_por_relacion['meses_en_intervalo'] = (periodo_por_relacion['ultimo_mes_periodo'].dt.year - periodo_por_relacion['primer_mes_periodo'].dt.year) * 12 + (periodo_por_relacion['ultimo_mes_periodo'].dt.month - periodo_por_relacion['primer_mes_periodo'].dt.month) + 1
periodo_por_relacion['meses_sin_registro_en_intervalo'] = periodo_por_relacion['meses_en_intervalo'] - periodo_por_relacion['meses_activos']
periodo_por_relacion['persistencia_intervalo'] = periodo_por_relacion['meses_activos'] / periodo_por_relacion['meses_en_intervalo']
periodo_por_relacion['proporcion_serie_activa'] = periodo_por_relacion['meses_activos'] / len(periodos)
periodo_por_relacion = periodo_por_relacion.drop(columns=['primer_mes_periodo', 'ultimo_mes_periodo'])
periodo_por_relacion.to_csv(CARPETA_TABLAS / 'duracion_documental_por_relacion.csv', index=False, encoding='utf-8-sig')
resumen_duracion = pd.DataFrame([{'n_relaciones_actor_caso': len(periodo_por_relacion), 'meses_en_serie': len(periodos), 'meses_activos_promedio': periodo_por_relacion['meses_activos'].mean(), 'meses_activos_mediana': periodo_por_relacion['meses_activos'].median(), 'persistencia_intervalo_promedio': periodo_por_relacion['persistencia_intervalo'].mean(), 'relaciones_con_2_o_mas_meses_activos': int((periodo_por_relacion['meses_activos'] >= 2).sum())}])
resumen_duracion.to_csv(CARPETA_TABLAS / 'resumen_duracion_documental.csv', index=False, encoding='utf-8-sig')
transiciones_mensuales = []
for i in range(1, len(periodos)):
    mes_anterior = periodos[i - 1]
    mes_actual = periodos[i]
    conjunto_anterior = relaciones_por_mes[mes_anterior]
    conjunto_actual = relaciones_por_mes[mes_actual]
    interseccion = conjunto_anterior & conjunto_actual
    entradas = conjunto_actual - conjunto_anterior
    salidas = conjunto_anterior - conjunto_actual
    union = conjunto_anterior | conjunto_actual
    jaccard = len(interseccion) / len(union) if union else np.nan
    transiciones_mensuales.append({'mes_anterior': mes_anterior, 'mes_actual': mes_actual, 'relaciones_mes_anterior': len(conjunto_anterior), 'relaciones_mes_actual': len(conjunto_actual), 'persistentes': len(interseccion), 'entradas': len(entradas), 'salidas': len(salidas), 'jaccard': jaccard, 'proporcion_persistente_sobre_anterior': len(interseccion) / len(conjunto_anterior) if conjunto_anterior else np.nan, 'proporcion_persistente_sobre_actual': len(interseccion) / len(conjunto_actual) if conjunto_actual else np.nan})
transiciones_mensuales = pd.DataFrame(transiciones_mensuales)
transiciones_mensuales.to_csv(CARPETA_TABLAS / 'transiciones_mensuales.csv', index=False, encoding='utf-8-sig')
relaciones_t['año'] = relaciones_t['periodo'].str[:4]
años = sorted(relaciones_t['año'].dropna().unique().tolist())
relaciones_por_año = {año: set(map(tuple, relaciones_t.loc[relaciones_t['año'] == año, ['id_caso', 'Id_actor']].drop_duplicates().to_numpy())) for año in años}
transiciones_anuales = []
for i in range(1, len(años)):
    año_anterior = años[i - 1]
    año_actual = años[i]
    conjunto_anterior = relaciones_por_año[año_anterior]
    conjunto_actual = relaciones_por_año[año_actual]
    interseccion = conjunto_anterior & conjunto_actual
    entradas = conjunto_actual - conjunto_anterior
    salidas = conjunto_anterior - conjunto_actual
    union = conjunto_anterior | conjunto_actual
    transiciones_anuales.append({'año_anterior': año_anterior, 'año_actual': año_actual, 'relaciones_año_anterior': len(conjunto_anterior), 'relaciones_año_actual': len(conjunto_actual), 'persistentes_entre_años': len(interseccion), 'entradas': len(entradas), 'salidas': len(salidas), 'jaccard': len(interseccion) / len(union) if union else np.nan})
transiciones_anuales = pd.DataFrame(transiciones_anuales)
transiciones_anuales.to_csv(CARPETA_TABLAS / 'transiciones_anuales.csv', index=False, encoding='utf-8-sig')
continuidad_total = relaciones_t.groupby(['id_caso', 'Id_actor'], as_index=False).agg(meses_activos=('periodo', 'nunique'), años_activos=('año', 'nunique'), primer_mes=('periodo', 'min'), ultimo_mes=('periodo', 'max'))
continuidad_total['presente_en_varios_años'] = continuidad_total['años_activos'] > 1
continuidad_total.to_csv(CARPETA_TABLAS / 'continuidad_relaciones_serie_completa.csv', index=False, encoding='utf-8-sig')
serie_mensual = pd.DataFrame({'periodo': periodos, 'relaciones_documentadas': [len(relaciones_por_mes[p]) for p in periodos]})
if not transiciones_mensuales.empty:
    serie_mensual = serie_mensual.merge(transiciones_mensuales[['mes_actual', 'persistentes', 'entradas', 'salidas', 'jaccard']], left_on='periodo', right_on='mes_actual', how='left').drop(columns=['mes_actual'])
serie_mensual.to_csv(CARPETA_TABLAS / 'serie_temporal_mensual.csv', index=False, encoding='utf-8-sig')
fig_relaciones = go.Figure()
fig_relaciones.add_trace(go.Scatter(x=serie_mensual['periodo'], y=serie_mensual['relaciones_documentadas'], mode='lines+markers', name='Relaciones actor–caso documentadas'))
fig_relaciones.update_layout(title='Evolución mensual de relaciones actor–caso documentadas', xaxis_title='Mes del reporte', yaxis_title='Número de relaciones únicas', template='plotly_white', height=550)
fig_relaciones.write_html(CARPETA_GRAFOS / 'bloque5_serie_relaciones_mensuales.html', include_plotlyjs=True)
if not transiciones_mensuales.empty:
    fig_transiciones = go.Figure()
    for columna, etiqueta in [('entradas', 'Entradas'), ('salidas', 'Salidas'), ('persistentes', 'Persistencias')]:
        fig_transiciones.add_trace(go.Scatter(x=transiciones_mensuales['mes_actual'], y=transiciones_mensuales[columna], mode='lines+markers', name=etiqueta))
    fig_transiciones.update_layout(title='Entradas, salidas y persistencias entre meses consecutivos', xaxis_title='Mes actual de la comparación', yaxis_title='Número de relaciones actor–caso', template='plotly_white', height=550)
    fig_transiciones.write_html(CARPETA_GRAFOS / 'bloque5_transiciones_mensuales.html', include_plotlyjs=True)
if not transiciones_mensuales.empty:
    fig_jaccard = go.Figure()
    fig_jaccard.add_trace(go.Scatter(x=transiciones_mensuales['mes_actual'], y=transiciones_mensuales['jaccard'], mode='lines+markers', name='Jaccard mensual'))
    fig_jaccard.update_layout(title='Similitud de relaciones actor–caso entre meses consecutivos', xaxis_title='Mes actual de la comparación', yaxis_title='Índice de Jaccard (0 a 1)', yaxis=dict(range=[0, 1]), template='plotly_white', height=550)
    fig_jaccard.write_html(CARPETA_GRAFOS / 'bloque5_jaccard_mensual.html', include_plotlyjs=True)
validaciones_temporales = pd.DataFrame([{'filas_relaciones_recibidas': n_filas_antes, 'relaciones_unicas_temporales': len(relaciones_t), 'periodos_mensuales_en_calendario': len(periodos), 'transiciones_mensuales_esperadas': max(len(periodos) - 1, 0), 'transiciones_mensuales_calculadas': len(transiciones_mensuales), 'transiciones_anuales_calculadas': len(transiciones_anuales), 'sin_relaciones_mensuales_duplicadas': all((len(relaciones_por_mes[p]) == len(set(relaciones_por_mes[p])) for p in periodos)), 'jaccard_mensual_en_rango_0_1': transiciones_mensuales['jaccard'].dropna().between(0, 1).all() if not transiciones_mensuales.empty else True, 'jaccard_anual_en_rango_0_1': transiciones_anuales['jaccard'].dropna().between(0, 1).all() if not transiciones_anuales.empty else True}])
validaciones_temporales.to_csv(CARPETA_VALIDACIONES / 'validaciones_bloque5_temporal.csv', index=False, encoding='utf-8-sig')
definiciones_temporales = pd.DataFrame([{'indicador': 'Meses activos', 'definicion': 'Número de meses distintos en que aparece una relación actor–caso.'}, {'indicador': 'Persistencia dentro del intervalo', 'definicion': 'Meses activos divididos entre los meses desde la primera hasta la última aparición, ambos incluidos.'}, {'indicador': 'Entrada mensual', 'definicion': 'Relación actor–caso presente en el mes actual y ausente en el mes anterior.'}, {'indicador': 'Salida mensual', 'definicion': 'Relación actor–caso presente en el mes anterior y ausente en el mes actual.'}, {'indicador': 'Persistencia mensual', 'definicion': 'Relación actor–caso presente en ambos meses consecutivos.'}, {'indicador': 'Jaccard mensual', 'definicion': 'Intersección de relaciones actor–caso de dos meses consecutivos dividida entre su unión.'}, {'indicador': 'Jaccard anual', 'definicion': 'Intersección de relaciones actor–caso presentes en dos años consecutivos dividida entre su unión.'}, {'indicador': 'Continuidad multianual', 'definicion': 'Relación actor–caso documentada en más de un año calendario.'}])
definiciones_temporales.to_csv(CARPETA_TABLAS / 'definiciones_indicadores_temporales.csv', index=False, encoding='utf-8-sig')
print('Bloque 5 terminado.')
print('Tablas guardadas en:', CARPETA_TABLAS.resolve())
print('Gráficos HTML guardados en:', CARPETA_GRAFOS.resolve())


# Comunidades de actores
import pandas as pd
import networkx as nx
from pathlib import Path
CARPETA_RESULTADOS = Path('resultados_redes')
CARPETA_TABLAS = CARPETA_RESULTADOS / 'tablas'
CARPETA_VALIDACIONES = CARPETA_RESULTADOS / 'validaciones'
CARPETA_GRAFOS = CARPETA_RESULTADOS / 'grafos'
for carpeta in [CARPETA_TABLAS, CARPETA_VALIDACIONES, CARPETA_GRAFOS]:
    carpeta.mkdir(parents=True, exist_ok=True)
if 'proyecciones_actores' not in globals():
    raise NameError("No existe 'proyecciones_actores'. Ejecuta primero el Bloque 2 y verifica que terminó sin errores.")
redes_actor_comunidades = {nombre: G for nombre, G in proyecciones_actores.items() if nombre.startswith(('mensual_', 'anual_')) or 'historica' in nombre}
if not redes_actor_comunidades:
    raise ValueError('No se encontraron proyecciones actor–actor.')
print('Redes actor–actor disponibles:', len(redes_actor_comunidades))
print('Ejemplos:', list(redes_actor_comunidades)[:5])

def preparar_grafo_comunidades(G):
    """
    Copia la proyección y normaliza el atributo de peso.
    Acepta tanto 'peso' como 'weight' en las aristas.
    """
    H = nx.Graph()
    H.add_nodes_from(G.nodes(data=True))
    for u, v, datos in G.edges(data=True):
        peso = datos.get('peso', datos.get('weight', 1))
        peso = float(peso)
        if peso <= 0:
            raise ValueError(f'Peso no positivo en la arista {u}–{v}: {peso}')
        H.add_edge(u, v, weight=peso)
    return H

def detectar_comunidades(G):
    """
    Usa Louvain ponderado cuando está disponible.
    Si la versión de NetworkX no lo incluye, usa greedy modularity.
    Los nodos aislados se conservan como comunidades individuales.
    """
    if G.number_of_nodes() == 0:
        return []
    G_con_aristas = G.subgraph([n for n in G.nodes() if G.degree(n) > 0]).copy()
    comunidades = []
    if G_con_aristas.number_of_nodes() > 0:
        if G_con_aristas.number_of_edges() > 0:
            if hasattr(nx.community, 'louvain_communities'):
                comunidades = nx.community.louvain_communities(G_con_aristas, weight='weight', resolution=1, seed=42)
            else:
                comunidades = list(nx.community.greedy_modularity_communities(G_con_aristas, weight='weight'))
        else:
            comunidades = [{n} for n in G_con_aristas.nodes()]
    nodos_con_comunidad = set().union(*comunidades) if comunidades else set()
    for nodo in G.nodes():
        if nodo not in nodos_con_comunidad:
            comunidades.append({nodo})
    return [set(c) for c in comunidades]

def codigo_visible(nodo, datos):
    return str(datos.get('codigo', nodo[1] if isinstance(nodo, tuple) else nodo))
filas_comunidades = []
filas_nodos = []
filas_validacion = []
comunidades_por_red = {}
for nombre_red, G_original in redes_actor_comunidades.items():
    G = preparar_grafo_comunidades(G_original)
    comunidades = detectar_comunidades(G)
    comunidades_por_red[nombre_red] = comunidades
    comunidad_por_nodo = {}
    for id_comunidad, comunidad in enumerate(comunidades, start=1):
        for nodo in comunidad:
            comunidad_por_nodo[nodo] = id_comunidad
        filas_comunidades.append({'red': nombre_red, 'comunidad': id_comunidad, 'n_actores': len(comunidad), 'actores': '; '.join(sorted((codigo_visible(n, G.nodes[n]) for n in comunidad)))})
    for nodo, id_comunidad in comunidad_por_nodo.items():
        filas_nodos.append({'red': nombre_red, 'nodo': str(nodo), 'codigo_actor': codigo_visible(nodo, G.nodes[nodo]), 'comunidad': id_comunidad, 'grado': G.degree(nodo), 'grado_ponderado': sum((datos['weight'] for _, _, datos in G.edges(nodo, data=True)))})
    modularidad = None
    if G.number_of_edges() > 0 and len(comunidades) > 1:
        modularidad = nx.community.modularity(G, comunidades, weight='weight')
    filas_validacion.append({'red': nombre_red, 'n_nodos_grafo': G.number_of_nodes(), 'n_nodos_asignados': len(comunidad_por_nodo), 'n_comunidades': len(comunidades), 'n_nodos_sin_comunidad': sum((nodo not in comunidad_por_nodo for nodo in G.nodes())), 'modularidad': modularidad, 'asignacion_completa': len(comunidad_por_nodo) == G.number_of_nodes()})
tabla_comunidades = pd.DataFrame(filas_comunidades)
tabla_nodos_comunidad = pd.DataFrame(filas_nodos)
validaciones_comunidades = pd.DataFrame(filas_validacion)
tabla_comunidades.to_csv(CARPETA_TABLAS / 'comunidades_por_red_actor_actor.csv', index=False, encoding='utf-8-sig')
tabla_nodos_comunidad.to_csv(CARPETA_TABLAS / 'asignacion_nodos_comunidades_actor_actor.csv', index=False, encoding='utf-8-sig')
validaciones_comunidades.to_csv(CARPETA_VALIDACIONES / 'validaciones_comunidades.csv', index=False, encoding='utf-8-sig')
print('Redes analizadas:', len(comunidades_por_red))
print('Todas las asignaciones están completas:', validaciones_comunidades['asignacion_completa'].all())


# Estabilidad temporal de comunidades
from sklearn.metrics import adjusted_rand_score
periodos_mensuales = sorted((nombre for nombre in redes_actor_comunidades if nombre.startswith('mensual_')))
comparaciones_comunidades = []
for nombre_anterior, nombre_siguiente in zip(periodos_mensuales[:-1], periodos_mensuales[1:]):
    G_anterior = redes_actor_comunidades[nombre_anterior]
    G_siguiente = redes_actor_comunidades[nombre_siguiente]
    actores_comunes = sorted(set(G_anterior.nodes()).intersection(G_siguiente.nodes()), key=str)
    if len(actores_comunes) < 2:
        ari = None
    else:
        mapa_anterior = {nodo: comunidad_id for comunidad_id, comunidad in enumerate(comunidades_por_red[nombre_anterior]) for nodo in comunidad}
        mapa_siguiente = {nodo: comunidad_id for comunidad_id, comunidad in enumerate(comunidades_por_red[nombre_siguiente]) for nodo in comunidad}
        etiquetas_anteriores = [mapa_anterior[n] for n in actores_comunes]
        etiquetas_siguientes = [mapa_siguiente[n] for n in actores_comunes]
        ari = adjusted_rand_score(etiquetas_anteriores, etiquetas_siguientes)
    comparaciones_comunidades.append({'periodo_anterior': nombre_anterior.replace('mensual_', ''), 'periodo_siguiente': nombre_siguiente.replace('mensual_', ''), 'actores_comunes': len(actores_comunes), 'comunidades_anterior': len(comunidades_por_red[nombre_anterior]), 'comunidades_siguiente': len(comunidades_por_red[nombre_siguiente]), 'ARI_actores_comunes': ari})
tabla_comparacion_comunidades = pd.DataFrame(comparaciones_comunidades)
tabla_comparacion_comunidades.to_csv(CARPETA_TABLAS / 'comparacion_comunidades_meses_consecutivos.csv', index=False, encoding='utf-8-sig')
print('Comparaciones mensuales guardadas:', len(tabla_comparacion_comunidades))


# Visualización de comunidades
import networkx as nx
import plotly.graph_objects as go
MAX_ACTORES = 35
redes_ejemplo = ['mensual_2021-01', 'mensual_2025-12', 'anual_2021', 'anual_2025', 'historica_2021_2025']

def codigo_visible(nodo, datos):
    if datos.get('codigo'):
        return str(datos['codigo'])
    if isinstance(nodo, tuple) and len(nodo) > 1:
        return str(nodo[1])
    return str(nodo)

def graficar_muestra_comunidades(nombre_red, G_completo, comunidades):
    comunidad_por_nodo = {nodo: numero for numero, comunidad in enumerate(comunidades, start=1) for nodo in comunidad}
    grado_ponderado = {nodo: sum((float(datos.get('weight', datos.get('peso', 1))) for _, _, datos in G_completo.edges(nodo, data=True))) for nodo in G_completo.nodes()}
    seleccionados = sorted(G_completo.nodes(), key=lambda nodo: (grado_ponderado[nodo], G_completo.degree(nodo)), reverse=True)[:MAX_ACTORES]
    G = G_completo.subgraph(seleccionados).copy()
    if G.number_of_nodes() == 0:
        print(f'Se omitió {nombre_red}: no tiene nodos.')
        return None
    posiciones = nx.spring_layout(G, seed=42, weight='weight')
    x_aristas, y_aristas = ([], [])
    for u, v in G.edges():
        x_aristas.extend([posiciones[u][0], posiciones[v][0], None])
        y_aristas.extend([posiciones[u][1], posiciones[v][1], None])
    traza_aristas = go.Scatter(x=x_aristas, y=y_aristas, mode='lines', line=dict(width=0.8, color='rgba(120,130,145,0.4)'), hoverinfo='none', name='Conexiones')
    nodos = list(G.nodes())
    etiquetas = [codigo_visible(n, G.nodes[n]) for n in nodos]
    traza_nodos = go.Scatter(x=[posiciones[n][0] for n in nodos], y=[posiciones[n][1] for n in nodos], mode='markers+text', text=etiquetas, textposition='top center', textfont=dict(size=10), marker=dict(size=[9 + 1.5 * min(G.degree(n), 12) for n in nodos], color=[comunidad_por_nodo.get(n, 0) for n in nodos], colorscale='Turbo', showscale=True, colorbar=dict(title='Comunidad'), line=dict(width=0.6, color='white')), customdata=[[etiquetas[i], comunidad_por_nodo.get(n, 'Sin asignar'), G.degree(n), round(grado_ponderado[n], 2)] for i, n in enumerate(nodos)], hovertemplate='Actor: %{customdata[0]}<br>Comunidad en red completa: %{customdata[1]}<br>Grado en la muestra: %{customdata[2]}<br>Grado ponderado en red completa: %{customdata[3]}<extra></extra>', name='Actores')
    fig = go.Figure(data=[traza_aristas, traza_nodos])
    fig.update_layout(title=f'Comunidades actor–actor — {nombre_red}<br><sup>Muestra visual: {G.number_of_nodes()} actores de {G_completo.number_of_nodes()} en la red completa</sup>', template='plotly_white', showlegend=False, margin=dict(l=20, r=30, t=90, b=20), xaxis=dict(visible=False), yaxis=dict(visible=False))
    ruta = CARPETA_GRAFOS / f'comunidades_muestra_{nombre_red}.html'
    fig.write_html(ruta, include_plotlyjs='cdn')
    return ruta
archivos_graficos_muestra = []
for nombre_red in redes_ejemplo:
    if nombre_red not in redes_actor_comunidades:
        print(f'No se encontró la red: {nombre_red}')
        continue
    ruta = graficar_muestra_comunidades(nombre_red, redes_actor_comunidades[nombre_red], comunidades_por_red[nombre_red])
    if ruta is not None:
        archivos_graficos_muestra.append(ruta)
print('\nGráficos de muestra guardados:')
for ruta in archivos_graficos_muestra:
    print('-', ruta)


# Validaciones
import pandas as pd
import networkx as nx
from pathlib import Path
CARPETA_RESULTADOS = Path('resultados_redes')
CARPETA_TABLAS = CARPETA_RESULTADOS / 'tablas'
CARPETA_VALIDACIONES = CARPETA_RESULTADOS / 'validaciones'
CARPETA_GRAFOS = CARPETA_RESULTADOS / 'grafos'
for carpeta in [CARPETA_TABLAS, CARPETA_VALIDACIONES, CARPETA_GRAFOS]:
    carpeta.mkdir(parents=True, exist_ok=True)
columnas_base = ['periodo_reporte', 'id_caso', 'Id_actor', 'Actor_normalizado', 'nombre_caso']
faltantes_columnas = [c for c in columnas_base if c not in df.columns]
if faltantes_columnas:
    raise ValueError(f'Faltan columnas en df: {faltantes_columnas}')
validaciones_base = []

def registrar_validacion(etapa, prueba, resultado, detalle=''):
    validaciones_base.append({'etapa': etapa, 'prueba': prueba, 'aprobada': bool(resultado), 'detalle': str(detalle)})
registrar_validacion('Base original', 'La base conserva las filas importadas', len(df) == filas_iniciales, f'Filas actuales: {len(df)}')
registrar_validacion('Base original', 'Identificadores de actor no vacíos', df['Id_actor'].notna().all() and df['Id_actor'].astype(str).str.strip().ne('').all(), f"Filas con Id_actor vacío: {df['Id_actor'].isna().sum()}")
registrar_validacion('Base original', 'Identificadores de caso no vacíos', df['id_caso'].notna().all() and df['id_caso'].astype(str).str.strip().ne('').all(), f"Filas con id_caso vacío: {df['id_caso'].isna().sum()}")
registrar_validacion('Base original', 'Periodos de reporte no vacíos', df['periodo_reporte'].notna().all(), f"Filas con periodo vacío: {df['periodo_reporte'].isna().sum()}")
relaciones_validacion = df[['periodo_reporte', 'id_caso', 'Id_actor', 'Actor_normalizado', 'nombre_caso']].drop_duplicates(subset=['periodo_reporte', 'id_caso', 'Id_actor']).copy()
registrar_validacion('Relaciones', 'No hay duplicados en periodo-caso-actor', not relaciones_validacion.duplicated(subset=['periodo_reporte', 'id_caso', 'Id_actor']).any(), f'Relaciones únicas: {len(relaciones_validacion)}')
duplicados_relacion = df[df.duplicated(subset=['periodo_reporte', 'id_caso', 'Id_actor'], keep=False)].copy()
duplicados_relacion.to_csv(CARPETA_VALIDACIONES / 'registros_duplicados_periodo_caso_actor.csv', index=False, encoding='utf-8-sig')
redes_bipartitas_validacion = {}
redes_bipartitas_validacion.update({f'mensual_{periodo}': G for periodo, G in grafos_bipartitos.items()})
redes_bipartitas_validacion.update({f'anual_{periodo}': G for periodo, G in grafos_bipartitos_anuales.items()})
redes_bipartitas_validacion['historica_2021_2025'] = grafo_bipartito_historico
validaciones_estructura = []
for nombre_red, G in redes_bipartitas_validacion.items():
    nodos_tienen_tipo = all((G.nodes[n].get('tipo') in ['actor', 'caso'] for n in G.nodes()))
    aristas_bipartitas = all((G.nodes[u].get('tipo') != G.nodes[v].get('tipo') for u, v in G.edges()))
    sin_autobucle = nx.number_of_selfloops(G) == 0
    codigos_no_vacios = all((str(G.nodes[n].get('codigo', '')).strip() != '' for n in G.nodes()))
    validaciones_estructura.append({'red': nombre_red, 'n_nodos': G.number_of_nodes(), 'n_aristas': G.number_of_edges(), 'nodos_con_tipo_actor_o_caso': nodos_tienen_tipo, 'todas_las_aristas_actor_caso': aristas_bipartitas, 'sin_autobucles': sin_autobucle, 'codigos_no_vacios': codigos_no_vacios})
validaciones_estructura = pd.DataFrame(validaciones_estructura)
validaciones_base = pd.DataFrame(validaciones_base)
validaciones_base.to_csv(CARPETA_VALIDACIONES / 'validaciones_base_y_relaciones.csv', index=False, encoding='utf-8-sig')
validaciones_estructura.to_csv(CARPETA_VALIDACIONES / 'validaciones_estructura_bipartita.csv', index=False, encoding='utf-8-sig')
print('Validaciones de base y relaciones guardadas.')
print('Validaciones estructurales de redes bipartitas guardadas.')


# Sensibilidad institucional
import re
import unicodedata
import plotly.express as px

def normalizar_nombre(valor):
    valor = unicodedata.normalize('NFKD', str(valor).lower())
    valor = ''.join((c for c in valor if not unicodedata.combining(c)))
    return re.sub('\\s+', ' ', valor).strip()
actores_unicos = relaciones[['Id_actor', 'Actor_normalizado']].drop_duplicates()
actores_unicos = actores_unicos.assign(nombre_normalizado=actores_unicos['Actor_normalizado'].map(normalizar_nombre))
patrones = {'sin_defensoria': '^defensoria del pueblo$', 'sin_pcm': '^presidencia del consejo de ministros(?: \\(pcm\\))?$', 'sin_minem': '^ministerio de energia y minas(?: \\(minem\\))?$'}
seleccion = {}
for escenario, patron in patrones.items():
    candidatos = actores_unicos.loc[actores_unicos['nombre_normalizado'].str.fullmatch(patron)]
    ids = candidatos['Id_actor'].unique().tolist()
    if len(ids) != 1:
        raise ValueError(f"Revisar identificador de {escenario}: {candidatos[['Id_actor', 'Actor_normalizado']].to_dict('records')}")
    seleccion[escenario] = str(ids[0])
G_original = grafo_bipartito_historico
escenarios_sensibilidad = {'original': G_original.copy()}
for nombre, codigo in seleccion.items():
    G = G_original.copy()
    G.remove_node(('actor', codigo))
    escenarios_sensibilidad[nombre] = G
G = G_original.copy()
G.remove_nodes_from([('actor', codigo) for codigo in seleccion.values()])
escenarios_sensibilidad['sin_tres_instituciones'] = G

def medir_escenario(nombre, G):
    actores = sum((d.get('tipo') == 'actor' for _, d in G.nodes(data=True)))
    casos = sum((d.get('tipo') == 'caso' for _, d in G.nodes(data=True)))
    componentes = list(nx.connected_components(G)) if len(G) else []
    return {'escenario': nombre, 'n_actores': actores, 'n_casos': casos, 'n_nodos': G.number_of_nodes(), 'n_aristas': G.number_of_edges(), 'n_componentes': len(componentes), 'tamano_componente_mayor': max(map(len, componentes), default=0), 'densidad_bipartita': G.number_of_edges() / (actores * casos) if actores * casos else 0.0}
tabla_sensibilidad_institucional = pd.DataFrame([medir_escenario(nombre, G) for nombre, G in escenarios_sensibilidad.items()])
base = tabla_sensibilidad_institucional.iloc[0]
for metrica in ('n_actores', 'n_nodos', 'n_aristas', 'n_componentes', 'tamano_componente_mayor', 'densidad_bipartita'):
    tabla_sensibilidad_institucional[f'cambio_abs_{metrica}'] = tabla_sensibilidad_institucional[metrica] - base[metrica]
    tabla_sensibilidad_institucional[f'cambio_pct_{metrica}'] = 100 * (tabla_sensibilidad_institucional[metrica] - base[metrica]) / base[metrica] if base[metrica] else np.nan
tabla_sensibilidad_institucional.to_csv(CARPETA_TABLAS / 'sensibilidad_institucional_individual_y_conjunta.csv', index=False, encoding='utf-8-sig')
validaciones_sensibilidad = pd.DataFrame([{'control': 'relaciones_historicas', 'aprobada': G_original.number_of_edges() == len(relaciones_historicas)}, {'control': 'sin_autobucles', 'aprobada': all((nx.number_of_selfloops(G) == 0 for G in escenarios_sensibilidad.values()))}, {'control': 'instituciones_excluidas', 'aprobada': all((('actor', x) not in escenarios_sensibilidad['sin_tres_instituciones'] for x in seleccion.values()))}])
validaciones_sensibilidad.to_csv(CARPETA_VALIDACIONES / 'validaciones_sensibilidad.csv', index=False, encoding='utf-8-sig')
tabla_grafico = tabla_sensibilidad_institucional.melt(id_vars='escenario', value_vars=['n_aristas', 'tamano_componente_mayor'], var_name='indicador', value_name='valor')
fig_sensibilidad = px.bar(tabla_grafico, x='escenario', y='valor', color='indicador', barmode='group', title='Sensibilidad de la red bipartita histórica')
fig_sensibilidad.update_layout(template='plotly_white', xaxis_tickangle=-15)
fig_sensibilidad.write_html(CARPETA_GRAFICOS / 'sensibilidad_institucional.html', include_plotlyjs='cdn')


# Índice de archivos
archivos = pd.DataFrame([{'categoria': carpeta.name, 'archivo': ruta.name} for carpeta in (CARPETA_TABLAS, CARPETA_VALIDACIONES, CARPETA_GRAFOS, CARPETA_GRAFICOS) for ruta in sorted(carpeta.iterdir()) if ruta.is_file()])
archivos.to_csv(CARPETA_RESULTADOS / 'indice_archivos.csv', index=False, encoding='utf-8-sig')
print(f'Archivos generados: {len(archivos)}')
