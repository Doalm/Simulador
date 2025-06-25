import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from components.sidebar import sidebar
from pages.home import home_layout

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(fluid=True, children=[
    dbc.Row([
        dbc.Col(sidebar, width=2),
        dbc.Col(home_layout, width=10)
    ])
])

if __name__ == "__main__":
    app.run(debug=True)
