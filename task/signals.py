from django.db.models.signals import post_save
from News.models import News, NewsTag, Columns, Author, Article
from django.conf import settings
from task.models import Task
from News.management.commands.scraper import run_news_scraper, get_news_links, \
    run_articles_scraper, run_columns_scraper
from threading import Thread
import os


def handler_run_parser(sender, instance, **kwargs):
    if kwargs.get('created'):
        if instance.task == 'run_parser':
            Thread(target=run_columns_scraper, args=(1, instance)).start()
            Thread(target=run_articles_scraper, args=(1, instance)).start()
            Thread(target=run_news_scraper, args=(1, instance)).start()
        elif instance.task == 'get_articles':
            Thread(target=run_articles_scraper, args=(1, instance)).start()
        elif instance.task == 'get_fresh_links':
            Thread(target=get_news_links, args=(1, instance)).start()
        elif instance.task == 'get_columns':
            Thread(target=run_columns_scraper, args=(1, instance)).start()
        elif instance.task == 'get_news':
            Thread(target=run_news_scraper, args=(1, instance)).start()
        elif instance.task == 'count_images':
            count_images = len(os.listdir(os.path.join(settings.BASE_DIR, 'media/images/')))
            instance.status = f'Images = {count_images}'
            instance.save()
        elif instance.task == 'count__total_news':
            news = News.objects.count()
            instance.status = f'There are {news} news in database'
            instance.save()
        elif instance.task == 'count__articles':
            count_items = Article.objects.count()
            instance.status = f'There are {count_items} Articles'
            instance.save()
        elif instance.task == 'count__columns':
            count_items = Columns.objects.count()
            instance.status = f'There are {count_items} Columns'
            instance.save()
        elif instance.task == 'count__categories':
            count_categories = NewsTag.objects.count()
            instance.status = f'There are {count_categories} categories in your database'
            instance.save()
        elif instance.task == 'count__author':
            authors = Author.objects.count()
            instance.status = f'There are {authors} Authors in your database'
            instance.save()


post_save.connect(handler_run_parser, sender=Task)
