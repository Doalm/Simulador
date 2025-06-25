# Simulador Dash - Estructura recomendada

simulador/
├── app.py                  # Punto de entrada principal
├── assets/                 # Recursos estáticos (CSS, imágenes)
│   └── styles.css          # Estilos globales (puedes copiar de Bootstrap Dashboard)
├── components/             # Componentes reutilizables
│   └── sidebar.py          # Sidebar tipo Bootstrap
├── pages/                  # Páginas/vistas del dashboard
│   └── home.py             # Página principal con tu gráfica
├── utils/                  # Utilidades y funciones
│   └── data_loader.py      # Funciones para cargar y procesar datos
├── data/                   # Datos (ya existe)
├── requirements.txt        # Dependencias de Python
