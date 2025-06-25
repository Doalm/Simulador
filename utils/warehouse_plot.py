import json
import os
import pyvista as pv
import plotly.graph_objects as go
# Usa load_layout desde data_loader, no lo redefinas aquí
from utils.data_loader import load_layout




def get_warehouse_by_name(layout_data, warehouse_name):
    for wh in layout_data.get("warehouses", []):
        if wh["name"] == warehouse_name:
            return wh
    return None

def get_zone_by_name(warehouse, zone_name):
    for z in warehouse.get("zones", []):
        if z["name"] == zone_name:
            return z
    return None

COLORS_PV = {
    "estanteria": "tan",
    "pasillo": "lightgrey",
    "punto_entrada": "red",
    "Bodega_13": "lightgreen",
    "Facturacion_Bodega_13": "pink",
    "Zona_Administrativa": "lightblue",
    "fondo_zona": "ghostwhite"
}

def create_warehouse_scene_pyvista(layout):
    plotter = pv.Plotter(window_size=[1200, 800])

    # Suelo X–Z
    dims = layout.get("dimensions", {})
    W, L = dims.get("width_m", 50), dims.get("length_m", 50)
    floor = pv.Plane(center=(W/2, 0, L/2), i_size=W, j_size=L)
    plotter.add_mesh(floor, color='gainsboro', show_edges=True, edge_color='grey')

    for zone in layout.get("zones", []):
        zx0, zz0 = zone["position"]   # 'y' del JSON se usa como Z
        zw, zl   = zone["size"]
        zone_color = COLORS_PV.get(zone.get("name"), COLORS_PV["fondo_zona"])

        # Plano de zona en X–Z
        zplane = pv.Plane(center=(zx0+zw/2, 0.01, zz0+zl/2), i_size=zw, j_size=zl)
        plotter.add_mesh(zplane, color=zone_color)

        # Racks (cajas 3D)
        for rack in zone.get("racks", []):
            dx, dz = rack["position"]
            rw, rl = rack["rack_size"]  # ancho, largo
            rh = sum(rack.get("level_heights_m", [])) or 1.0  # altura

            xmin, xmax = zx0+dx, zx0+dx+rw
            zmin, zmax = zz0+dz, zz0+dz+rl
            ymin, ymax = 0, rh

            box = pv.Box(bounds=[xmin, xmax, ymin, ymax, zmin, zmax])
            plotter.add_mesh(box, color=COLORS_PV["estanteria"], show_edges=True, edge_color='black')

        # Pasillos (planos en X–Z por encima de la zona)
        for aisle in zone.get("aisles", []):
            dx, dz = aisle["position"]
            aw, al = aisle["width_m"], aisle["length_m"]
            aisle_plane = pv.Plane(
                center=(zx0+dx+aw/2, 0.02, zz0+dz+al/2),
                i_size=aw, j_size=al
            )
            plotter.add_mesh(aisle_plane, color=COLORS_PV["pasillo"], opacity=0.7)

    # Puntos de entrada (cajas bajas)
    for ep in layout.get("entry_points", []):
        ex, ez = ep["position"]
        ew, el = ep["size"]
        entry_box = pv.Box(bounds=[ex, ex+ew, 0, 0.2, ez, ez+el])
        plotter.add_mesh(entry_box, color=COLORS_PV["punto_entrada"], show_edges=True, edge_color='black')

    plotter.camera_position = 'iso'
    plotter.add_axes()
    plotter.background_color = 'white'
    return plotter

def create_3d_warehouse(layout_data, inventario_df=None, articulos_dict=None, warehouse_name=None):
    """Crea la visualización 3D del almacén usando Plotly, con orientación y proporciones correctas.
    inventario_df: DataFrame de inventario vivo (load_inventario)
    articulos_dict: dict de articulos por codart (load_articulos)
    warehouse_name: nombre de la bodega (para filtrar inventario)
    """
    import numpy as np
    fig = go.Figure()
    if not layout_data:
        return fig
    colors = {
        "floor": "#ADADAD",
        "walls": "#ffffff",
        "racks": "#ff5800",
        "zones": "#e0e0e0"
    }
    if "dimensions" in layout_data:
        dims = layout_data["dimensions"]
    else:
        dims = layout_data.get("warehouses", [{}])[0].get("dimensions", {})
    W, L, H = dims.get("width_m", 35), dims.get("length_m", 15), dims.get("height_m", 6)
    corner_x = [0, W, 0, W, 0, W, 0, W]
    corner_y = [0, 0, L, L, 0, 0, L, L]
    corner_z = [0, 0, 0, 0, H, H, H, H]
    fig.add_trace(go.Scatter3d(
        x=corner_x, y=corner_y, z=corner_z,
        mode="markers",
        marker=dict(size=1, color="#000", opacity=0),
        showlegend=False,
        hoverinfo="skip"
    ))
    floor_x = [0, W, W, 0]
    floor_y = [0, 0, L, L]
    floor_z = [0, 0, 0, 0]
    fig.add_trace(go.Mesh3d(
        x=floor_x, y=floor_y, z=floor_z,
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=colors["floor"],
        opacity=1.0,
        name="Piso"
    ))
    fig.add_trace(go.Mesh3d(
        x=[0, 0, 0, 0],
        y=[0, L, L, 0],
        z=[0, 0, H, H],
        i=[0], j=[1], k=[2],
        color=colors["walls"], opacity=0.1, name="Pared x=0"
    ))
    fig.add_trace(go.Mesh3d(
        x=[W, W, W, W],
        y=[0, L, L, 0],
        z=[0, 0, H, H],
        i=[0], j=[1], k=[2],
        color=colors["walls"], opacity=0.1, name="Pared x=W"
    ))
    fig.add_trace(go.Mesh3d(
        x=[0, W, W, 0],
        y=[0, 0, 0, 0],
        z=[0, 0, H, H],
        i=[0], j=[1], k=[2],
        color=colors["walls"], opacity=0.1, name="Pared y=0"
    ))
    fig.add_trace(go.Mesh3d(
        x=[0, W, W, 0],
        y=[L, L, L, L],
        z=[0, 0, H, H],
        i=[0], j=[1], k=[2],
        color=colors["walls"], opacity=0.1, name="Pared y=L"
    ))
    for zone in layout_data.get("zones", []):
        x0, y0 = zone["position"]
        width, length = zone["size"]
        zone_type = zone.get("type", "")
        if zone_type == "administrativo":
            zone_color = "#f2f2f2"
        else:
            zone_color = colors["zones"]
        zx = [x0, x0+width, x0+width, x0]
        zy = [y0, y0, y0+length, y0+length]
        zz = [0.01, 0.01, 0.01, 0.01]
        fig.add_trace(go.Mesh3d(
            x=zx, y=zy, z=zz,
            i=[0], j=[1], k=[2],
            color=zone_color, opacity=0.2, name=zone.get("name", "Zona")
        ))
        racks = zone.get("racks", [])
        for rack in racks:
            # --- MODIFICADO: Leer posición [x, y, z] ---
            pos = rack.get("position", [0, 0, 0])
            if len(pos) == 3:
                rx0, ry0, rz0 = pos
            else:  # Compatibilidad con [x, y]
                rx0, ry0 = pos
                rz0 = 0

            rwidth, rlength = rack["rack_size"][:2]
            H_max = sum(rack.get("level_heights_m", [])) or 4
            rack_id = rack.get("id")
            # --- INVENTARIO Y HOVER ---
            hover_lines = [f"<b>Rack: {rack_id}</b>"]
            rack_inv = None
            # Normalizar nombres de columnas a minúsculas para evitar errores de KeyError
            if inventario_df is not None:
                inventario_df.columns = [c.lower() for c in inventario_df.columns]
                # Buscar nombres de columna equivalentes
                ubiart_col = next((c for c in inventario_df.columns if c.lower() in ["ubiart", "ubicacionart", "ubicacion_art", "ubicacion"]), None)
                bodega_col = next((c for c in inventario_df.columns if "bodega" in c.lower()), None)
                # Mapeo de bodega para filtrar correctamente según warehouse_name
                bodega_map = {
                    "Principal": {"A011", "C010", "C015", "C018"},
                    "Principal_Mezzanine": {"A011", "C010", "C015", "C018"},
                    "Principal_Alturas": {"A011", "C010", "C015", "C018"},
                    "Bodega_13": {"D017"},
                    # Agrega más si tienes más bodegas físicas
                }
                if warehouse_name in bodega_map and ubiart_col and bodega_col:
                    rack_inv = inventario_df[
                        (inventario_df[ubiart_col] == rack_id) &
                        (inventario_df[bodega_col].isin(bodega_map[warehouse_name]))
                    ]
                else:
                    rack_inv = None
            # DEBUG: Imprimir columnas y valores para depuración
            codart_lines = []
            total_unidades = 0
            total_volumen = 0
            # Buscar nombres de columna equivalentes para codArt, lote y unidadesPresentacionLote
            codart_col = next((c for c in inventario_df.columns if c.lower() == "codart"), None)
            lote_col = next((c for c in inventario_df.columns if "lote" in c.lower()), None)
            unidades_col = next((c for c in inventario_df.columns if "unidadespresentacionlote" in c.lower()), None)
            if rack_inv is not None and not rack_inv.empty and codart_col and lote_col and unidades_col:
                # Agrupar por codArt y lote
                grouped = rack_inv.groupby([codart_col, lote_col], dropna=False)
                for (codart, lote), group in grouped:
                    unidades = group[unidades_col].sum()
                    total_unidades += unidades
                    art = articulos_dict.get(codart) if articulos_dict else None
                    if art:
                        try:
                            # Asegurar que las dimensiones sean numéricas antes de calcular
                            alto = float(art.get('alto_cm', 0))
                            ancho = float(art.get('ancho_cm', 0))
                            largo = float(art.get('largo _cm', 0))
                            
                            volumen = (alto * ancho * largo) / 1e6  # m3
                            volumen_total = volumen * unidades
                            total_volumen += volumen_total
                        except (ValueError, TypeError):
                            volumen_total = None
                            print(f"Advertencia: Omitiendo artículo {codart} en el gráfico 3D por datos de dimensión inválidos.")
                    else:
                        volumen_total = None
                    codart_line = f"• {codart}: {int(unidades)}u"
                    if lote:
                        codart_line += f" (Lote: {lote})"
                    if volumen_total is not None:
                        codart_line += f" [{volumen_total:.2f} m³]"
                    codart_lines.append(codart_line)
            else:
                codart_lines.append("Vacío")
            # Ocupación y capacidad
            capacidad = rack.get("capacidad") or rack.get("slots") or total_unidades or 1
            # Calcular ocupación por volumen: vol_ocupado / vol_max
            vol_max = (sum(rack.get("level_heights_m", [])) * rwidth * rlength) if rack.get("level_heights_m") else H_max * rwidth * rlength
            vol_ocupado = total_volumen if total_volumen > 0 else 0  # 0 si vacío
            ocup = (vol_ocupado / vol_max) if vol_max > 0 else 0
            ocup_min = max(ocup, 0.1) if vol_ocupado > 0 else 0.1
            h = H_max * ocup_min
            hover_lines.append(f"Ocupación (vol_ocupado/vol_max): {ocup*100:.1f}% ({vol_ocupado:.2f} m³ / {vol_max:.2f} m³)")
            hover_lines.append(f"Volumen total ocupado: {total_volumen:.2f} m³")
            hover_lines += codart_lines
            hovertext = "<br>".join(hover_lines)
            
            # --- MODIFICADO: Usar rz0 como altura base ---
            v = [
                (rx0,        ry0,        rz0),
                (rx0+rwidth, ry0,        rz0),
                (rx0+rwidth, ry0+rlength, rz0),
                (rx0,        ry0+rlength, rz0),
                (rx0,        ry0,        rz0 + h),
                (rx0+rwidth, ry0,        rz0 + h),
                (rx0+rwidth, ry0+rlength, rz0 + h),
                (rx0,        ry0+rlength, rz0 + h)
            ]
            faces = [
                (0,1,2),(0,2,3),
                (4,5,6),(4,6,7),
                (0,1,5),(0,5,4),
                (1,2,6),(1,6,5),
                (2,3,7),(2,7,6),
                (3,0,4),(3,4,7)
            ]
            x, y, z = zip(*v)
            i, j, k = zip(*faces)
            fig.add_trace(go.Mesh3d(
                x=x, y=y, z=z,
                i=i, j=j, k=k,
                intensity=[ocup]*len(v),
                colorscale="RdYlGn_r",
                cmin=0, cmax=1,
                intensitymode="cell",
                showscale=False,
                name=rack_id,
                hoverinfo="text",
                hovertext=hovertext
            ))
            # --- NUEVO: Agregar wireframe/bordes con Scatter3d ---
            edges = [
                (0,1),(1,2),(2,3),(3,0), # base
                (4,5),(5,6),(6,7),(7,4), # top
                (0,4),(1,5),(2,6),(3,7)  # verticals
            ]
            for e0, e1 in edges:
                fig.add_trace(go.Scatter3d(
                    x=[x[e0], x[e1]],
                    y=[y[e0], y[e1]],
                    z=[z[e0], z[e1]],
                    mode="lines",
                    line=dict(color="black", width=2),
                    showlegend=False,
                    hoverinfo="skip"
                ))
    fig.update_layout(
        title="Visualización 3D del Almacén (wireframe)",
        scene=dict(
            xaxis_title="X (Ancho)",
            yaxis_title="Y (Largo)",
            zaxis_title="Z (Alto)",
            aspectmode='data',
            bgcolor="#f8f8f8",
            xaxis=dict(range=[0, W]),
            yaxis=dict(range=[0, L]),
            zaxis=dict(range=[0, H]),
        ),
        showlegend=False,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    return fig
