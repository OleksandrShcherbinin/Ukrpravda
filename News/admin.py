from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import *


class NewsAdmin(SummernoteModelAdmin):
    summernote_fields = ('news_text',)
    list_filter = ['parsing_date']
    list_display = ['title', 'news_date', 'parsing_date', 'source_reviews']
    list_editable = ['source_reviews']
    search_fields = ['news_text']


class ColumnsAdmin(SummernoteModelAdmin):
    summernote_fields = ('column_text',)
    list_filter = ['author_tag']
    list_display = ['title', 'column_date', 'source_reviews', 'moderated']
    list_editable = ['source_reviews', 'moderated']
    search_fields = ['column_text']


class ArticlesAdmin(SummernoteModelAdmin):
    summernote_fields = ('article_text',)
    list_filter = ['author_tag']
    list_display = ['title', 'article_date', 'source_reviews', 'moderated']
    list_editable = ['source_reviews', 'moderated']
    search_fields = ['article_text']


class ReviewAdmin(SummernoteModelAdmin):
    summernote_fields = ('comment',)
    list_filter = ['published', 'moderated']
    list_display = ['name', 'email', 'published', 'moderated']
    list_editable = ['moderated']
    search_fields = ['title', 'news_text']


class ArticleReviewAdmin(SummernoteModelAdmin):
    summernote_fields = ('comment',)
    list_filter = ['published', 'moderated']
    list_display = ['name', 'email', 'published', 'moderated']
    list_editable = ['moderated']
    search_fields = ['title', 'article_text']


class ColumnsReviewAdmin(SummernoteModelAdmin):
    summernote_fields = ('comment',)
    list_filter = ['published', 'moderated']
    list_display = ['name', 'email', 'published', 'moderated']
    list_editable = ['moderated']
    search_fields = ['title', 'column_text']


admin.site.register(NewsTag)
admin.site.register(Author)
admin.site.register(News, NewsAdmin)
admin.site.register(Columns, ColumnsAdmin)
admin.site.register(Article, ArticlesAdmin)
admin.site.register(Reviews, ReviewAdmin)
admin.site.register(ArticleReviews, ArticleReviewAdmin)
admin.site.register(ColumnReviews, ColumnsReviewAdmin)


