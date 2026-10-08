# El Diario Tecsup — Portal de Noticias con Django

Laboratorio 6 de Django: portal de noticias con modelos relacionados, herencia de plantillas,
fragmentos reutilizables, archivos estáticos y de medios, panel de administración personalizado
y verificación del escapado automático de HTML.

**Autor:** Luis Cucho — Tecsup

## Tecnologías

| Herramienta | Versión |
|-------------|---------|
| Python      | 3.14    |
| Django      | 6.1.2   |
| Pillow      | 12.3.0  |
| Base de datos | SQLite |

## Instalación

```bash
git clone https://github.com/luiscucho-oss/django-news-portal.git
cd django-news-portal

python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_news      # 3 categorías, 3 autores y 5 noticias con imagen
python manage.py runserver
```

- Sitio: <http://127.0.0.1:8000/>
- Administración: <http://127.0.0.1:8000/admin/>

La sexta noticia («Feria del Libro de Lima rompe récord de visitantes») se registra
manualmente desde el administrador; es la que contiene la prueba de escapado.

## Estructura del proyecto

```
django-news-portal/
├── portal/                  # Proyecto (settings.py, urls.py)
├── news/                    # Aplicación
│   ├── models.py            # Category, Author, Article
│   ├── views.py             # home, article_detail, category_list
│   ├── urls.py              # Rutas con nombre (app_name = 'news')
│   ├── admin.py             # list_display, list_filter, search_fields
│   ├── context_processors.py
│   ├── tests.py             # Casos de prueba
│   └── management/commands/seed_news.py
├── templates/
│   ├── base.html            # Bloques: title, content, sidebar
│   └── news/
│       ├── _article_card.html   # Fragmento: tarjeta de noticia
│       ├── _category_tags.html  # Fragmento: etiquetas de categoría
│       ├── _back_link.html      # Fragmento: enlace a la portada
│       ├── home.html
│       ├── article_detail.html
│       └── category_list.html
├── static/css/styles.css
├── media/                   # Imágenes subidas (no se versiona)
└── docs/capturas/           # Capturas de pantalla
```

## Desarrollo del laboratorio

### 1. Configuración (`portal/settings.py` y `portal/urls.py`)

```python
INSTALLED_APPS = [..., 'news']

TEMPLATES = [{ 'DIRS': [BASE_DIR / 'templates'], ... }]

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

```python
# portal/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('news.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 2. Modelos

| Modelo     | Campos principales | Relaciones |
|------------|--------------------|------------|
| `Category` | `name`, `slug`, `description` | — |
| `Author`   | `name`, `email`, `bio` | — |
| `Article`  | `title`, `slug`, `summary`, `body`, `image` (ImageField), `published_at` | `author` → ForeignKey a `Author`; `categories` → ManyToMany a `Category` |

### 3. Plantillas

#### Herencia (`extends`) e inclusión (`include`)

```
base.html                         ← estructura común: <head>, menú, barra lateral, pie
│   {% block title %}  {% block content %}  {% block sidebar %}
│
├── news/home.html                (extends)  → for/empty sobre las noticias
│     └── include _article_card.html
│               └── include _category_tags.html
│
├── news/category_list.html       (extends)  → misma tarjeta, filtrada por categoría
│     ├── include _article_card.html
│     │         └── include _category_tags.html
│     └── include _back_link.html
│
└── news/article_detail.html      (extends)  → noticia completa + sidebar propio con {{ block.super }}
      ├── include _category_tags.html
      └── include _back_link.html
```

Los nombres de los fragmentos empiezan con `_` para distinguirlos de las páginas completas.
Ningún bloque de marcado está copiado en dos plantillas: lo que se repite vive en `base.html`
o en un fragmento.

| Plantilla | Tipo | Qué hace |
|-----------|------|----------|
| `base.html` | Base | Carga el CSS con `{% load static %}`, arma el menú de categorías y define los bloques `title`, `content` y `sidebar`. |
| `home.html` | Página | Recorre las noticias con `{% for %}` y muestra `{% empty %}` si no hay ninguna. |
| `article_detail.html` | Página | Imagen, autor, fecha con `\|date`, cuerpo con `\|linebreaks`, biografía con `\|default` y noticias relacionadas. Amplía la barra lateral con `{{ block.super }}`. |
| `category_list.html` | Página | Título y descripción de la categoría (`{% if %}`) y sus noticias, reutilizando la tarjeta. |
| `_article_card.html` | Fragmento | Tarjeta de noticia: imagen, título, autor, fecha (`\|date`) y resumen (`\|truncatewords:25`). |
| `_category_tags.html` | Fragmento | Etiquetas de categoría enlazadas. Recibe la lista con `{% include ... with categories=... %}`. |
| `_back_link.html` | Fragmento | Enlace «Volver a la portada» con `{% url 'news:home' %}`. |

#### Etiquetas y filtros utilizados

| Etiqueta / filtro | Dónde | Para qué |
|-------------------|-------|----------|
| `{% extends %}` / `{% block %}` | Todas las páginas | Herencia de `base.html` |
| `{% include ... with %}` | Portada, detalle, categoría | Fragmentos reutilizables |
| `{% for %}` / `{% empty %}` | Portada, categoría, menú, relacionadas | Recorrer listas y manejar el caso sin datos |
| `{% if %}` | Categoría | Mostrar la descripción solo si existe |
| `{% url %}` | Todos los enlaces | Generar rutas por nombre |
| `{% load static %}` / `{% static %}` | `base.html` | Cargar la hoja de estilos |
| `{% now "Y" %}` | Pie de página | Año actual |
| `\|date` | Tarjeta y detalle | Fecha en formato «07 de octubre de 2026» |
| `\|truncatewords:25` | Tarjeta | Recortar el resumen |
| `\|linebreaks` | Detalle | Convertir los saltos de línea del cuerpo en párrafos |
| `\|default` | Detalle | Texto alternativo si el autor no tiene biografía |

La lógica de consulta (filtrar por categoría, noticias relacionadas, conteo de noticias por categoría)
está en las vistas y en el procesador de contexto `news/context_processors.py`, no en las plantillas.

### 4. URLs con nombre

```python
app_name = 'news'

urlpatterns = [
    path('', views.home, name='home'),
    path('noticia/<slug:slug>/', views.article_detail, name='article_detail'),
    path('categoria/<slug:slug>/', views.category_list, name='category'),
]
```

En las plantillas todos los enlaces usan `{% url 'news:home' %}`,
`{% url 'news:article_detail' article.slug %}` y `{% url 'news:category' category.slug %}`;
no hay direcciones escritas a mano.

### 5. Administración

| Modelo   | `list_display` | `list_filter` | `search_fields` |
|----------|----------------|---------------|-----------------|
| Noticia  | título, autor, categorías, fecha | categorías, autor, fecha | título, resumen, cuerpo, autor |
| Categoría| nombre, slug, n.º de noticias | fecha de las noticias | nombre, descripción |
| Autor    | nombre, correo, n.º de noticias | categorías de sus noticias | nombre, correo, biografía |

## Capturas de pantalla

### Sitio público

**Portada** — seis noticias en tres categorías, con fecha formateada y resumen recortado.

![Portada](docs/capturas/09-portada.png)

**Detalle de una noticia** — imagen destacada, autor, fecha y categorías enlazadas.

![Detalle](docs/capturas/10-detalle.png)

**Listado por categoría (Cultura)** — reutiliza el fragmento `_article_card.html`.

![Categoría Cultura](docs/capturas/11-categoria-cultura.png)

**Estado vacío** — `{% empty %}` cuando una categoría no tiene noticias.

![Categoría vacía](docs/capturas/12-categoria-vacia.png)

**Vista móvil**

<img src="docs/capturas/16-portada-movil.png" alt="Portada en móvil" width="320">

### Panel de administración

**Inicio de sesión del superusuario**

![Login](docs/capturas/01-admin-login.png)

**Inicio del administrador**

![Admin inicio](docs/capturas/02-admin-inicio.png)

**Registro de una noticia desde el administrador**

![Nueva noticia](docs/capturas/03-admin-nueva-noticia.png)

**Listado de noticias** (`list_display`, `list_filter`, `date_hierarchy`)

![Lista de noticias](docs/capturas/04-admin-lista-noticias.png)

**Búsqueda** (`search_fields`: «vóley»)

![Búsqueda](docs/capturas/05-admin-busqueda.png)

**Filtro por categoría** (`list_filter`: Cultura)

![Filtro](docs/capturas/06-admin-filtro-categoria.png)

**Categorías y autores**

![Categorías](docs/capturas/07-admin-categorias.png)

![Autores](docs/capturas/08-admin-autores.png)

## Prueba de escapado automático

En el cuerpo de la noticia «Feria del Libro de Lima rompe récord de visitantes» se escribió desde el
administrador:

```html
Prueba de seguridad: <script>alert('Hackeado')</script> y <b>texto en negrita</b>
```

**Resultado en el navegador:** las etiquetas aparecen como texto. No se ejecuta ningún `alert`
y la palabra «texto en negrita» no se muestra en negrita.

![Escapado en la página](docs/capturas/14-escapado-detalle.png)

**HTML que envía el servidor:**

![Código fuente](docs/capturas/15-escapado-codigo-fuente.png)

**¿Por qué?** Django activa el *autoescape* en todas las plantillas. Al imprimir
`{{ article.body }}`, convierte los caracteres especiales en entidades HTML:

| Carácter | Se convierte en |
|----------|-----------------|
| `<`      | `&lt;`          |
| `>`      | `&gt;`          |
| `'`      | `&#x27;`        |
| `"`      | `&quot;`        |
| `&`      | `&amp;`         |

Así, el navegador muestra el texto en vez de interpretarlo como código. Esto protege al sitio de
ataques **XSS (Cross-Site Scripting)**: aunque alguien con acceso al administrador, o un formulario
público, guarde un `<script>` malicioso, este nunca se ejecuta en el navegador de los lectores.

El escapado solo se desactiva de forma explícita, con el filtro `|safe` o el bloque
`{% autoescape off %}`, y solo debe hacerse con contenido 100 % confiable. El filtro `|linebreaks`
usado en el detalle respeta el escapado: primero escapa el texto y luego añade las etiquetas `<p>`.

## Casos de prueba

Se ejecutan con:

```bash
python manage.py test news
```

| # | Caso de prueba | Resultado esperado | Estado |
|---|----------------|--------------------|--------|
| 1 | Abrir la portada | 200, usa `base.html` y `_article_card.html`, lista las noticias | ✅ |
| 2 | Portada sin noticias | Muestra «No hay noticias publicadas todavía.» (`{% empty %}`) | ✅ |
| 3 | Resumen de más de 25 palabras | Se recorta con `truncatewords:25` | ✅ |
| 4 | Abrir el detalle de una noticia | Muestra autor, categorías enlazadas e imagen | ✅ |
| 5 | Abrir una noticia que no existe | Responde 404 | ✅ |
| 6 | Listado por categoría | Solo muestra noticias de esa categoría y reutiliza la tarjeta | ✅ |
| 7 | Categoría sin noticias | Muestra «No hay noticias en esta categoría.» | ✅ |
| 8 | HTML dentro del cuerpo | Se muestra escapado (`&lt;script&gt;`), no se ejecuta | ✅ |
| 9 | Hoja de estilos | La página enlaza `/static/css/styles.css` mediante `{% static %}` | ✅ |
| 10 | Fragmentos reutilizados | Detalle y categoría usan `_category_tags.html` y `_back_link.html` | ✅ |
| 11 | Edición desde el administrador | Se edita una noticia en `/admin/` (título, cuerpo y categorías) y el cambio aparece en el detalle y en la categoría nueva sin tocar código | ✅ |

```
Ran 11 tests in 0.729s

OK
```

Además, se verificó manualmente con el servidor de desarrollo:

| URL | Código |
|-----|--------|
| `/` | 200 |
| `/noticia/festival-cine-lima-programacion/` | 200 |
| `/categoria/deportes/` | 200 |
| `/static/css/styles.css` | 200 |
| `/media/articles/festival-cine-lima-programacion.jpg` | 200 |
| `/noticia/no-existe/` | 404 |

## Observaciones

- **Plantillas sin marcado repetido.** Todo lo común está en `base.html`. Las piezas que aparecen en
  más de una página son fragmentos (`_article_card.html`, `_category_tags.html`, `_back_link.html`)
  que se incluyen con `{% include %}`. Al principio las etiquetas de categoría y el enlace
  «Volver a la portada» estaban copiados en dos plantillas; se pasaron a fragmentos para no repetirlos.
- **Contenido 100 % administrable.** Noticias, categorías, autores, imágenes, biografías y
  descripciones salen de la base de datos. El menú y la barra lateral de categorías también son
  dinámicos gracias al procesador de contexto `news.context_processors.categories`. Al crear una
  categoría en el panel, aparece sola en el menú. En las plantillas solo queda texto fijo de
  interfaz (nombre del portal, títulos de sección y mensajes de estado vacío).
- **Sin lógica de negocio en las plantillas.** Las consultas (filtrar por categoría, noticias
  relacionadas, conteo con `annotate`) se hacen en las vistas y en el procesador de contexto. Las
  plantillas solo recorren, condicionan y dan formato.
- **Formato con filtros, no a mano.** La fecha se muestra en español con `|date`
  (`LANGUAGE_CODE = 'es'`, `TIME_ZONE = 'America/Lima'`), el resumen se recorta con `|truncatewords`
  y el cuerpo se separa en párrafos con `|linebreaks`.
- **Enlaces por nombre.** No hay ninguna URL escrita a mano: se usa `{% url %}` en las plantillas y
  `reverse()` en `get_absolute_url()`.
- **Slugs en las URL.** Las direcciones son legibles (`/noticia/<slug>/`, `/categoria/<slug>/`). En
  el administrador el slug se completa solo a partir del título (`prepopulated_fields`).
- **Archivos de medios.** Se sirven con `static()` solo cuando `DEBUG = True`. En producción los
  debe servir el servidor web (Nginx, almacenamiento en la nube, etc.).
- **Archivos no versionados.** `db.sqlite3`, `media/` y `.venv/` están en `.gitignore`. Para
  reproducir los datos se incluye el comando `seed_news`, que también genera las imágenes con Pillow.
- **Traducción del admin.** Algunos textos del panel («Select an option», «Run», «Filter by…»)
  aparecen en inglés porque la traducción al español de Django 6.1 aún está incompleta. No es un
  error del proyecto.
- **Prueba de escapado.** Se hizo con una noticia real registrada desde el admin. Las capturas
  muestran el resultado en la página y el HTML que envía el servidor.

## Conclusiones

1. La **herencia de plantillas** (`extends` + `block`) permite definir la estructura del sitio una
   sola vez. Cada página solo describe lo que cambia, y un cambio en el menú o el pie se refleja en
   todas.
2. Los **fragmentos con `include`** evitan duplicar marcado: la misma tarjeta sirve para la portada
   y para cada categoría, y con `with` se les pasa solo el dato que necesitan.
3. Las **etiquetas de control** (`for`, `empty`, `if`) y los **filtros** (`date`, `truncatewords`,
   `linebreaks`, `default`) bastan para presentar los datos del modelo. Toda la lógica de consulta
   queda en las vistas.
4. El **panel de administración** de Django, personalizado con `list_display`, `list_filter` y
   `search_fields`, es un gestor de contenidos completo. Lo que se publica en el panel se ve en el
   sitio sin tocar código, como comprueba la prueba automática n.º 11.
5. Separar **estáticos** (CSS del proyecto) y **medios** (imágenes subidas por usuarios) ordena el
   proyecto y prepara su despliegue, donde cada tipo de archivo se sirve de forma distinta.
6. Las **URL con nombre** hacen el sitio más fácil de mantener: si cambia una ruta, se modifica solo
   `urls.py` y todos los enlaces siguen funcionando.
7. El **escapado automático** está activo por defecto y protege contra XSS: cualquier HTML ingresado
   como contenido se muestra como texto. Solo se desactiva de forma explícita con `|safe`, y únicamente
   con contenido confiable.
