import dash
from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd
import dash_bootstrap_components as dbc

# Layouts y callbacks personalizados
from utils.data_loader import load_ventas, load_actas, load_data, get_dependency_map
from pages.warehouse import warehouse_layout
from pages.Capacidad_bodega import register_resource_callbacks, capacidad_bodega_layout
from utils.layout_simulador import resource_simulator_layout
from pages.home import home_layout


# --- Carga de Datos ---
df_resources = load_data()
dependency_map = get_dependency_map()
df_ventas_original = load_ventas()
df_actas_original = load_actas()

# --- Funciones de Procesamiento ---
def procesar_ventas(df):
    try:
        mes_col = next(col for col in df.columns if 'fech' in col.lower())
        caja_col = next(col for col in df.columns if 'caja' in col.lower())
        df_proc = df[[mes_col, caja_col]].rename(columns={mes_col: 'mes', caja_col: 'caja'})
        df_proc['caja'] = pd.to_numeric(df_proc['caja'], errors='coerce').fillna(0)
        df_proc['mes'] = pd.to_datetime(df_proc['mes'], format='%d/%m/%Y', dayfirst=True, errors='coerce').dt.to_period('M').astype(str)
        df_proc = df_proc.dropna(subset=['mes'])
        df_grouped = df_proc.groupby('mes', as_index=False)['caja'].sum()
        df_grouped = df_grouped[df_grouped['mes'] >= '2024-07'].sort_values(by='mes')
        return df_grouped
    except Exception as e:
        print(f"Error procesando ventas: {e}")
        return pd.DataFrame(columns=['mes', 'caja'])
    
def procesar_actas(df):
    try:
        # 1. Identificar columnas automáticamente
        mes_col = next(col for col in df.columns if any(x in col.lower() for x in ['fech', 'fecha', 'period']))
        caja_col = next(col for col in df.columns if any(x in col.lower() for x in ['caj_rec', 'caja', 'cajas', 'rec']))
        
        df_proc = df[[mes_col, caja_col]].rename(columns={mes_col: 'mes', caja_col: 'caj_rec'})
        
        # 2. Convertir valores numéricos
        df_proc['caj_rec'] = pd.to_numeric(df_proc['caj_rec'], errors='coerce').fillna(0)
        
        # 3. Convertir fechas con formato flexible
        df_proc['mes'] = pd.to_datetime(df_proc['mes'], format='mixed', dayfirst=True, errors='coerce')              
        df_proc = df_proc.dropna(subset=['mes'])
        
        # 5. Extraer año y mes para agrupación
        df_proc['año'] = df_proc['mes'].dt.year
        df_proc['mes_num'] = df_proc['mes'].dt.month
        
        condicion = (
            (df_proc['año'] > 2024) | 
            ((df_proc['año'] == 2024) & (df_proc['mes_num'] >= 6))
        )
        df_filtrado = df_proc[condicion]
        df_grouped = df_filtrado.groupby(['año', 'mes_num'], as_index=False)['caj_rec'].sum()

        df_grouped = df_grouped.sort_values(by=['año', 'mes_num'])
        
        # 9. Crear columna de fecha legible (primer día del mes)
        df_grouped['mes'] = pd.to_datetime(
            df_grouped['año'].astype(str) + '-' + 
            df_grouped['mes_num'].astype(str) + '-01'
        )
        
        return df_grouped[['mes', 'caj_rec']]
        
    except Exception as e:
        print(f"Error procesando actas: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=['mes', 'caj_rec'])


# --- Procesamiento de Datos ---

df_ventas_grouped = procesar_ventas(df_ventas_original)
df_actas_grouped = procesar_actas(df_actas_original)

# --- Gráfico de Tendencias ---
def crear_figura_tendencias(df_ventas, df_actas):
    fig = go.Figure()
    if not df_ventas.empty:
        fig.add_trace(go.Scatter(
            x=df_ventas['mes'],
            y=df_ventas['caja'],
            mode='lines+markers',
            name='Cajas Vendidas',
            line=dict(color='blue')
        ))
    if not df_actas.empty:
        fig.add_trace(go.Scatter(
            x=df_actas['mes'],
            y=df_actas['caj_rec'],
            mode='lines+markers',
            name='Cajas Actas Recepción',
            line=dict(color='orange')
        ))
    fig.update_layout(
        title='Tendencia Mensual de Cajas',
        xaxis_title='Mes',
        yaxis_title='Cantidad de Cajas',
        legend_title='Categoría',
        plot_bgcolor='whitesmoke'
    )
    return fig

fig_tendencia_cajas = crear_figura_tendencias(df_ventas_grouped, df_actas_grouped)

# --- Inicialización de la Aplicación ---
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, "assets/css/style.css"],
    suppress_callback_exceptions=True
)
app.title = "Capacidades"

# --- Layout Principal ---
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Capacidades", className="text-center my-4"), width=12)),
    dcc.Tabs(id="app-tabs", value='tab-tendencias', children=[
        dcc.Tab(label='Análisis de Tendencias', value='tab-tendencias', children=[
            home_layout()
        ]),
        dcc.Tab(label='Capacidades', value='tab-capacidad', children=[
            capacidad_bodega_layout()
        ]),
        dcc.Tab(label='Ocupacion', value='tab-ocupacion', children=[
            dbc.Row([
                dbc.Col([
                    html.H2('Warehouse', className='mt-4 mb-4 text-center'),
                    html.Div(id='warehouse-ocupacion-content')
                ], width=10, className="offset-md-1")
            ])
        ]),
    ], className="mt-3")
], fluid=True, className="py-3")

# --- Callbacks ---
register_resource_callbacks(app, df_resources, dependency_map)

# --- Callback para cargar warehouse_layout solo al seleccionar la pestaña ---
from dash import Output, Input
@app.callback(
    Output('warehouse-ocupacion-content', 'children'),
    Input('app-tabs', 'value')
)
def render_warehouse_content(tab):
    if tab == 'tab-ocupacion':
        from pages.warehouse import warehouse_layout
        return warehouse_layout(only_occupation=True)
    return None

# --- Ejecutar Aplicación ---
if __name__ == '__main__':
    app.run(debug=True)
