import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc
from utils.data_loader import load_ventas, load_actas, load_ox

def home_layout():
    df_ventas = load_ventas()
    df_actas = load_actas()
    df_ox = load_ox()

    # --- VENTAS Y ACTAS COMENTADO POR ERROR DE DATOS ---
    # if df_ventas.empty:
    #     return html.Div("No se encontraron datos de ventas válidos.", style={"color": "red"})
    # mes_col_ventas = next((col for col in df_ventas.columns if 'fech' in col.lower() or 'fecha' in col.lower() or 'period' in col.lower()), None)
    # caja_col_ventas = next((col for col in df_ventas.columns if 'caja' in col.lower() or 'cant' in col.lower() or 'unid' in col.lower()), None)
    # if not mes_col_ventas or not caja_col_ventas:
    #     return html.Div("No se encontraron columnas de fecha o caja en ventas.", style={"color": "red"})
    # if not isinstance(df_ventas[caja_col_ventas], pd.Series) or df_ventas[caja_col_ventas].dropna().empty:
    #     return html.Div("La columna de caja en ventas está vacía o no es válida.", style={"color": "red"})
    # df_ventas = df_ventas.rename(columns={mes_col_ventas: 'mes', caja_col_ventas: 'caja'})
    # df_ventas['caja'] = pd.to_numeric(df_ventas['caja'], errors='coerce').fillna(0)
    # df_ventas['mes'] = pd.to_datetime(df_ventas['mes'], format='mixed', dayfirst=True, errors='coerce').dt.to_period('M').astype(str)
    # df_ventas_grouped = df_ventas.groupby('mes', as_index=False)['caja'].sum()

    # if df_actas.empty:
    #     return html.Div("No se encontraron datos de actas válidos.", style={"color": "red"})
    # mes_col_actas = next((col for col in df_actas.columns if 'fech' in col.lower() or 'fecha' in col.lower() or 'period' in col.lower()), None)
    # caja_col_actas = next((col for col in df_actas.columns if 'caj_rec' in col.lower() or 'caja' in col.lower() or 'cajas' in col.lower() or 'rec' in col.lower()), None)
    # if not mes_col_actas or not caja_col_actas:
    #     return html.Div("No se encontraron columnas de fecha o caja en actas.", style={"color": "red"})
    # if not isinstance(df_actas[caja_col_actas], pd.Series) or df_actas[caja_col_actas].dropna().empty:
    #     return html.Div("La columna de caja en actas está vacía o no es válida.", style={"color": "red"})
    # df_actas = df_actas.rename(columns={mes_col_actas: 'mes', caja_col_actas: 'caj_rec'})
    # df_actas['caj_rec'] = pd.to_numeric(df_actas['caj_rec'], errors='coerce').fillna(0)
    # df_actas['mes'] = pd.to_datetime(df_actas['mes'], format='mixed', dayfirst=True, errors='coerce').dt.to_period('M').astype(str)
    # df_actas_grouped = df_actas.groupby('mes', as_index=False)['caj_rec'].sum()

    # --- SOLO OX ---
    if df_ox.empty:
        return html.Div("No se encontraron datos de OX válidos.", style={"color": "red"})
    mes_col_ox = next((col for col in df_ox.columns if 'fech' in col.lower() or 'fecha' in col.lower() or 'period' in col.lower()), None)
    caja_col_ox = next((col for col in df_ox.columns if 'ox' in col.lower() or 'cant' in col.lower() or 'unid' in col.lower() or 'caja' in col.lower()), None)
    if not mes_col_ox or not caja_col_ox:
        return html.Div("No se encontraron columnas de fecha o caja en OX.", style={"color": "red"})
    if not isinstance(df_ox[caja_col_ox], pd.Series) or df_ox[caja_col_ox].dropna().empty:
        return html.Div("La columna de OX está vacía o no es válida.", style={"color": "red"})
    df_ox = df_ox.rename(columns={mes_col_ox: 'mes', caja_col_ox: 'ox'})
    df_ox['ox'] = pd.to_numeric(df_ox['ox'], errors='coerce').fillna(0)
    df_ox['mes'] = pd.to_datetime(df_ox['mes'], format='mixed', dayfirst=True, errors='coerce').dt.to_period('M').astype(str)
    df_ox_grouped = df_ox.groupby('mes', as_index=False)['ox'].sum()

    # Gráfico solo OX
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_ox_grouped['mes'],
        y=df_ox_grouped['ox'],
        mode='lines+markers',
        name='OX',
        line=dict(color='green')
    ))
    fig.update_layout(
        title='Tendencia Mensual de OX',
        xaxis_title='Mes',
        yaxis_title='Cantidad de OX',
        legend_title='Categoría',
        plot_bgcolor='whitesmoke'
    )
    return html.Div([
        dcc.Graph(figure=fig)
    ])
