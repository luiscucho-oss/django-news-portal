from django.shortcuts import get_object_or_404, render

from .models import Article, Category


def home(request):
    articles = Article.objects.select_related('author').prefetch_related('categories')
    return render(request, 'news/home.html', {'articles': articles})


def article_detail(request, slug):
    article = get_object_or_404(
        Article.objects.select_related('author').prefetch_related('categories'),
        slug=slug,
    )
    related = (
        Article.objects.filter(categories__in=article.categories.all())
        .exclude(pk=article.pk)
        .distinct()[:3]
    )
    return render(request, 'news/article_detail.html', {'article': article, 'related': related})


def category_list(request, slug):
    category = get_object_or_404(Category, slug=slug)
    articles = category.articles.select_related('author').prefetch_related('categories')
    return render(request, 'news/category_list.html', {'category': category, 'articles': articles})
