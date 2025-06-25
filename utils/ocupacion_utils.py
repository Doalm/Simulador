import pandas as pd
from utils.data_loader import load_layout
from utils.data_loader import load_articulos

layout = load_layout()
articulos = load_articulos()

def calcular_ocupacion_racks(df_inventario, bodega_layout_name=None, bodega_inventario=None):
    """
    Devuelve un DataFrame con la ocupación de cada rack de la bodega y zona visualizada.
    Si no se especifica bodega_layout_name, usa la primera bodega y zona del layout.
    """
    # Buscar la bodega y zona correctas
    if bodega_layout_name is None:
        wh = layout['warehouses'][0]
        zona = wh['zones'][0]
    else:
        wh = next((w for w in layout['warehouses'] if w['name'] == bodega_layout_name), None)
        if wh is None:
            return pd.DataFrame([{'Rack': 'Error: bodega no encontrada en layout'}])
        zona = wh['zones'][0] if not bodega_inventario else next((z for z in wh['zones'] if z['name'] == bodega_inventario), wh['zones'][0])
    racks = zona['racks']
    # Filtrar inventario de la bodega
    # Normaliza nombres de columnas a minúsculas para robustez
    df_inventario.columns = [c.lower() for c in df_inventario.columns]
    bodega_col = next((c for c in df_inventario.columns if 'bodega' in c), None)
    ubiart_col = next((c for c in df_inventario.columns if 'ubiart' in c), None)
    codart_col = next((c for c in df_inventario.columns if 'codart' in c), None)
    unidades_col = next((c for c in df_inventario.columns if 'unidadespresentacionlote' in c.lower()), None)
    if not all([bodega_col, ubiart_col, codart_col, unidades_col]):
        return pd.DataFrame([{'Rack': 'Error: columnas no encontradas en inventario'}])
    # Si se especifica bodega_inventario, filtrar por ese valor
    if bodega_inventario:
        df_bod = df_inventario[df_inventario[bodega_col] == bodega_inventario]
    else:
        df_bod = df_inventario
    # Prepara resultado
    rows = []
    # Calcular ocupación por volumen para cada rack
    for rack in racks:
        rack_id = rack["id"]
        # Compatibilidad: usar 'rack_size' si existe, si no 'size'
        rack_size = rack.get('rack_size') or rack.get('size')
        if not rack_size:
            continue  # saltar racks sin dimensiones
        ancho = rack_size[0]
        largo = rack_size[1]
        h = sum(rack.get("level_heights_m", [])) if rack.get("level_heights_m") else (rack_size[2] if len(rack_size) > 2 else 1)
        vol_max = ancho * largo * h
        # Filtrar inventario de la bodega y rack actual
        df_rack = df_bod[df_bod[ubiart_col] == rack_id]
        vol_ocupado = 0
        detalle = []
        for _, row in df_rack.iterrows():
            art = articulos.get(row[codart_col])
            if art:
                try:
                    # Asegurar que los valores sean numéricos antes de calcular
                    alto = float(art.get('alto_cm', 0)) / 100
                    ancho_art = float(art.get('ancho_cm', 0)) / 100
                    largo_art = float(art.get('largo _cm', 0)) / 100
                    unidades = int(row[unidades_col])
                    
                    v = alto * ancho_art * largo_art * unidades
                    vol_ocupado += v
                    detalle.append(f"{row[codart_col]} x{unidades}")
                except (ValueError, TypeError):
                    # Si hay un error en la conversión, omitir este artículo y continuar
                    print(f"Advertencia: Omitiendo artículo {row[codart_col]} por datos de dimensión inválidos.")
                    continue

        porcentaje = (vol_ocupado / vol_max) if vol_max > 0 else 0
        sobre = vol_ocupado > vol_max
        rows.append({
            'Rack': rack_id,
            'Volumen ocupado (m³)': round(vol_ocupado, 3),
            'Volumen máximo (m³)': round(vol_max, 3),
            '% Ocupación': porcentaje,
            'Sobreocupado': 'Sí' if sobre else 'No',
            'Detalle': ', '.join(detalle)
        })
    return pd.DataFrame(rows)

def calcular_ocupacion_bodega(df_inventario, bodega_layout_name=None, bodega_inventario=None):
    """
    Calcula el resumen de ocupación a nivel de bodega (no por rack):
    - Suma el volumen de todos los artículos en las ubicaciones asociadas a la bodega física.
    - Suma el volumen máximo de todos los racks de la bodega.
    - Devuelve: volumen ocupado, volumen máximo, % ocupación, volumen disponible.
    """
    # Buscar la bodega correcta
    wh = next((w for w in layout['warehouses'] if w['name'] == bodega_layout_name), None)
    if wh is None:
        return {'Bodega': bodega_layout_name, 'Volumen ocupado (m³)': 0, 'Volumen máximo (m³)': 0, '% Ocupación': 0, 'Volumen disponible (m³)': 0}
    # Sumar volumen máximo de todos los racks
    vol_max = 0
    ubicaciones_bodega = set()
    for zona in wh['zones']:
        racks_zona = zona.get('racks', [])
        for rack in racks_zona:
            # Compatibilidad: usar 'rack_size' si existe, si no 'size'
            rack_size = rack.get('rack_size') or rack.get('size')
            if not rack_size:
                continue  # saltar racks sin dimensiones
            rwidth, rlength = rack_size[0], rack_size[1]
            h = sum(rack.get('level_heights_m', [])) if rack.get('level_heights_m') else (rack_size[2] if len(rack_size) > 2 else 1)
            vol_max += rwidth * rlength * h
            ubicaciones_bodega.add(rack['id'])
    # Filtrar inventario solo por ubicaciones de la bodega física
    df_inventario.columns = [c.lower() for c in df_inventario.columns]
    ubiart_col = next((c for c in df_inventario.columns if c.startswith('ubiart')), None)
    codart_col = next((c for c in df_inventario.columns if c == 'codart'), None)
    unidades_col = next((c for c in df_inventario.columns if 'unidadespresentacionlote' in c), None)
    if not all([ubiart_col, codart_col, unidades_col]):
        return {'Bodega': bodega_layout_name, 'Volumen ocupado (m³)': 0, 'Volumen máximo (m³)': vol_max, '% Ocupación': 0, 'Volumen disponible (m³)': vol_max}
    df_bod = df_inventario[df_inventario[ubiart_col].isin(ubicaciones_bodega)]
    articulos = load_articulos()
    vol_ocupado = 0
    for _, row in df_bod.iterrows():
        art = articulos.get(row[codart_col])
        if art:
            try:
                # Asegurar que los valores sean numéricos antes de calcular
                alto = float(art.get('alto_cm', 0)) / 100
                ancho = float(art.get('ancho_cm', 0)) / 100
                largo = float(art.get('largo _cm', 0)) / 100
                unidades = int(row[unidades_col])
                vol_ocupado += alto * ancho * largo * unidades
            except (ValueError, TypeError):
                # Si hay un error en la conversión, omitir este artículo y continuar
                print(f"Advertencia: Omitiendo artículo {row[codart_col]} por datos de dimensión inválidos.")
                continue

    porcentaje = (vol_ocupado / vol_max) if vol_max > 0 else 0
    vol_disponible = vol_max - vol_ocupado
    return {
        'Bodega': bodega_layout_name,
        'Volumen ocupado (m³)': round(vol_ocupado, 3),
        'Volumen máximo (m³)': round(vol_max, 3),
        '% Ocupación': porcentaje,
        'Volumen disponible (m³)': round(vol_disponible, 3)
    }
