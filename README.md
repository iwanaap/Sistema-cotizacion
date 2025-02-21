👌 Sistema de Cotización

El Sistema de Cotización es una aplicación web construida con Flask y SQLite, que permite gestionar clientes y generar cotizaciones en formato PDF.

🚀 Características

✅ Gestión de clientes (agregar, editar, eliminar).✅ Creación y edición de cotizaciones con productos detallados.✅ Generación de cotizaciones en PDF con formato profesional.✅ Cálculo automático de IVA y totales.✅ Interfaz responsiva con Bootstrap.✅ Autocompletado de datos de clientes.✅ Base de datos SQLite para almacenamiento local.

🛠️ Instalación

1⃣ Clonar el repositorio

git clone https://github.com/iwanaap/Sistema-cotizacion.git
cd Sistema-de-Cotizacion

2⃣ Crear un entorno virtual (opcional pero recomendado)

python -m venv venv
source venv/bin/activate  # En macOS/Linux
venv\Scripts\activate     # En Windows

3⃣ Instalar las dependencias

pip install -r requirements.txt

4⃣ Ejecutar la aplicación

python app.py

La aplicación se ejecutará en http://127.0.0.1:5000/.

📂 Estructura del Proyecto

Sistema-de-Cotizacion/

│── static/              # Archivos estáticos (CSS, imágenes, etc.)

│── templates/           # Plantillas HTML

│── app.py               # Archivo principal de la aplicación Flask

│── clientes.py          # Módulo de gestión de clientes

│── editar.py            # Módulo para editar cotizaciones

│── cotizaciones.db      # Base de datos SQLite (NO SE DEBE SUBIR A GITHUB)

│── requirements.txt     # Dependencias del proyecto

│── .gitignore           # Archivos a ignorar en Git

│── README.md            # Documentación del proyecto

🖥️ Uso de la Aplicación

1⃣ Gestión de Clientes

Desde la página principal, puedes agregar, editar y eliminar clientes.

Los clientes registrados pueden ser autocompletados al crear una cotización.

2⃣ Creación de Cotizaciones

Se pueden agregar productos con cantidad, precio y formato.

El sistema calcula el total neto, IVA (19%) y total final automáticamente.

3⃣ Generación de PDF

Cada cotización puede descargarse como archivo PDF con un diseño profesional.

⚙️ Configuración Adicional

Si deseas personalizar el sistema, edita los archivos dentro de templates/ y static/.

Para cambiar el formato de los PDFs, modifica el archivo pdf.html en la carpeta templates/.

🤝 Contribuciones

Si deseas mejorar el sistema, ¡eres bienvenido! Puedes enviar un pull request o reportar errores en la sección de Issues.

🐝 Licencia

Este proyecto se encuentra bajo la licencia MIT, por lo que puedes modificarlo y distribuirlo libremente.

💪 Hecho con pasión por Nelson Landaeta.