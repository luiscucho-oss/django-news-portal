from django.contrib import admin

from .models import Article, Author, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'total_articles')
    list_filter = ('articles__published_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='N.º de noticias')
    def total_articles(self, obj):
        return obj.articles.count()


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'total_articles')
    list_filter = ('articles__categories',)
    search_fields = ('name', 'email', 'bio')

    @admin.display(description='N.º de noticias')
    def total_articles(self, obj):
        return obj.articles.count()


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category_names', 'published_at')
    list_filter = ('categories', 'author', 'published_at')
    search_fields = ('title', 'summary', 'body', 'author__name')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('categories',)
    date_hierarchy = 'published_at'

    @admin.display(description='Categorías')
    def category_names(self, obj):
        return ', '.join(c.name for c in obj.categories.all())

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author').prefetch_related('categories')
