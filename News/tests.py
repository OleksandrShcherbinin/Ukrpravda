from django.test import TestCase, RequestFactory
from .management.commands.scraper import news_scraper, get_news_links, articles_scraper, columns_scraper
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
                    break
        self.assertTrue(fresh_links)



