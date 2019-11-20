from django.shortcuts import render
from .models import *
from django.db.models import Count
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic import FormView
from django.views.generic.list import ListView
from django.http import Http404
from django.contrib import messages
from django.db.models import Q
from .forms import ReviewForm
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from datetime import datetime
import logging

#logger = logging.getLogger('django')


class IndexView(ListView):
    template_name = 'home.html'
    paginate_by = 14

    def get_queryset(self):
        return News.objects.all().order_by('-news_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        value = datetime.now().date()
        big_news = Article.objects.filter(moderated=True).order_by('-article_date')[0]
        fresh_news = Columns.objects.filter(moderated=True).order_by('-column_date')[1:3]
        context.update({'big_news': big_news})
        context.update({'fresh_news': fresh_news})
        context.update({'value': value})
        context['popular_news'] = News.objects.all().order_by('-source_reviews')[:5]
        context['latest'] = News.objects.all().order_by('-news_date')[:3]
        context['most_comments'] = News.objects.all().order_by('-reviews')[:3]

        return context


class ArticlesView(ListView):
    template_name = 'article.html'
    paginate_by = 10

    def get_queryset(self):
        return Article.objects.filter(moderated=True).order_by('-article_date')[3:]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        value = datetime.now().date()
        big_news = Article.objects.filter(moderated=True).order_by('-article_date')[0]
        fresh_news = Article.objects.filter(moderated=True).order_by('-article_date')[1:3]
        context.update({'big_news': big_news})
        context.update({'fresh_news': fresh_news})
        context.update({'value': value})
        context['popular_news'] = Article.objects.filter(moderated=True).order_by('-source_reviews')[:5]
        context['latest'] = Article.objects.filter(moderated=True).order_by('-article_date')[:3]
        context['most_comments'] = Article.objects.filter(moderated=True).order_by('-articlereviews')[:3]

        return context


class ColumnsView(ListView):
    template_name = 'columns.html'
    paginate_by = 8
    model = Columns

    def get_queryset(self):
        columns = Columns.objects.filter(moderated=True).order_by('-column_date').prefetch_related('author_tag')
        return columns

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        value = datetime.now().date()
        context['value'] = value
        context['popular_news'] = Columns.objects.filter(moderated=True).order_by('-source_reviews')[:5]
        context['latest'] = Columns.objects.filter(moderated=True).order_by('-column_date')[:3]
        context['most_comments'] = Columns.objects.filter(moderated=True).order_by('-columnreviews')[:3]

        return context


@method_decorator(csrf_protect, name='dispatch')
class ArticleView(DetailView, FormView, SingleObjectMixin):
    template_name = 'single.html'
    model = News
    context_object_name = 'title'
    slug_url_kwarg = 'slug'
    form_class = ReviewForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        value = datetime.now().date()
        news = News.objects.get(title=self.object)
        context.update({'news': news})
        context.update({'value': value})

        context['reviews'] = Reviews.objects.filter(news=self.object,
                                                    moderated=True).order_by('-published')[:5]
        context['popular_news'] = News.objects.all().order_by('-source_reviews')[:5]
        context['latest'] = News.objects.all().order_by('-news_date')[:3]
        context['most_comments'] = News.objects.annotate(num_reviews=Count('reviews')).order_by('-num_reviews')[:3]
        post_tags = NewsTag.objects.filter(news=self.object.id)
        context['post_tags'] = post_tags
        context['tags'] = NewsTag.objects.all()[:10]
        return context

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.form = ReviewForm(self.request.POST)
        context = self.get_context_data(**kwargs)
        if self.form.is_valid():
            Reviews.objects.create(**self.form.cleaned_data, news=self.object)
            messages.add_message(self.request, messages.INFO, 'Thank you! Your review is on moderation!')
        else:
            #logger.warning(self.form)
            context['form'] = self.form
            messages.add_message(self.request, messages.INFO, 'Incorrect input! Try one more time!')
        return self.render_to_response(context)


@method_decorator(csrf_protect, name='dispatch')
class DetailArticleView(DetailView, FormView, SingleObjectMixin):
    template_name = 'single_article.html'
    model = Article
    context_object_name = 'title'
    slug_url_kwarg = 'slug'
    form_class = ReviewForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        value = datetime.now().date()
        news = Article.objects.get(title=self.object)
        context.update({'news': news})
        context.update({'value': value})
        author = Author.objects.get(article=self.object)
        context['author'] = author

        context['articlereviews'] = ArticleReviews.objects.filter(article=self.object,
                                                                  moderated=True).order_by('-published')[:5]
        context['popular_news'] = Article.objects.all().order_by('-source_reviews')[:5]
        context['latest'] = Article.objects.all().order_by('-article_date')[:3]
        context['most_comments'] = Article.objects.annotate(num_reviews=Count('articlereviews')).order_by('-num_reviews')[:3]
        post_tags = NewsTag.objects.filter(article=self.object.id)
        context['post_tags'] = post_tags
        context['tags'] = NewsTag.objects.all()[:10]
        return context

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.form = ReviewForm(self.request.POST)
        context = self.get_context_data(**kwargs)
        if self.form.is_valid():
            ArticleReviews.objects.create(**self.form.cleaned_data, article=self.object)
            messages.add_message(self.request, messages.INFO, 'Thank you! Your review is on moderation!')
        else:
            #logger.warning(self.form)
            context['form'] = self.form
            messages.add_message(self.request, messages.INFO, 'Incorrect input! Try one more time!')
        return self.render_to_response(context)


@method_decorator(csrf_protect, name='dispatch')
class DetailColumnView(DetailView, FormView, SingleObjectMixin):
    template_name = 'single_column.html'
    model = Columns
    context_object_name = 'title'
    slug_url_kwarg = 'slug'
    form_class = ReviewForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        value = datetime.now().date()
        news = Columns.objects.get(title=self.object)
        context.update({'news': news})
        context.update({'value': value})
        author = Author.objects.get(columns=self.object)
        context['author'] = author

        context['columnreviews'] = ColumnReviews.objects.filter(column=self.object,
                                                                moderated=True).order_by('-published')[:5]
        context['popular_news'] = Columns.objects.all().order_by('-source_reviews')[:5]
        context['latest'] = Columns.objects.all().order_by('-column_date')[:3]
        context['most_comments'] = Columns.objects.annotate(num_reviews=Count('columnreviews')).order_by('-num_reviews')[:3]
        post_tags = NewsTag.objects.filter(columns=self.object.id)
        context['post_tags'] = post_tags
        context['tags'] = NewsTag.objects.all()[:10]
        return context

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.form = ReviewForm(self.request.POST)
        context = self.get_context_data(**kwargs)
        if self.form.is_valid():
            ColumnReviews.objects.create(**self.form.cleaned_data, column=self.object)
            messages.add_message(self.request, messages.INFO, 'Thank you! Your review is on moderation!')
        else:
            #logger.warning(self.form)
            context['form'] = self.form
            messages.add_message(self.request, messages.INFO, 'Incorrect input! Try one more time!')
        return self.render_to_response(context)


class AuthorView(ListView, SingleObjectMixin):
    template_name = 'page-author.html'
    model = Author
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Author.objects.all())
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        article = Article.objects.filter(author_tag=self.object, moderated=True).order_by('-article_date')
        if article:
            return article
        else:
            return Columns.objects.filter(author_tag=self.object, moderated=True).order_by('-column_date')


class AuthorsView(ListView):
    template_name = 'authors.html'
    model = Author
    paginate_by = 10

    def get_queryset(self):
        return Author.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        value = datetime.now().date()
        context.update({'value': value})
        context['popular_news'] = News.objects.all().order_by('-source_reviews')[:5]
        context['latest'] = News.objects.all().order_by('-news_date')[:3]
        context['most_comments'] = News.objects.all().order_by('-reviews')[:3]

        return context


class SearchView(ListView):
    template_name = 'page-search.html'
    model = News
    paginate_by = 14

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return News.objects.filter(title__icontains=query).order_by('-news_date')
        else:
            return Http404()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        value = datetime.now().date()
        context['value'] = value
        return context


def robots_view(request):
    return render(request, 'robots.txt', {}, content_type="text/plain")
