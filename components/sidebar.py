import dash_bootstrap_components as dbc
from dash import html

sidebar = html.Div([
    html.Div([
        html.H2("Simulador", className="sidebar-brand d-flex align-items-center justify-content-center mb-4"),
    ], className="sidebar-header p-3 border-bottom"),
    dbc.Nav([
        dbc.NavLink([
            html.I(className="mdi mdi-view-dashboard me-2"),
            "Dashboard"
        ], href="/", active="exact", className="sidebar-link"),
        dbc.NavLink([
            html.I(className="mdi mdi-file-chart me-2"),
            "Reportes"
        ], href="/reportes", active="exact", className="sidebar-link"),
    ],
    vertical=True,
    pills=True,
    className="nav flex-column nav-pills sidebar-nav"
    )
], className="sidebar bg-white shadow-sm vh-100 p-0 border-end")
