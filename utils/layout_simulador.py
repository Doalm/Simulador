import dash_bootstrap_components as dbc
from dash import html, dcc


def resource_simulator_layout(df_resources):
    # Obtenemos los posibles 'drivers' de nuestro mapa de dependencias
    from utils.data_loader import get_dependency_map
    drivers = list(get_dependency_map().keys())

    # Ajustar para nuevas columnas: 'TipoArea', 'Area', 'Impacto'
    tipoarea_options = [{'label': tipo, 'value': tipo} for tipo in df_resources['TipoArea'].unique()]
    area_options = [{'label': area, 'value': area} for area in df_resources['Area'].unique()]
    layout = dbc.Container([
        dbc.Row([
            dbc.Col(html.H3("Simulador de Recursos Operativos", className="text-center mb-4 card-title"), width=12)
        ]),
        
        # --- SECCIÓN DE CONTROLES DE SIMULACIÓN ---
        dbc.Row([
            dbc.Col([
                dbc.Label("1. Seleccione el Indicador a Cambiar (Driver):", className="form-label mb-1"),
                dcc.Dropdown(id="driver-metric-select", options=[{'label': i, 'value': i} for i in drivers], placeholder="Seleccionar driver...", className="form-select mb-2"),
            ], md=6, className="mb-3"),
            dbc.Col([
                dbc.Label("2. Ingrese el Nuevo Valor Total:", className="form-label mb-1"),
                dbc.Input(id="new-value-input", type="number", placeholder="Ej: 1600000", className="form-control mb-2"),
            ], md=4, className="mb-3"),
            dbc.Col([
                dbc.Button("Simular Impacto", id="btn-run-simulation", color="success", className="w-100 mt-4 btn btn-success")
            ], md=2, className="align-self-end mb-3")
        ], className="mb-3 align-items-end g-3"), # g-3 añade espacio entre columnas

        # --- SECCIÓN DE RESULTADOS ---
        dbc.Row([
            dbc.Col([
                html.H4("Resultados de la Simulación:", className="mt-4 card-title"),
                dbc.Alert(id="simulation-results-alert", color="success", className="mt-2", is_open=False)
            ])
        ]),

        # --- SECCIÓN PARA MOSTRAR DATOS BASE ---
        dbc.Row([
            dbc.Col([
                html.H4("Datos Base Actuales", className="mt-5 card-title"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Filtrar por TipoArea:", className="form-label mb-1"),
                        dcc.Dropdown(id="tipoarea-filter", options=tipoarea_options, placeholder="Seleccionar TipoArea...", className="form-select mb-2"),
                    ], md=6, className="mb-3"),
                    dbc.Col([
                        dbc.Label("Filtrar por Área:", className="form-label mb-1"),
                        dcc.Dropdown(id="area-filter", options=area_options, placeholder="Seleccionar Área...", className="form-select mb-2"),
                    ], md=6, className="mb-3"),
                ], className="mb-3"),
                html.Div(id="base-data-table-container", className="mt-3")
            ])
        ])

    ], fluid=True, className="mt-4")
    return layout