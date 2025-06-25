import ssl
import pandas as pd
import requests
import io
import time
import os
import json
import urllib3

# Ruta para el snapshot local
SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'inventario_snapshot.parquet')

# --- CACHE para inventario ---
_inventario_cache = {'data': None, 'timestamp': 0}
_CACHE_TTL = 600  # 10 minutos en segundos

# Desactivar advertencias de SSL (no recomendado en producción)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_ventas():
    return pd.read_parquet(r"G:\Unidades compartidas\Analisis BI\Data_Parquet\Data\venta.parquet")

def load_ox():
    return pd.read_parquet(r"G:\Unidades compartidas\Analisis BI\Data_Parquet\Data\ox.parquet")

def load_actas():
    return pd.read_parquet(r"G:\Unidades compartidas\Analisis BI\Data_Parquet\Data\actas_recepcion.parquet")


# --- NUEVO: Cargar snapshot local si existe, si no descargar y guardar ---
def load_inventario(force_refresh=False, url="https://apkit.ramedicas.com/api/items/ws-batchsunits?token=3f8857af327d7f1adb005b81a12743bc17fef5c48f228103198100d4b032f556"):
    global _inventario_cache
    now = time.time()
    # Si hay cache y no ha expirado, usarla (a menos que se pida refresh)
    if not force_refresh and _inventario_cache['data'] is not None and (now - _inventario_cache['timestamp'] < _CACHE_TTL):
        return _inventario_cache['data']
    # Intentar leer snapshot local
    if not force_refresh and os.path.exists(SNAPSHOT_PATH):
        try:
            df = pd.read_parquet(SNAPSHOT_PATH)
            _inventario_cache = {'data': df, 'timestamp': now}
            return df
        except Exception as e:
            print(f"Error leyendo snapshot local: {e}")
    # Si no hay snapshot o se pide refresh, descargar y guardar
    try:
        response = requests.get(url, timeout=60, verify=False)
        response.raise_for_status()
        data_json = response.json()
        df = pd.DataFrame(data_json)
        # Limpiar columnas innecesarias
        drop_cols = [
            'cur', 'presentacionArt', 'refProveedor', 'embalajeArt', 'invimaArt', 'fechaInvimaArt', 'cumArt',
            'descontArt', 'fFarmaceuticaArt', 'atcArt', 'vigBpmArt', 'vidaUtilArt', 'tipoArt', 'lineaArt',
            'codfabrArt', 'nomfabrArt', 'codGerapArt', 'precioControlDirectArt', 'medContrEspArt',
            'medVitDispArt', 'iumArt', 'fechaCreacion'
        ]
        for col in drop_cols:
            if col in df.columns:
                df = df.drop(columns=col)
        # Guardar snapshot local
        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        df.to_parquet(SNAPSHOT_PATH, index=False)
        _inventario_cache = {'data': df, 'timestamp': now}
        return df
    except Exception as e:
        print(f"Error al descargar inventario: {e}")
    return pd.DataFrame() 



def load_data():
    # Nuevos datos proporcionados por el usuario
    data_string = '''Descripcion;Cantidad;TipoArea;Area;Impacto
Actas Recibidas;5677;Ramedicas;Bodega;90%
Bodega A011;1;Ramedicas;Comercial;50%
Bodega C014;1;Proyectos;Proyectos;50%
Bodega D017;1;Ramedicas;Comercial;30%
Cajas Despachadas Transportadoras Mensual;15593;Ramedicas;Bodega;70%
Cantidad de Facturas Mensual;7700;Ramedicas;Bodega;80%
Cantidad de Notas Credito Mensual;727;Ramedicas;Contabilidad;30%
Cantidad Ordenes de Pedido Mensual;5569;Ramedicas;Comercial;80%
Cantidad Ordenes OX en consignacion Mensual;1313;Proyectos;Proyectos;90%
Colaboradores Bodega;143;Ramedicas;Bodega;80%
Colaboradores Cartera;5;Ramedicas;Cartera;20%
Colaboradores compras;7;Ramedicas;Compras;20%
Colaboradores Contabilidad;4;Ramedicas;Contabilidad;70%
Colaboradores Contact;15;Ramedicas;Comercial;10%
Colaboradores Dispensacion;92;Proyectos;Dispensacion;45%
Colaboradores Logistica;16;Ramedicas;Bodega;30%
Colaboradores Proyectos;28;Proyectos;Proyectos;30%
Colaboradores tecnica recepcion;5;Ramedicas;Tecnica;70%
Colaboradores Tecnica;7;Ramedicas;Tecnica;40%
Colaboradores Tesoreria;3;Ramedicas;Tesoreria;15%
Colaboradores Contact Proyectos;7;Proyectos;Proyectos;20%
Facturas Proveedores;2178;Ramedicas;Tesoreria;50%
Guias Generadas;4402;Ramedicas;Bodega;75%
Lineas Actas de recepcion;5914;Ramedicas;Tecnica;90%
Lineas Facturadas por colaborador;57136;Ramedicas;Comercial;90%
Lineas Ordenes de compra por colaborador;8248;Ramedicas;Compras;90%
Lineas OX por colaborador;17645;Proyectos;Proyectos;90%
Numero de Posiciones A011;1687;Ramedicas;Bodega;80%
Numero de Posiciones C014;331;Proyectos;Bodega;80%
Numero de Posiciones D017;70;Ramedicas;Bodega;80%
Numero de Posiciones Desnaturalizacion;315;Ramedicas;Bodega;10%
PQRS;417;Ramedicas;Comercial;33%
Presentaciones Auxiliares Tecnica por colaborador;421043;Ramedicas;Tecnica;100%
Presentaciones Contact por colaborador;102379;Ramedicas;Comercial;100%
Unidades Dispensacion por colaborador;158472;Proyectos;Dispensacion;100%
Presentaciones Proyectos por colaborador;61855;Proyectos;Proyectos;100%
Referencias Almacenadas;3804;Ramedicas;Bodega;0%
Transportadoras;10;Ramedicas;Bodega;0%
Turnos;2;Ramedicas;Bodega;0%
Unidades en consignacion;432988;Proyectos;Proyectos;100%
Unidades Facturadas;1535687;Ramedicas;Comercial;100%
Unidades Recibidas;2105216;Ramedicas;Tecnica;100%'''
    df = pd.read_csv(io.StringIO(data_string), sep=';')
    df['Cantidad'] = df['Cantidad'].astype(str).str.replace(r'\.', '', regex=True)
    df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
    # No establecer índice, mantener todas las columnas
    return df

def get_dependency_map():
    # Mapea cada 'Area' a la lista de 'Tipo' que pertenecen a esa área
    df = load_data()
    dependency_map = {}
    for area in df['Area'].unique():
        tipos = df[df['Area'] == area]['TipoArea'].tolist()
        dependency_map[area] = tipos
    return dependency_map

def load_layout(path="warehouse_layout.json"):
    base_path = os.path.dirname(os.path.dirname(__file__))
    volumetria_path = os.path.join(base_path, "Volumetria")
    config_path = os.path.join(volumetria_path, path)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_articulos(path="articulos.json"):
    base_path = os.path.dirname(os.path.dirname(__file__))
    volumetria_path = os.path.join(base_path, "Volumetria")
    articulos_path = os.path.join(volumetria_path, path)
    with open(articulos_path, "r", encoding="utf-8") as f:
        return {a['codArt']: a for a in json.load(f)}