import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Article, Author, Category

MEDIA_ROOT = tempfile.mkdtemp()

# GIF de 1x1 píxel para no depender de archivos externos
TINY_GIF = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00'
    b'\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class NewsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.tech = Category.objects.create(name='Tecnología', slug='tecnologia')
        cls.sports = Category.objects.create(name='Deportes', slug='deportes')
        cls.author = Author.objects.create(name='María Quispe', email='maria@example.com')
        cls.article = cls.make_article('Robot reciclador', 'robot-reciclador', cls.tech)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def make_article(cls, title, slug, category, body='Cuerpo de la noticia.', summary='Resumen corto.'):
        article = Article.objects.create(
            title=title,
            slug=slug,
            summary=summary,
            body=body,
            author=cls.author,
            image=SimpleUploadedFile(f'{slug}.gif', TINY_GIF, content_type='image/gif'),
        )
        article.categories.add(category)
        return article

    def test_portada_lista_noticias_y_usa_plantilla_base(self):
        response = self.client.get(reverse('news:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'news/_article_card.html')
        self.assertContains(response, 'Robot reciclador')

    def test_portada_vacia_muestra_mensaje_empty(self):
        Article.objects.all().delete()
        response = self.client.get(reverse('news:home'))
        self.assertContains(response, 'No hay noticias publicadas todavía.')

    def test_resumen_se_recorta_a_25_palabras(self):
        long_summary = ' '.join(f'palabra{i}' for i in range(40))
        self.make_article('Noticia larga', 'noticia-larga', self.tech, summary=long_summary)
        response = self.client.get(reverse('news:home'))
        self.assertContains(response, 'palabra24 …')
        self.assertNotContains(response, 'palabra30')

    def test_detalle_muestra_autor_categorias_e_imagen(self):
        response = self.client.get(reverse('news:article_detail', args=[self.article.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'news/article_detail.html')
        self.assertContains(response, 'María Quispe')
        self.assertContains(response, reverse('news:category', args=['tecnologia']))
        self.assertContains(response, self.article.image.url)

    def test_fragmentos_reutilizados_en_detalle_y_categoria(self):
        detail = self.client.get(reverse('news:article_detail', args=[self.article.slug]))
        self.assertTemplateUsed(detail, 'news/_category_tags.html')
        self.assertTemplateUsed(detail, 'news/_back_link.html')
        category = self.client.get(reverse('news:category', args=['tecnologia']))
        self.assertTemplateUsed(category, 'news/_category_tags.html')
        self.assertTemplateUsed(category, 'news/_back_link.html')

    def test_cambio_en_el_admin_se_publica_en_el_sitio(self):
        User.objects.create_superuser('editor', 'editor@example.com', 'clave-segura-123')
        self.client.login(username='editor', password='clave-segura-123')
        response = self.client.post(reverse('admin:news_article_change', args=[self.article.pk]), {
            'title': 'Robot reciclador gana concurso nacional',
            'slug': self.article.slug,
            'summary': 'Resumen editado desde el panel.',
            'body': 'Cuerpo editado desde el panel.',
            'published_at_0': '2026-10-08',
            'published_at_1': '10:00:00',
            'author': self.author.pk,
            'categories': [self.tech.pk, self.sports.pk],
        })
        self.assertRedirects(response, reverse('admin:news_article_changelist'))

        page = self.client.get(reverse('news:article_detail', args=[self.article.slug]))
        self.assertContains(page, 'Robot reciclador gana concurso nacional')
        self.assertContains(page, 'Cuerpo editado desde el panel.')
        self.assertContains(page, reverse('news:category', args=['deportes']))
        self.assertContains(self.client.get(reverse('news:category', args=['deportes'])),
                            'Robot reciclador gana concurso nacional')

    def test_detalle_inexistente_devuelve_404(self):
        response = self.client.get(reverse('news:article_detail', args=['no-existe']))
        self.assertEqual(response.status_code, 404)

    def test_categoria_filtra_noticias_y_reutiliza_tarjeta(self):
        self.make_article('Final de vóley', 'final-voley', self.sports)
        response = self.client.get(reverse('news:category', args=['deportes']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'news/_article_card.html')
        self.assertContains(response, 'Final de vóley')
        self.assertNotContains(response, 'Robot reciclador')

    def test_categoria_sin_noticias_muestra_empty(self):
        Category.objects.create(name='Cultura', slug='cultura')
        response = self.client.get(reverse('news:category', args=['cultura']))
        self.assertContains(response, 'No hay noticias en esta categoría.')

    def test_html_en_el_cuerpo_se_escapa(self):
        body = "<script>alert('XSS')</script> y <b>negrita</b>"
        article = self.make_article('Prueba de escapado', 'prueba-escapado', self.tech, body=body)
        response = self.client.get(reverse('news:article_detail', args=[article.slug]))
        self.assertNotContains(response, "<script>alert('XSS')</script>")
        self.assertContains(response, '&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;')
        self.assertContains(response, '&lt;b&gt;negrita&lt;/b&gt;')

    def test_hoja_de_estilos_se_carga_con_static(self):
        response = self.client.get(reverse('news:home'))
        self.assertContains(response, '/static/css/styles.css')
