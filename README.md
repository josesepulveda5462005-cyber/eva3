# Ludix | Tienda digital de videojuegos

## Ficha de Registro y Aprobación de la Propuesta

| Campo | Detalle |
|---|---|
| **Nombre de la Organización o Plataforma:** | Ludix |
| **Modelo de Negocio / Giro:** | Catálogo y venta simulada de videojuegos digitales |
| **Integrantes del Equipo:** | José Sepúlveda - RUT: 21.927.528-5 (Desarrollo Individual) |
| **Entidad de Contexto / Agrupación (ORM):** | Género de videojuego (`Genre`) |
| **Entidad Principal Gestionable (ORM):** | Videojuego (`Game`) |
| **Propósito de la Sesión (request.session):** | Carrito temporal con cantidades, validación de stock y desglose económico (subtotal neto, IVA 19% y total) antes de emitir una solicitud de compra simulada |

## Funcionalidades

- Catálogo público con búsqueda por título, código, plataforma y descripción, filtro por género, orden y paginación.
- Fichas de juegos reales y conocidos con precios/stock ficticios de demostración, y portada opcional.
- Registro, inicio y cierre de sesión; perfil asociado con RUT y teléfono.
- Carrito almacenado en `request.session`, con edición de cantidades, control de stock, subtotales y total.
- Confirmación de compra simulada: crea un comprobante persistente, descuenta el stock y vacía el carrito.
- CRUD protegido para personal autorizado. La eliminación es una baja lógica para conservar el historial.
- Django Admin personalizado para géneros, videojuegos, perfiles y solicitudes.
- Comando `poblar_datos` con cuatro géneros, doce videojuegos reales y usuarios de demostración.

La carpeta `images/` contiene las portadas proporcionadas para la evaluación. Ludix las muestra asociadas al título correspondiente y admite cambiar o subir otras imágenes desde el panel de administración.

El catálogo de demostración incluye *Assassin's Creed Unity*, *Assassin's Creed II*, *Grand Theft Auto: San Andreas*, *Grand Theft Auto V*, *Red Dead Redemption 2*, *The Witcher 3: Wild Hunt*, *Cyberpunk 2077*, *Minecraft*, *Elden Ring*, *Age of Empires II: Definitive Edition*, *Stardew Valley* y *Forza Horizon 5*. Precios y stock son datos ficticios para la evaluación; la tienda no procesa pagos reales.

## Requisitos

- Python 3.10 o superior
- pip

## Instalación local (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py poblar_datos
python manage.py runserver
```

Abrir http://127.0.0.1:8000/. Para entrar al panel de administración, abrir http://127.0.0.1:8000/admin/.

En Windows, si PowerShell bloquea la activación del entorno, ejecutar `.\.venv\Scripts\python.exe` en lugar de `python` o activar el entorno desde una terminal autorizada.

## Usuarios de demostración

`python manage.py poblar_datos` crea estas cuentas locales únicamente si no existen:

| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | `admin` | `AdminLudix2026!` |
| Cliente | `jugador` | `JugadorLudix2026!` |

Son credenciales públicas para desarrollo y evaluación local. No reutilizarlas ni desplegarlas en producción. Para personalizar la clave del administrador en la primera carga, definir `LUDIX_ADMIN_PASSWORD` antes de ejecutar el comando. El admin de Django queda disponible en `/admin/`.

## Variables de entorno

`settings.py` carga el archivo `.env` con `python-dotenv`. `.env.example` contiene valores locales de ejemplo; cambiar `DJANGO_SECRET_KEY` y desactivar `DJANGO_DEBUG` en cualquier despliegue. No subir `.env` al repositorio.

## Pruebas y tareas útiles

```powershell
python manage.py test
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

Las portadas se guardan bajo `media/game_covers/`. Para entregar un ZIP, excluir `.venv/`, `db.sqlite3`, `.env` y archivos temporales.

## Bitácora de prompts de IA

1. **Arquitectura de datos**
   - **Prompt:** «Propón modelos Django para una tienda digital de videojuegos con géneros y productos, validación de precio y stock, imagen, disponibilidad y baja lógica».
   - **Respuesta técnica:** Separar la clasificación `Genre` del recurso `Game`, usar `ForeignKey(..., on_delete=PROTECT)`, validadores numéricos, opciones cerradas, `ImageField` y un indicador de vigencia.
   - **Adaptación aplicada:** Se implementaron `Genre` y `Game`; los productos desactivados no aparecen en el catálogo y su género no se puede borrar si tiene videojuegos asociados.

2. **Carrito y consultas**
   - **Prompt:** «¿Cómo implementar en Django un carrito de videojuegos en sesión, evitando confiar en precios enviados desde el navegador y calculando el total con Decimal?».
   - **Respuesta técnica:** Guardar solo identificadores y cantidades en `request.session`; volver a consultar productos y precios en el servidor, validar disponibilidad y usar `Decimal`.
   - **Adaptación aplicada:** El carrito guarda `{game_id: quantity}`. El checkout revalida el stock dentro de una transacción, persiste precios en el comprobante y descuenta las unidades confirmadas.

3. **Autorización y formularios**
   - **Prompt:** «¿Qué controles usar para proteger un CRUD Django de videojuegos y procesar portadas de forma segura?».
   - **Respuesta técnica:** Restringir cada vista con autenticación y rol autorizado, usar `ModelForm`, validar en servidor, mantener CSRF en formularios POST y enviar archivos mediante `request.FILES`.
   - **Adaptación aplicada:** El CRUD exige `login_required` y `user_passes_test(is_staff)`. Los formularios incluyen validación del identificador y precio, `{% csrf_token %}` y el formulario multipart procesa portadas.

## Diseño técnico

- **Framework:** Django 5.2
- **Persistencia local:** SQLite (ruta configurable con `DATABASE_PATH`)
- **Multimedia:** Pillow e `ImageField`
- **Interfaz:** Bootstrap 5 y estilos propios
- **Zona horaria:** `America/Santiago`
