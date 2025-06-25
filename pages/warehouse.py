import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from utils.warehouse_plot import load_layout, create_3d_warehouse, get_warehouse_by_name, get_zone_by_name
from utils.data_loader import load_inventario, load_articulos
from dash import dash_table
import numpy as np
import pandas as pd
from utils.ocupacion_utils import calcular_ocupacion_racks, calcular_ocupacion_bodega


# --- CACHE para resumen de ocupación ---
_ocupacion_cache = {'data': None, 'inv_timestamp': 0}

def calcular_medida_ocupacion():
    from utils.data_loader import load_inventario, load_articulos, _inventario_cache
    # Si el inventario no ha cambiado, usar el cache
    if _ocupacion_cache.get('data') is not None and _ocupacion_cache['inv_timestamp'] == _inventario_cache['timestamp']:
        return _ocupacion_cache['data']
    bodegas_dict = {
        'Principal': {"A011", "C010", "C015", "C018"},
        'Bodega_13': {"D017"},
        'Proyectos': {"C014"},
        'Alterna': {"D018"}
    }
    df_inv = load_inventario()
    if df_inv is None or df_inv.empty:
        return None
    resultados = {}
    for nombre, bodegas in bodegas_dict.items():
        # Usar el resumen global de bodega, no por rack
        from utils.ocupacion_utils import calcular_ocupacion_bodega
        resumen = calcular_ocupacion_bodega(df_inv, bodega_layout_name=nombre)
        resultados[nombre] = resumen
    _ocupacion_cache['data'] = resultados
    _ocupacion_cache['inv_timestamp'] = _inventario_cache['timestamp']
    return resultados


def calcular_resumen_bodega():
    """
    Devuelve un dict con el resumen de ocupación por bodega física (no por rack).
    """
    from utils.data_loader import load_inventario, _inventario_cache
    from utils.ocupacion_utils import calcular_ocupacion_bodega
    if _ocupacion_cache['data'] is not None and _ocupacion_cache['inv_timestamp'] == _inventario_cache['timestamp']:
        return _ocupacion_cache.get('resumen_bodega')
    bodegas_dict = {
        'Principal': {"A011", "C010", "C015", "C018"},
        "Principal_Mezzanine": {"A011", "C010", "C015", "C018"},
        "Principal_Alturas": {"A011", "C010", "C015", "C018"},
        'Bodega_13': {"D017"},
        'Proyectos': {"C014"}
    }
    df_inv = load_inventario()
    if df_inv is None or df_inv.empty:
        return None
    resumen = {}
    for nombre in bodegas_dict:
        resumen[nombre] = calcular_ocupacion_bodega(df_inv, bodega_layout_name=nombre)
    _ocupacion_cache['resumen_bodega'] = resumen
    return resumen


def warehouse_layout(only_occupation=False):
    layout_data = load_layout()
    warehouse_names = [w['name'] for w in layout_data.get('warehouses', [])]
    first_warehouse = warehouse_names[0] if warehouse_names else None
    first_zones = []
    if first_warehouse:
        wh = get_warehouse_by_name(layout_data, first_warehouse)
        first_zones = [z['name'] for z in wh.get('zones', [])]
    dropdown_warehouse = dcc.Dropdown(
        id='warehouse-dropdown',
        options=[{'label': w, 'value': w} for w in warehouse_names],
        value=first_warehouse,
        clearable=False,
        style={"width": "100%", "marginBottom": "1em"},
        className="form-select mb-3"
    )
    dropdown_zone = dcc.Dropdown(
        id='zone-dropdown',
        options=[{'label': z, 'value': z} for z in first_zones],
        value=first_zones[0] if first_zones else None,
        clearable=False,
        style={"width": "100%", "marginBottom": "1em"},
        className="form-select mb-3"
    )
    # --- NEW: Manual refresh button and store ---
    refresh_button = dbc.Button("Actualizar inventario", id="refresh-inv-btn", color="primary", className="mb-2 me-2 btn btn-primary")
    refresh_store = dcc.Store(id="refresh-inv-store", data={"refresh": False, "ts": 0})
    # Spinner de carga para el resumen general
    resumen_spinner = html.Div([
        dbc.Spinner(
            [html.Div(id='resumenes-content')],
            color="primary", fullscreen=False, type="border", size="lg", delay_show=300, spinner_style={"width": "4rem", "height": "4rem"}
        )
    ], className="my-4")
    # Contenedor para el gráfico y resumen de zona
    content = html.Div(id='zona-content', className="mt-4")
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("Resumen de ocupación por bodega/zona:", className="mb-3"),
                    resumen_spinner
                ], className="card card-body shadow-sm mb-4"),
            ], width=12)
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Label("Bodega:", className="form-label me-2"),
                        dropdown_warehouse
                    ], className="mb-2"),
                    html.Div([
                        html.Label("Zona:", className="form-label me-2"),
                        dropdown_zone
                    ], className="mb-2"),
                    refresh_button,
                    refresh_store
                ], className="card card-body shadow-sm mb-4"),
            ], width=12)
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    content
                ], className="card card-body shadow-sm mb-4"),
            ], width=12)
        ])
    ], fluid=True, className="py-4")

# --- CALLBACKS ---

from dash import callback, Output, Input, State
import time

@callback(
    Output('zone-dropdown', 'options'),
    Output('zone-dropdown', 'value'),
    Input('warehouse-dropdown', 'value')
)
def update_zone_dropdown(warehouse_name):
    layout_data = load_layout()
    wh = get_warehouse_by_name(layout_data, warehouse_name)
    zones = [z['name'] for z in wh.get('zones', [])] if wh else []
    value = zones[0] if zones else None
    return [{'label': z, 'value': z} for z in zones], value

@callback(
    Output("refresh-inv-store", "data"),
    Input("refresh-inv-btn", "n_clicks"),
    prevent_initial_call=True
)
def trigger_refresh(n_clicks):
    # Set refresh flag and timestamp
    return {"refresh": True, "ts": time.time()}

@callback(
    Output('zona-content', 'children'),
    Input('warehouse-dropdown', 'value'),
    Input('zone-dropdown', 'value'),
    Input('refresh-inv-store', 'data')
)
def update_zona_content(warehouse_name, zone_name, refresh_data):
    try:
        force_refresh = False
        if refresh_data and refresh_data.get("refresh", False):
            force_refresh = True
            global _ocupacion_cache
            _ocupacion_cache = {'data': None, 'inv_timestamp': 0}
        
        layout_data = load_layout()
        wh = get_warehouse_by_name(layout_data, warehouse_name)
        if not wh or not zone_name:
            return dbc.Alert("Selecciona una bodega y zona.", color="warning")
        
        zone = get_zone_by_name(wh, zone_name)
        if not zone:
            return dbc.Alert("Zona no encontrada.", color="danger")
        
        wh_for_plot = wh.copy()
        wh_for_plot['zones'] = [zone]
        
        inventario_df = load_inventario(force_refresh=force_refresh)
        if inventario_df is None or inventario_df.empty:
            return dbc.Alert("No se pudieron cargar los datos de inventario. La fuente de datos puede estar vacía o inaccesible.", color="warning")

        articulos_dict = load_articulos()
        
        fig = create_3d_warehouse(wh_for_plot, inventario_df=inventario_df, articulos_dict=articulos_dict, warehouse_name=warehouse_name)
        return dcc.Graph(figure=fig, style={"height": "700px"})
    except Exception as e:
        import traceback
        print(f"Error en update_zona_content: {traceback.format_exc()}")
        return dbc.Alert(f"Error al generar la vista de la zona: {e}", color="danger")

@callback(
    Output('resumenes-content', 'children'),
    Input('warehouse-dropdown', 'value'),
    Input('zone-dropdown', 'value'),
    Input('refresh-inv-store', 'data')
)
def update_resumenes_content(warehouse_name, zone_name, refresh_data):
    try:
        force_refresh = False
        if refresh_data and refresh_data.get("refresh", False):
            force_refresh = True
            global _ocupacion_cache
            _ocupacion_cache = {'data': None, 'inv_timestamp': 0}

        # La lógica de refresh se maneja reseteando el caché y pasando el flag a load_inventario
        # que es llamado dentro de las funciones de cálculo.
        resumen_bodega = calcular_resumen_bodega()

        if not resumen_bodega:
            return dbc.Alert("No se pudieron calcular los resúmenes de ocupación. Verifique la fuente de datos.", color="warning")

        resumenes = []
        for nombre, resumen in resumen_bodega.items():
            if resumen and isinstance(resumen, dict) and all(k in resumen for k in ['Volumen ocupado (m³)', 'Volumen máximo (m³)', '% Ocupación', 'Volumen disponible (m³)']):
                resumenes.append(
                    dbc.Card([
                        dbc.CardHeader(html.H4(f"{nombre} (Resumen Bodega)", className="mb-0")),
                        dbc.CardBody([
                            html.H5(f"Volumen ocupado: {resumen['Volumen ocupado (m³)']:,} m³", className="card-title"),
                            html.H5(f"Volumen máximo: {resumen['Volumen máximo (m³)']:,} m³", className="card-title"),
                            html.H5(f"% Ocupación: {resumen['% Ocupación']*100:.1f}%", className="card-title"),
                            html.H5(f"Volumen disponible: {resumen['Volumen disponible (m³)']:,} m³", className="card-title")
                        ])
                    ], className="mb-4 shadow-sm")
                )
            else:
                resumenes.append(dbc.Alert(f"Datos de ocupación incompletos o no disponibles para {nombre}.", color="warning"))
        
        if not resumenes:
            return dbc.Alert("No hay resúmenes de ocupación para mostrar.", color="info")

        return dbc.Row([dbc.Col(resumen, width=6) for resumen in resumenes], className="g-4 justify-content-center mb-4")
    except Exception as e:
        import traceback
        print(f"Error en update_resumenes_content: {traceback.format_exc()}")
        return dbc.Alert(f"Error al generar los resúmenes de ocupación: {e}", color="danger")


# --- CACHE para tabla de inventario filtrada ---
_inv_table_cache = {'data': None, 'search': None, 'inv_timestamp': 0}

@callback(
    Output("inv-table-container", "children"),
    Input("inv-codart-search", "value"),
    Input("refresh-inv-store", "data")
)
def update_inv_table(search_value, refresh_data):
    from utils.data_loader import load_inventario, _inventario_cache
    force_refresh = False
    if refresh_data and refresh_data.get("refresh", False):
        force_refresh = True
        global _inv_table_cache
        _inv_table_cache = {'data': None, 'search': None, 'inv_timestamp': 0}
    df_inv = load_inventario(force_refresh=force_refresh)
    now_inv_timestamp = _inventario_cache['timestamp']
    # Si el inventario y el filtro no han cambiado, usar el cache
    if (
        _inv_table_cache['data'] is not None and
        _inv_table_cache['search'] == search_value and
        _inv_table_cache['inv_timestamp'] == now_inv_timestamp
    ):
        return _inv_table_cache['data']
    if df_inv is not None and not df_inv.empty:
        df_inv.columns = [c.lower() for c in df_inv.columns]
        codart_col = next((c for c in df_inv.columns if "codart" in c), None)
        if not codart_col:
            return html.Div("No se encontró la columna de codArt en los datos de inventario.", style={"color": "red"})
        if search_value:
            df_filtered = df_inv[df_inv[codart_col].astype(str).str.contains(str(search_value), case=False, na=False)]
        else:
            df_filtered = df_inv
        columns = [{"name": c, "id": c} for c in df_filtered.columns]
        data = df_filtered.to_dict("records")
        table = dash_table.DataTable(
            columns=columns,
            data=data,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center", "fontSize":14},
            style_header={"backgroundColor": "#e0e0e0", "fontWeight": "bold"},
            page_size=10
        )
        _inv_table_cache['data'] = table
        _inv_table_cache['search'] = search_value
        _inv_table_cache['inv_timestamp'] = now_inv_timestamp
        return table
    else:
        return html.Div("No hay datos de inventario disponibles.")
