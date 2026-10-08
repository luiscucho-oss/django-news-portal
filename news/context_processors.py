from django.db.models import Count

from .models import Category


def categories(request):
    """Categorías disponibles en todas las plantillas (menú y barra lateral)."""
    return {
        'nav_categories': Category.objects.annotate(num_articles=Count('articles')),
    }
