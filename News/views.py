from django.shortcuts import render
from .models import *
from django.db.models import Count
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic import FormView
from django.views.generic.list import ListView, MultipleObjectMixin
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.http import Http404
from django.contrib import messages
from .forms import ReviewForm
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from datetime import datetime
import logging

#logger = logging.getLogger('django')


class IndexView(TemplateView):
    template_name = 'home.html'
    paginate_by = 10

    #def get(self, request, *args, **kwargs):
    #    self.object = self.get_object(queryset=NewsTag.objects.all())
    #    return super().get(request, *args, **kwargs)

    #def get_queryset(self):
    #    #news_tag = self.request.GET.get('news_tag')
    #    return News.objects.filter(news_tag=self.object.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        value = datetime.now().date()
        big_news = Article.objects.all().order_by('-article_date')[0]
        fresh_news = Columns.objects.all().order_by('-column_date')[1:3]
        news = News.objects.all().order_by('-news_date')[3:14]
        context.update({'big_news': big_news})
        context.update({'fresh_news': fresh_news})
        context.update({'news': news})
        context.update({'value': value})
        context['popular_news'] = News.objects.all().order_by('-source_reviews')[:5]
        context['latest'] = News.objects.all().order_by('-news_date')[:3]
        context['most_comments'] = News.objects.all().order_by('-reviews')[:3]
        #news_for_tags = News.objects.get(news_tag=self.object)
        #context.update({'news_for_tags': news_for_tags})
        #news_tags = NewsTag.objects.filter(news_for_tags=self.object.id)
        #context['news_tags'] = news_tags

        return context


class ArticlesView(TemplateView, Paginator):
    template_name = 'article.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        value = datetime.now().date()
        big_news = Article.objects.all().order_by('-article_date')[0]
        fresh_news = Article.objects.all().order_by('-article_date')[1:3]
        news = Article.objects.all().order_by('-article_date')[3:14]
        context.update({'big_news': big_news})
        context.update({'fresh_news': fresh_news})
        context.update({'news': news})
        context.update({'value': value})
        context['popular_news'] = Article.objects.all().order_by('-source_reviews')[:5]
        context['latest'] = Article.objects.all().order_by('-article_date')[:3]
        context['most_comments'] = Article.objects.all().order_by('-articlereviews')[:3]

        return context


class ColumnsView(TemplateView, Paginator):
    template_name = 'columns.html'
    paginate_by = 10

    model = Columns
    #slug_field = 'columns'

    #def get(self, request, *args, **kwargs):
    #    self.object = self.get_object(queryset=Author.objects.all())
    #    return super().get(request, *args, **kwargs)

    #def get_queryset(self):
    #    #self.author_tag = get_object_or_404(Author, columns=self.author_tag)
    #    return Columns.objects.filter(author_tag=self.object)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        value = datetime.now().date()
        #big_news = Columns.objects.all().order_by('-column_date')[0]
        #fresh_news = Columns.objects.all().order_by('-column_date')[1:3]
        news = Columns.objects.all().order_by('-column_date')[0:14]
        #author = Author.objects.filter(columns=self.author_tag)
        #context['author'] = author
        #context.update({'author': author})
        #context.update({'big_news': big_news})
        #context.update({'fresh_news': fresh_news})
        context.update({'news': news})
        context.update({'value': value})
        context['popular_news'] = Columns.objects.all().order_by('-source_reviews')[:5]
        context['latest'] = Columns.objects.all().order_by('-column_date')[:3]
        context['most_comments'] = Columns.objects.all().order_by('-columnreviews')[:3]

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


class SearchView(ListView):
    template_name = 'home.html'
    model = News
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return News.objects.filter(title__contains=query)
        else:
            return Http404()

