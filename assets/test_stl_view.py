import pyvista as pv
import os

# Ruta al STL
stl_path = os.path.join(os.path.dirname(__file__), 'RackVersion_1.stl')

if not os.path.exists(stl_path):
    raise FileNotFoundError(f"No se encontró el archivo: {stl_path}")

# Cargar el STL
mesh = pv.read(stl_path)

print(f"Número de puntos: {mesh.n_points}")
print(f"Número de caras: {mesh.n_faces}")
print(f"Bounds: {mesh.bounds}")

# Visualizar
plotter = pv.Plotter()
plotter.add_mesh(mesh, color='tan', show_edges=True)
plotter.add_axes()
plotter.show(title='Visualización STL: RackVersion_1.stl')
