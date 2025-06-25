import pandas as pd
import json

# Paths
excel_file_path = r"G:\Unidades compartidas\Capacidades\Simulador\Volumetria\BaseProductos_Normalizado.xlsx"
json_file_path = R"G:\Unidades compartidas\Capacidades\Simulador\Volumetria\articulos.json"


excel_reader = pd.read_excel(excel_file_path, engine='openpyxl')
# Convertir a JSON (orientado por registros = lista de diccionarios)

excel_reader.to_json('articulos.json', orient='records', force_ascii=False, indent=4)

print(f"Conversión completada. Archivo guardado como {json_file_path}.")