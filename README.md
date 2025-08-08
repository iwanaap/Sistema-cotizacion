# Sistema de Cotización

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.1.0-green)
![SQLite](https://img.shields.io/badge/SQLite-3-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

El Sistema de Cotización es una aplicación web profesional construida con Flask y SQLite, diseñada para simplificar la gestión de clientes y la generación de cotizaciones en formato PDF para pequeñas y medianas empresas.

## 🚀 Características

- **Gestión de Clientes**
  - Agregar, editar y eliminar información de clientes
  - Base de datos SQLite para almacenamiento persistente
  - Interfaz intuitiva para manejo de datos

- **Sistema de Cotizaciones**
  - Creación y edición de cotizaciones con productos detallados
  - Autocompletado de datos de clientes existentes
  - Cálculo automático de IVA (19%) y totales
  - Generación de cotizaciones en PDF con formato profesional

- **Interfaz de Usuario**
  - Diseño responsivo con Bootstrap
  - Navegación intuitiva
  - Experiencia de usuario optimizada

## ⚙️ Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- wkhtmltopdf (necesario para la generación de PDFs)

## 🛠️ Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/iwanaap/Sistema-cotizacion.git
   cd Sistema-cotizacion
   ```

2. **Crear un entorno virtual**
   ```bash
   python -m venv venv
   
   # En Windows
   .\venv\Scripts\activate
   
   # En macOS/Linux
   source venv/bin/activate
   ```

3. **Instalar las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar la base de datos**
   ```bash
   # La base de datos se inicializará automáticamente al ejecutar la aplicación
   python app.py
   ```

5. **Iniciar la aplicación**
   ```bash
   python app.py
   ```

La aplicación estará disponible en `http://127.0.0.1:5000/`

## 📂 Estructura del Proyecto

```
Sistema-cotizacion/
├── static/                 # Archivos estáticos
│   ├── css/               # Hojas de estilo
│   ├── js/                # Scripts de JavaScript
│   └── img/               # Imágenes
├── templates/             # Plantillas HTML
│   ├── clientes.html      # Vista de gestión de clientes
│   ├── crear.html         # Formulario de creación
│   ├── editar.html        # Vista de edición
│   ├── index.html         # Página principal
│   └── pdf.html           # Plantilla para PDFs
├── app.py                 # Aplicación principal Flask
├── clientes.py           # Módulo de gestión de clientes
├── editar.py             # Módulo de edición de cotizaciones
├── requirements.txt      # Dependencias del proyecto
└── README.md             # Documentación
```

## 📱 Guía de Uso

### Gestión de Clientes
- Accede a la sección de clientes desde el menú principal
- Agrega nuevos clientes con su información completa
- Edita o elimina clientes existentes
- Utiliza el autocompletado al crear cotizaciones

### Creación de Cotizaciones
- Selecciona un cliente existente o ingresa uno nuevo
- Agrega productos con:
  - Descripción detallada
  - Cantidad
  - Precio unitario
- El sistema calculará automáticamente:
  - Subtotal
  - IVA (19%)
  - Total final

### Generación de PDFs
- Previsualiza la cotización antes de generar el PDF
- Personaliza el formato según tus necesidades
- Descarga o envía el PDF directamente

## ⚙️ Personalización

### Modificar el Diseño
- Personaliza las plantillas HTML en `/templates`
- Ajusta los estilos CSS en `/static/css`
- Modifica el formato PDF en `templates/pdf.html`

### Configuración del Sistema
- Ajusta el porcentaje de IVA en `app.py`
- Personaliza los campos de clientes en `clientes.py`
- Modifica las validaciones en `editar.py`

## 🛡️ Seguridad

- La base de datos SQLite (`cotizaciones.db`) se genera automáticamente
- No se incluye en el repositorio por seguridad
- Se recomienda realizar backups periódicos

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Haz un Fork del proyecto
2. Crea una rama para tu característica (`git checkout -b feature/AmazingFeature`)
3. Haz commit de tus cambios (`git commit -m 'Add: nueva característica'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## � Licencia

Este proyecto está bajo la licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👤 Autor

**Nelson Landaeta**
- GitHub: [@iwanaap](https://github.com/iwanaap)

---
⭐ Si este proyecto te fue útil, considera darle una estrella en GitHub.