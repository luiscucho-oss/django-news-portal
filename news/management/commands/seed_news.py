"""Carga datos de prueba: 3 categorías, 3 autores y 5 noticias con imagen generada."""
import io
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from news.models import Article, Author, Category

CATEGORIES = [
    ('Tecnología', 'tecnologia', 'Innovación, software, ciencia y el mundo digital.', (31, 78, 140)),
    ('Deportes', 'deportes', 'Fútbol, vóley, atletismo y todo el deporte nacional.', (24, 120, 72)),
    ('Cultura', 'cultura', 'Arte, música, cine, literatura y tradiciones.', (140, 52, 110)),
]

AUTHORS = [
    ('María Quispe', 'maria.quispe@diariotecsup.pe', 'Periodista especializada en tecnología y ciencia.'),
    ('Jorge Ramírez', 'jorge.ramirez@diariotecsup.pe', 'Cronista deportivo con diez años de experiencia.'),
    ('Ana Torres', 'ana.torres@diariotecsup.pe', 'Editora de la sección de cultura y espectáculos.'),
]

ARTICLES = [
    {
        'title': 'Estudiantes de Tecsup desarrollan un robot que clasifica residuos',
        'slug': 'estudiantes-tecsup-robot-clasifica-residuos',
        'summary': 'Un equipo de estudiantes presentó un prototipo que usa visión artificial para '
                   'separar plástico, vidrio y papel en tiempo real, con una precisión superior al 90 %.',
        'body': 'El proyecto nació como trabajo de curso y terminó ganando la feria de innovación del campus.\n\n'
                'El robot utiliza una cámara y un modelo de clasificación entrenado con más de diez mil '
                'imágenes de residuos reciclables.\n\n'
                'Los estudiantes planean instalar el primer prototipo en la cafetería durante el próximo ciclo.',
        'author': 0, 'categories': [0], 'days_ago': 1,
    },
    {
        'title': 'La inteligencia artificial llega a las aulas peruanas',
        'slug': 'inteligencia-artificial-aulas-peruanas',
        'summary': 'Docentes de distintas regiones comienzan a usar asistentes de IA para preparar clases, '
                   'corregir ejercicios y acompañar a sus estudiantes fuera del horario escolar.',
        'body': 'Un programa piloto capacitó a más de 500 docentes en el uso responsable de herramientas de IA.\n\n'
                'Los especialistas recomiendan usar estas herramientas como apoyo y no como reemplazo del '
                'trabajo docente.\n\n'
                'El ministerio evaluará los resultados a fin de año para decidir si amplía la iniciativa.',
        'author': 0, 'categories': [0, 2], 'days_ago': 3,
    },
    {
        'title': 'Perú clasifica a la final del Sudamericano de Vóley',
        'slug': 'peru-clasifica-final-sudamericano-voley',
        'summary': 'La selección femenina venció 3-1 a Colombia en un partido intenso y disputará el título '
                   'este domingo ante Brasil en el Coliseo Eduardo Dibós.',
        'body': 'Las dirigidas por el comando técnico nacional remontaron un primer set adverso.\n\n'
                'La capitana fue la máxima anotadora con 22 puntos y destacó el apoyo del público.\n\n'
                'La final se jugará a las 4:00 p. m. y será transmitida en señal abierta.',
        'author': 1, 'categories': [1], 'days_ago': 2,
    },
    {
        'title': 'Maratón de Lima 42K reunirá a más de 15 000 corredores',
        'slug': 'maraton-lima-42k-15000-corredores',
        'summary': 'La competencia recorrerá seis distritos de la capital y contará con atletas de élite '
                   'de Kenia, Etiopía y Sudamérica que buscarán batir el récord del circuito.',
        'body': 'La organización habilitó 12 puntos de hidratación y tres zonas de atención médica.\n\n'
                'Por primera vez habrá una categoría adaptada para atletas en silla de ruedas.\n\n'
                'Se recomienda a los vecinos revisar los desvíos vehiculares publicados por la municipalidad.',
        'author': 1, 'categories': [1], 'days_ago': 5,
    },
    {
        'title': 'El Festival de Cine de Lima anuncia su programación',
        'slug': 'festival-cine-lima-programacion',
        'summary': 'Más de 120 películas de 30 países competirán este año; la selección peruana incluye '
                   'cinco largometrajes de ficción y tres documentales de directores jóvenes.',
        'body': 'Las funciones se realizarán en cinco sedes y habrá proyecciones gratuitas en parques.\n\n'
                'El festival rendirá homenaje a la trayectoria de reconocidos cineastas nacionales.\n\n'
                'La venta de entradas comenzará la próxima semana a través de la web oficial.',
        'author': 2, 'categories': [2], 'days_ago': 4,
    },
]


def _font(size, bold=False):
    names = ['georgiab.ttf', 'arialbd.ttf', 'DejaVuSans-Bold.ttf'] if bold else ['arial.ttf', 'DejaVuSans.ttf']
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_image(title, label, color, size=(1200, 675)):
    """Genera una imagen destacada con degradado, etiqueta de categoría y título."""
    width, height = size
    img = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        k = y / height
        draw.line([(0, y), (width, y)], fill=tuple(int(c * (1 - 0.55 * k)) for c in color))
    for i in range(6):
        r = 120 + i * 90
        draw.ellipse([width - r, -r // 2, width + r, r * 1.5], outline=(255, 255, 255, 40), width=2)

    label_font, title_font = _font(30, bold=True), _font(62, bold=True)
    draw.rounded_rectangle([60, 60, 60 + draw.textlength(label.upper(), font=label_font) + 40, 112],
                           radius=26, fill=(255, 255, 255))
    draw.text((80, 68), label.upper(), font=label_font, fill=color)

    words, lines, line = title.split(), [], ''
    for word in words:
        test = f'{line} {word}'.strip()
        if draw.textlength(test, font=title_font) > width - 140:
            lines.append(line)
            line = word
        else:
            line = test
    lines.append(line)
    y = height - 80 - len(lines) * 76
    for text in lines:
        draw.text((60, y), text, font=title_font, fill=(255, 255, 255))
        y += 76

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=88)
    return buffer.getvalue()


class Command(BaseCommand):
    help = 'Crea categorías, autores y noticias de ejemplo con imágenes generadas.'

    def handle(self, *args, **options):
        categories = []
        for name, slug, description, _ in CATEGORIES:
            category, _ = Category.objects.update_or_create(
                slug=slug, defaults={'name': name, 'description': description},
            )
            categories.append(category)

        authors = []
        for name, email, bio in AUTHORS:
            author, _ = Author.objects.update_or_create(email=email, defaults={'name': name, 'bio': bio})
            authors.append(author)

        now = timezone.now()
        for data in ARTICLES:
            if Article.objects.filter(slug=data['slug']).exists():
                self.stdout.write(f'  ya existe: {data["title"]}')
                continue
            first = CATEGORIES[data['categories'][0]]
            article = Article(
                title=data['title'],
                slug=data['slug'],
                summary=data['summary'],
                body=data['body'],
                author=authors[data['author']],
                published_at=now - timedelta(days=data['days_ago']),
            )
            article.image.save(f'{data["slug"]}.jpg', ContentFile(make_image(data['title'], first[0], first[3])),
                               save=False)
            article.save()
            article.categories.set(categories[i] for i in data['categories'])
            self.stdout.write(self.style.SUCCESS(f'  creada: {article.title}'))

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {Category.objects.count()} categorías, {Author.objects.count()} autores, '
            f'{Article.objects.count()} noticias.'
        ))
