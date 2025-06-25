# simulator_callbacks.py (callbacks para el simulador)
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output, State
import pandas as pd
from utils.data_loader import load_data, get_dependency_map

def register_resource_callbacks(app, df_resources, dependency_map):

    # Callback para mostrar la tabla de datos base y filtrarla
    @app.callback(
        Output("base-data-table-container", "children"),
        [Input("tipoarea-filter", "value"), Input("area-filter", "value")]
    )
    def update_base_table(tipoarea, area):
        df = load_data()
        filtered_df = df.copy()
        if tipoarea:
            filtered_df = filtered_df[filtered_df['TipoArea'] == tipoarea]
        if area:
            filtered_df = filtered_df[filtered_df['Area'] == area]
        filtered_df['Cantidad'] = filtered_df['Cantidad'].apply(lambda x: f"{x:,.0f}")
        table = dbc.Table.from_dataframe(filtered_df, striped=True, bordered=True, hover=True)
        return table

    # Callback principal para la simulación
    @app.callback(
        [Output("simulation-results-alert", "children"),
         Output("simulation-results-alert", "is_open")],
        [Input("btn-run-simulation", "n_clicks")],
        [State("driver-metric-select", "value"),
         State("new-value-input", "value")]
    )
    def run_simulation(n_clicks, driver_metric, new_value):
        if n_clicks is None:
            return "Seleccione un indicador, ingrese un nuevo valor y haga clic en 'Simular Impacto'.", False

        # --- Validación de entradas ---
        if not driver_metric or new_value is None:
            return html.Div([
                html.Strong("Error de validación:"),
                html.P("Debe seleccionar un indicador (driver) y proporcionar un nuevo valor numérico.")
            ]), True

        try:
            new_value = float(new_value)
            if new_value < 0:
                raise ValueError
        except (ValueError, TypeError):
            return html.Div([
                html.Strong("Error de validación:"),
                html.P("El nuevo valor debe ser un número positivo.")
            ]), True

        # --- Lógica de cálculo ---
        try:
            # 1. Obtener valor base del driver
            base_driver_value = df_resources.loc[driver_metric, 'Cantidad']
            if base_driver_value == 0:
                return f"Error: El valor base para '{driver_metric}' es 0, no se puede calcular la proporción.", True

            # 2. Obtener la lista de métricas que dependen de este driver
            dependent_metrics = dependency_map.get(driver_metric, [])
            if not dependent_metrics:
                return f"No hay dependencias definidas para '{driver_metric}'.", True

            # 3. Calcular y mostrar los resultados
            results_list = [html.H5(f"Impacto de cambiar '{driver_metric}' de {base_driver_value:,.0f} a {new_value:,.0f}:")]
            
            for metric in dependent_metrics:
                base_dependent_value = df_resources.loc[metric, 'Cantidad']
                
                # Calcular la proporción
                ratio = base_dependent_value / base_driver_value
                
                # Calcular el nuevo valor y el cambio
                new_dependent_value = new_value * ratio
                change = new_dependent_value - base_dependent_value
                
                # Formatear el resultado
                color = "text-success" if change >= 0 else "text-danger"
                sign = "+" if change >= 0 else ""
                
                results_list.append(
                    html.P([
                        f" • {metric}: ",
                        html.Strong(f"{new_dependent_value:,.0f}", className="me-2"),
                        html.Span(f" (Cambio: {sign}{change:,.0f})", className=color)
                    ])
                )

            return results_list, True

        except KeyError as e:
            return f"Error: La métrica '{e}' no se encontró en los datos.", True
        except Exception as e:
            return f"Ocurrió un error inesperado: {e}", True

def capacidades_bodega_layout():
    import dash_bootstrap_components as dbc
    from dash import dcc, html
    # Tabs para TipoArea
    tabs = []
    for tipoarea in ['Ramedicas', 'Proyectos']:
        tab_content = html.Div([
            html.H4(f"Calculadora de capacidades - {tipoarea}"),
            html.Div(id=f"calculadora-content-{tipoarea.lower()}")
        ])
        tabs.append(dcc.Tab(label=tipoarea, value=tipoarea.lower(), children=[tab_content]))
    return dcc.Tabs(id="tabs-tipoarea", value="ramedicas", children=tabs)

# Exportar para importación en main.py
capacidad_bodega_layout = capacidades_bodega_layout

from dash import callback, Output, Input, State
import dash_bootstrap_components as dbc
from dash import dcc, html

@callback(
    Output("calculadora-content-ramedicas", "children"),
    Input("tabs-tipoarea", "value"),
    State("calculadora-content-ramedicas", "children")
)
def show_calculadora_ramedicas(tab, _):
    if tab != "ramedicas":
        return None
    df = load_data()
    try:
        unidades_actual = int(df[df['Descripcion'].str.lower().str.contains('unidades facturadas')]['Cantidad'].iloc[0])
    except Exception:
        unidades_actual = 0
    return html.Div([
        html.H5("Simulador de Unidades Facturadas (Ramedicas)", className="card-title mb-3"),
        dbc.Label("Unidades facturadas promedio mensual actual:"),
        html.Div([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{unidades_actual:,.0f}".replace(",", "."), className="display-4 text-center mb-0")
                ])
            ], color="primary", inverse=True, className="mb-3 shadow-sm")
        ], className="row"),
        dbc.Label("Aumento de unidades facturadas:"),
        dbc.Input(id="input-aumento-facturadas", type="number", placeholder="Ej: 200000", value=200000, min=0, step=1000, className="form-control mb-2"),
        dbc.Button("Calcular Impacto", id="btn-calcular-impacto-ramedicas", color="primary", className="btn btn-primary mb-3"),
        html.Div(id="impacto-ramedicas-result", className="mt-3")
    ], className="card p-4 shadow border-0 mb-4")

@callback(
    Output("impacto-ramedicas-result", "children"),
    Input("btn-calcular-impacto-ramedicas", "n_clicks"),
    State("input-aumento-facturadas", "value")
)
def calcular_impacto_ramedicas(n_clicks, aumento):
    if not n_clicks:
        return None
    import pandas as pd
    df = load_data()
    try:
        unidades_actual = int(df[df['Descripcion'].str.lower().str.contains('unidades facturadas')]['Cantidad'].iloc[0])
    except Exception:
        unidades_actual = 0
    if aumento is None:
        return dbc.Alert("Debes ingresar el aumento de unidades facturadas.", color="warning", className="alert alert-warning")
    nuevas_unidades = unidades_actual + aumento
    porcentaje_aumento = (aumento / unidades_actual * 100) if unidades_actual > 0 else 0
    df_ramedicas = df[df['TipoArea'].str.lower() == 'ramedicas'].copy()
    df_ramedicas['Ratio'] = df_ramedicas['Cantidad'] / unidades_actual
    df_ramedicas['Nuevo Valor Teorico'] = df_ramedicas['Ratio'] * nuevas_unidades
    df_ramedicas['ImpactoNum'] = df_ramedicas['Impacto'].str.replace('%','').astype(float) / 100
    df_ramedicas['Aumento Necesario'] = ((df_ramedicas['Nuevo Valor Teorico'] - df_ramedicas['Cantidad']) * df_ramedicas['ImpactoNum']).round(0).astype(int)
    df_ramedicas['Nuevo Total'] = (df_ramedicas['Cantidad'] + df_ramedicas['Aumento Necesario']).astype(int)
    for col in ['Cantidad','Aumento Necesario','Nuevo Total']:
        df_ramedicas[col] = df_ramedicas[col].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    table = dbc.Table.from_dataframe(
        df_ramedicas[['Descripcion','Cantidad','Impacto','Aumento Necesario','Nuevo Total']],
        striped=True, bordered=True, hover=True,
        className="table table-bordered table-hover table-striped table-responsive-md tabla-impacto mb-0"
    )
    resumen = html.Div([
        html.H6(f"Unidades facturadas actuales: {unidades_actual:,.0f}".replace(",", "."), className="mb-1"),
        html.H6(f"Aumento de unidades facturadas: {aumento:,.0f}".replace(",", "."), className="mb-1"),
        html.H6(f"Nuevo total de unidades facturadas: {nuevas_unidades:,.0f}".replace(",", "."), className="mb-1"),
        html.H6(f"Porcentaje de aumento: {porcentaje_aumento:.2f}%", className="mb-3")
    ], className="mb-3")
    return html.Div([
        resumen,
        table
    ], className="card card-body shadow-sm border-0")

@callback(
    Output("calculadora-content-proyectos", "children"),
    Input("tabs-tipoarea", "value"),
    State("calculadora-content-proyectos", "children")
)
def show_calculadora_proyectos(tab, _):
    if tab != "proyectos":
        return None
    df = load_data()
    try:
        unidades_consignacion = int(df[df['Descripcion'].str.lower().str.contains('unidades en consignacion')]['Cantidad'].iloc[0])
    except Exception:
        unidades_consignacion = 0
    return html.Div([
        html.H5("Simulador de Unidades en Consignación (Proyectos)", className="card-title mb-3"),
        dbc.Label("Unidades en consignación promedio mensual actual:"),
        html.Div([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{unidades_consignacion:,.0f}".replace(",", "."), className="display-4 text-center mb-0")
                ])
            ], color="primary", inverse=True, className="mb-3 shadow-sm")
        ], className="row"),
        dbc.Label("Aumento de unidades en consignación:"),
        dbc.Input(id="input-aumento-facturadas-proyectos", type="number", placeholder="Ej: 10000", value=10000, min=0, step=1000, className="form-control mb-2"),
        dbc.Button("Calcular Impacto", id="btn-calcular-impacto-proyectos", color="primary", className="btn btn-primary mb-3"),
        html.Div(id="impacto-proyectos-result", className="mt-3")
    ], className="card p-4 shadow border-0 mb-4")

@callback(
    Output("impacto-proyectos-result", "children"),
    Input("btn-calcular-impacto-proyectos", "n_clicks"),
    State("input-aumento-facturadas-proyectos", "value")
)
def calcular_impacto_proyectos(n_clicks, aumento):
    if not n_clicks:
        return None
    import pandas as pd
    df = load_data()
    try:
        unidades_consignacion = int(df[df['Descripcion'].str.lower().str.contains('unidades en consignacion')]['Cantidad'].iloc[0])
    except Exception:
        unidades_consignacion = 0
    if aumento is None:
        return dbc.Alert("Debes ingresar el aumento de unidades en consignación.", color="warning", className="alert alert-warning")
    nuevas_unidades = unidades_consignacion + aumento
    porcentaje_aumento = (aumento / unidades_consignacion * 100) if unidades_consignacion > 0 else 0
    df_proyectos = df[df['TipoArea'].str.lower() == 'proyectos'].copy()
    df_proyectos['Ratio'] = df_proyectos['Cantidad'] / unidades_consignacion
    df_proyectos['Nuevo Valor Teorico'] = df_proyectos['Ratio'] * nuevas_unidades
    df_proyectos['ImpactoNum'] = df_proyectos['Impacto'].str.replace('%','').astype(float) / 100
    df_proyectos['Aumento Necesario'] = ((df_proyectos['Nuevo Valor Teorico'] - df_proyectos['Cantidad']) * df_proyectos['ImpactoNum']).round(0).astype(int)
    df_proyectos['Nuevo Total'] = (df_proyectos['Cantidad'] + df_proyectos['Aumento Necesario']).astype(int)
    for col in ['Cantidad','Aumento Necesario','Nuevo Total']:
        df_proyectos[col] = df_proyectos[col].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    table = dbc.Table.from_dataframe(
        df_proyectos[['Descripcion','Cantidad','Impacto','Aumento Necesario','Nuevo Total']],
        striped=True, bordered=True, hover=True,
        className="table table-bordered table-hover table-striped table-responsive-md tabla-impacto mb-0"
    )
    resumen = html.Div([
        html.H6(f"Unidades en consignación actuales: {unidades_consignacion:,.0f}".replace(",", "."), className="mb-1"),
        html.H6(f"Aumento de unidades en consignación: {aumento:,.0f}".replace(",", "."), className="mb-1"),
        html.H6(f"Nuevo total de unidades en consignación: {nuevas_unidades:,.0f}".replace(",", "."), className="mb-1"),
        html.H6(f"Porcentaje de aumento: {porcentaje_aumento:.2f}%", className="mb-3")
    ], className="mb-3")
    return html.Div([
        resumen,
        table
    ], className="card card-body shadow-sm border-0")