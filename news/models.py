from django.db import models
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    name = models.CharField('nombre', max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField('descripción', blank=True)

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('news:category', args=[self.slug])


class Author(models.Model):
    name = models.CharField('nombre', max_length=120)
    email = models.EmailField('correo', unique=True)
    bio = models.TextField('biografía', blank=True)

    class Meta:
        verbose_name = 'autor'
        verbose_name_plural = 'autores'
        ordering = ['name']

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField('título', max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    summary = models.TextField('resumen')
    body = models.TextField('cuerpo')
    image = models.ImageField('imagen destacada', upload_to='articles/')
    published_at = models.DateTimeField('fecha de publicación', default=timezone.now)
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name='articles',
        verbose_name='autor',
    )
    categories = models.ManyToManyField(
        Category,
        related_name='articles',
        verbose_name='categorías',
    )

    class Meta:
        verbose_name = 'noticia'
        verbose_name_plural = 'noticias'
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news:article_detail', args=[self.slug])
