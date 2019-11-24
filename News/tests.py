from django.test import TestCase, RequestFactory
from .management.commands.scraper import news_scraper, get_news_links, articles_scraper, \
    columns_scraper, run_news_scraper
from .models import *
from queue import Queue
from datetime import datetime
import os
import random
from .views import IndexView


class UkrpravdaScraperTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()   
    
    def test_news_scraper(self):
        count = News.objects.all().count()
        self.assertEqual(count, 0)
        news_links = []
        with open(os.path.join('news/management/commands/fresh_news_links.txt')) as file:
            for line in file:
                if ".ua/news" in line:
                    url = line.strip("\n")
                    news_links.append(url)
                    del url
                else:
                    continue
        choice_url = random.choice(news_links)
        del news_links
        qu = Queue()
        qu.put(choice_url)
        news_scraper(qu)
        count = News.objects.all().count()
        self.assertEqual(count, 1)

    def test_column_scraper(self):
        count = Columns.objects.all().count()
        self.assertEqual(count, 0)
        columns_links = []
        with open(os.path.join('news/management/commands/fresh_news_links.txt')) as file:
            for line in file:
                if ".ua/columns" in line:
                    url = line.strip("\n")
                    columns_links.append(url)
                    del url
                else:
                    continue
        choice_url = random.choice(columns_links)
        del columns_links
        qu = Queue()
        qu.put(choice_url)
        columns_scraper(qu)
        count = Columns.objects.all().count()
        self.assertEqual(count, 1)

    def test_article_scraper(self):
        count = Article.objects.all().count()
        self.assertEqual(count, 0)
        articles_links = []
        with open(os.path.join('news/management/commands/fresh_news_links.txt')) as file:
            for line in file:
                if ".ua/articles" in line:
                    url = line.strip("\n")
                    articles_links.append(url)
                    del url
                else:
                    continue
        choice_url = random.choice(articles_links)
        del articles_links
        qu = Queue()
        qu.put(choice_url)
        articles_scraper(qu)
        count = Article.objects.all().count()
        self.assertEqual(count, 1)

    def test_getting_fresh_links(self):
        get_news_links(1, None)
        date = str(datetime.now().date()).replace("-", '/')
        with open(os.path.join('news/management/commands/fresh_news_links.txt')) as file:
            for line in file:
                if date in line:
                    fresh_links = True
                    print('Links Are Fresh!')
                    break
        self.assertTrue(fresh_links)


class ModelsTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_news_model(self):
        title = hasattr(News, 'title')
        slug = hasattr(News, 'slug')
        news_text = hasattr(News, 'news_text')
        image = hasattr(News, 'image')
        image_url = hasattr(News, 'image_url')
        news_date = hasattr(News, 'news_date')
        news_source = hasattr(News, 'news_source')
        parsing_date = hasattr(News, 'parsing_date')
        source_reviews = hasattr(News, 'source_reviews')
        self.assertTrue(title)
        self.assertTrue(slug)
        self.assertTrue(news_text)
        self.assertTrue(image)
        self.assertTrue(image_url)
        self.assertTrue(news_date)
        self.assertTrue(news_source)
        self.assertTrue(parsing_date)
        self.assertTrue(source_reviews)

    def test_author_model(self):
        name = hasattr(Author, 'name')
        slug = hasattr(Author, 'slug')
        self.assertTrue(name)
        self.assertTrue(slug)

    def test_columns_model(self):
        title = hasattr(Columns, 'title')
        slug = hasattr(Columns, 'slug')
        column_text = hasattr(Columns, 'column_text')
        image = hasattr(Columns, 'image')
        image_url = hasattr(Columns, 'image_url')
        column_date = hasattr(Columns, 'column_date')
        column_source = hasattr(Columns, 'column_source')
        parsing_date = hasattr(Columns, 'parsing_date')
        source_reviews = hasattr(Columns, 'source_reviews')
        moderated = hasattr(Columns, 'moderated')
        self.assertTrue(title)
        self.assertTrue(slug)
        self.assertTrue(column_text)
        self.assertTrue(image)
        self.assertTrue(image_url)
        self.assertTrue(column_date)
        self.assertTrue(column_source)
        self.assertTrue(parsing_date)
        self.assertTrue(source_reviews)
        self.assertTrue(moderated)

    def test_article_model(self):
        title = hasattr(Article, 'title')
        slug = hasattr(Article, 'slug')
        article_text = hasattr(Article, 'article_text')
        image = hasattr(Article, 'image')
        image_url = hasattr(Article, 'image_url')
        article_date = hasattr(Article, 'article_date')
        article_source = hasattr(Article, 'article_source')
        parsing_date = hasattr(Article, 'parsing_date')
        source_reviews = hasattr(Article, 'source_reviews')
        moderated = hasattr(Article, 'moderated')
        self.assertTrue(title)
        self.assertTrue(slug)
        self.assertTrue(article_text)
        self.assertTrue(image)
        self.assertTrue(image_url)
        self.assertTrue(article_date)
        self.assertTrue(article_source)
        self.assertTrue(parsing_date)
        self.assertTrue(source_reviews)
        self.assertTrue(moderated)
