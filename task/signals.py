from django.db.models.signals import post_save
from News.models import News, NewsTag, Columns, Author, Article
from task.models import Task
from News.management.commands.scraper import run_news_scraper2
from threading import Thread
import os
from django.conf import settings


def handler_run_parser(sender, instance, **kwargs):
    if kwargs.get('created'):
        if instance.task == 'run_parser':
            try:
                start, end = instance.arg.split(',')
                start, end = int(start), int(end)
            except Exception as e:
                print(e, type(e))
                start, end = 0, 1
            Thread(target=run_news_scraper2, args=(start, end, instance)).start()
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
