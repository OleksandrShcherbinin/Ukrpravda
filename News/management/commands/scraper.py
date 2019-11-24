from django.core.management.base import BaseCommand
from concurrent.futures import ThreadPoolExecutor
from requests_html import HTMLSession
from django.contrib import messages
from googletrans import Translator
from datetime import datetime
from threading import Lock
from time import sleep
from News.models import *
from queue import Queue
import random
import logging
import sys
import os

LOCKER = Lock()
logger = logging.getLogger('django')

with open(os.path.join('News/management/commands/user_agents.txt'), 'r') as f:
    user_agents = f.read().split('\n')

with open(os.path.join('News/management/commands/fresh_socks.txt'), 'r') as f:
    proxies_list = f.read().split('\n')

COUNTER = 0
NEWS_COUNTER = 0
ARTICLES_COUNTER = 0
COLUMNS_COUNTER = 0


def news_scraper(qu):
    while True:
        url = qu.get()
        prox = random.choice(proxies_list)
        proxies = {'http': prox, 'https': prox}
        user_agent = str(random.choice(user_agents)).strip("\t\t\t\t")
        headers = {'User-Agent': user_agent}
        try:
            with HTMLSession() as session:
                response = session.get(url, proxies=proxies, headers=headers, timeout=10)
                h1_start, h1_end = response.text.index('<h1 class="post_news__title">'), response.text.index('</h1>')
                title = response.text[h1_start: h1_end]
                title = title.split(">")[-1]
                news_text1 = response.text.index('<div class="post_news__text"')
                news_text2 = response.text.index('</div> <div class="post__source">')
                news_text = response.text[news_text1: news_text2]
                news_text = news_text.split(">", maxsplit=1)
                news_text = ''.join([f"<p>{p}</p>" for p in news_text[1].split("\n") if p])
                slug = url.split('news')[-1]
                slug = slug[1:-1].replace('/', '-')
                try:
                    image_url = response.html.xpath('//div[@class="post_news__photo clearfix"]/img/@src')
                    with HTMLSession() as session2:
                        resp_img = session2.get(image_url[0])
                        image_name = 'images/' + image_url[0].split("/")[-1]
                    with open(f'media/{image_name}', 'wb') as picture:
                        picture.write(resp_img.content)
                    del resp_img
                except Exception as e:
                    print(e, type(e), sys.exc_info()[-1].tb_lineno)
                    image_name = 'images/default.jpg'
                    image_url = ['default.jpg']

                post_date_index = response.text.index('<div class="post_news__date"')
                post_date_index2 = response.text.index('<div class="post__social-container">')
                post_date = response.text[post_date_index + 29: post_date_index2-7]
                days = {'Понеділок': 'Monday', 'Вівторок': 'Tuesday', 'Середа': 'Wednesday', 'Четвер': 'Thursday',
                        "П'ятниця": 'Friday', 'Субота': 'Saturday', 'Неділя': 'Sunday'}
                for day, d_tarns in days.items():
                    post_date = post_date.replace(day, d_tarns)
                months = {'січеня': 'January', 'лютого': 'February', 'березня': 'March', 'квітня': 'April',
                          'травня': 'May', 'червня': 'June', 'липня': 'July', 'серпня': 'August',
                          'вересня': 'September', 'жовтня': 'October', 'листопада': 'November', 'грудня': 'December'}
                for month, m_trans in months.items():
                    post_date = post_date.replace(month, m_trans)
                date_time_obj = datetime.strptime(post_date, '%A, %d %B %Y, %H:%M')

                reviews = response.html.xpath('//div[@class="post__views"]')
                reviews = [elem.text for elem in reviews]
                reviews = str(reviews[0]).split(' ')[0]
                try:
                    tags = response.html.xpath('//span[@class="post__tags__item"]/a/@href')
                except Exception as e:
                    tags = ['/tags/just-news/']
                new_tags = []
                for tag in tags:
                    new_tag = tag.replace("/tags/", '').replace("/", '')
                    new_tags.append(new_tag.upper())

                news = {
                    'title': title,
                    'slug': slug,
                    'news_text': news_text,
                    'image': image_name,
                    'image_url': image_url[0],
                    'news_date': date_time_obj,
                    'news_source': url,
                    'parsing_date': datetime.now().date(),
                    'source_reviews': int(reviews),
                }

                with LOCKER:
                    try:
                        item = News.objects.create(**news)
                        global COUNTER, NEWS_COUNTER
                        COUNTER += 1
                        print(f'[Item number {COUNTER} saved]', news["title"], news['news_date'])

                    except Exception as e:
                        print('Не удалось записать', type(e), e)
                        NEWS_COUNTER -= COUNTER
                        print(f'{NEWS_COUNTER} left to be parsed!')
                        return

                    for t in new_tags:
                        tag = {'name': t, 'slug': t}
                        tag, created = NewsTag.objects.get_or_create(**tag)
                        item.news_tag.add(tag)
                del response, title, news_text, reviews, slug, news, image_name, image_url, item, new_tags, new_tag, \
                    date_time_obj, tags, prox, proxies, user_agent, headers, post_date
                    # logger.debug(item)
        except Exception as e:
            print(url)
            print(type(e))
            qu.put(url)

        if qu.empty():
            break


def columns_scraper(qu):
    while True:
        url = qu.get()
        translator = Translator()
        prox = random.choice(proxies_list)
        proxies = {'http': prox, 'https': prox}
        user_agent = str(random.choice(user_agents)).strip("\t\t\t\t")
        headers = {'User-Agent': user_agent}
        try:
            with HTMLSession() as session:
                response = session.get(url, proxies=proxies, headers=headers, timeout=10)
                h1_start, h1_end = response.text.index('<h1 class="post_news__title'), response.text.index('</h1>')
                title = response.text[h1_start: h1_end]
                title = title.split(">")[-1]
                news_text1 = response.text.index('<div class="post_news__text"')
                try:
                    news_text2 = response.text.index('<div class="post__tags">')
                    news_text = response.text[news_text1: news_text2]
                except Exception as e:
                    news_text2 = response.text.index("Точка зору редакції УП може не збігатися з "
                                                     "точкою зору автора колонки.")
                    news_text = response.text[news_text1: news_text2 + 86]
                news_text = news_text.split(">", maxsplit=1)
                news_text = ''.join([f"<p>{p}</p>" for p in news_text[1].split("\n") if p])
                slug = url.split('columns')[-1]
                slug = f"column-{slug[1:-1].replace('/', '-')}"
                author_index1 = response.text.index('<div class="post_news__author"')
                author = response.text[author_index1+31: author_index1+200].split("<")
                author = author[1].split(">")[-1]
                author = translator.translate(author, dest='en')
                sleep(1)
                author = author.text
                try:
                    image_url = response.html.xpath('//div[@class="post_news__column-author"]/img/@src')
                    with HTMLSession() as session2:
                        resp_img = session2.get(image_url[0])
                        image_name = 'images/' + image_url[0].split("/")[-1]
                    with open(f'media/{image_name}', 'wb') as picture:
                        picture.write(resp_img.content)
                    del resp_img
                except Exception as e:
                    print(e, sys.exc_info()[-1].tb_lineno)
                    image_name = 'images/default.jpg'
                    image_url = ['default.jpg']
                post_date_index = response.text.index('<div class="post_news__date"')
                post_date = response.text[post_date_index + 29: post_date_index + 70]
                post_date = post_date.split("</div>")[0]
                days = {'Понеділок': 'Monday', 'Вівторок': 'Tuesday', 'Середа': 'Wednesday', 'Четвер': 'Thursday',
                        "П'ятниця": 'Friday', 'Субота': 'Saturday', 'Неділя': 'Sunday'}
                for day, d_tarns in days.items():
                    post_date = post_date.replace(day, d_tarns)
                months = {'січеня': 'January', 'лютого': 'February', 'березня': 'March', 'квітня': 'April',
                          'травня': 'May', 'червня': 'June', 'липня': 'July', 'серпня': 'August',
                          'вересня': 'September', 'жовтня': 'October', 'листопада': 'November', 'грудня': 'December'}
                for month, m_trans in months.items():
                    post_date = post_date.replace(month, m_trans)
                date_time_obj = datetime.strptime(post_date, '%A, %d %B %Y, %H:%M')

                reviews = response.html.xpath('//div[@class="post__views"]')
                reviews = [elem.text for elem in reviews]
                reviews = str(reviews[0]).split(' ')[0]
                try:
                    tags = response.html.xpath('//span[@class="post__tags__item"]/a/@href')
                except Exception as e:
                    tags = ['/tags/just-news/']
                new_tags = []
                for tag in tags:
                    new_tag = tag.replace("/tags/", '').replace("/", '')
                    new_tags.append(new_tag.upper())

                columns = {
                    'title': title,
                    'slug': slug,
                    'column_text': news_text,
                    'image': image_name,
                    'image_url': image_url[0],
                    'column_date': date_time_obj,
                    'column_source': url,
                    'parsing_date': datetime.now().date(),
                    'source_reviews': int(reviews),
                    }

                with LOCKER:
                    try:
                        item = Columns.objects.create(**columns)
                        global COUNTER
                        COUNTER += 1
                        print(f'[Item number {COUNTER} saved]', columns["title"], columns['column_date'])
                    except Exception as e:
                        print('Не удалось записать', e, type(e))
                        return
                for t in new_tags:
                    tag = {'name': t, 'slug': t}
                    tag, created = NewsTag.objects.get_or_create(**tag)
                    item.news_tag.add(tag)
                author_slug = '-'.join(author.split(" "))
                authors = {'name': author, 'slug': author_slug}
                authors, created = Author.objects.get_or_create(**authors)
                item.author_tag.add(authors)

        except Exception as e:
            print(url)
            print(type(e))
            qu.put(url)

        if qu.empty():
            break


def articles_scraper(qu):
    while True:
        url = qu.get()
        translator = Translator()
        prox = random.choice(proxies_list)
        proxies = {'http': prox, 'https': prox}
        user_agent = str(random.choice(user_agents)).strip("\t\t\t\t")
        headers = {'User-Agent': user_agent}
        try:
            with HTMLSession() as session:
                response = session.get(url, proxies=proxies, headers=headers, timeout=10)
                h1_start, h1_end = response.text.index('<h1 class="post_news__title'), response.text.index('</h1>')
                title = response.text[h1_start: h1_end]
                title = title.split(">")[-1]
                news_text1 = response.text.index('<div class="post_news__text"')
                try:
                    news_text2 = response.text.index('<div class="post__tags">')
                    news_text = response.text[news_text1: news_text2]
                except Exception as e:
                    news_text2 = response.text.index("Точка зору редакції УП може не збігатися з "
                                                     "точкою зору автора колонки.")
                    news_text = response.text[news_text1: news_text2 + 86]
                news_text = news_text.split(">", maxsplit=1)
                news_text = ''.join([f"<p>{p}</p>" for p in news_text[1].split("\n") if p])
                slug = url.split('articles')[-1]
                slug = f"article-{slug[1:-1].replace('/', '-')}"
                author_index1 = response.text.index('<div class="post_news__author"')
                author_index2 = response.text.index('<div class="post_news__photo__about"')
                author = response.text[author_index1 + 31: author_index2-25]
                author = author.split(">")[1][:-3]
                author = translator.translate(author, dest='en')
                sleep(1)
                author = author.text
                try:
                    image_url = response.html.xpath('//div[@class="article__wide-header__back"]')
                    image_url = str(image_url[0]).split("url(")
                    image_url = image_url[1].split(")")
                    with HTMLSession() as session2:
                        resp_img = session2.get(image_url[0])
                        image_name = 'images/' + image_url[0].split("/")[-1]
                        with open(f'media/{image_name}', 'wb') as picture:
                            picture.write(resp_img.content)
                        del resp_img
                except Exception as e:
                    print(e, sys.exc_info()[-1].tb_lineno)
                    image_url = ['http://default.jpg']
                    image_name = 'images/default.jpg'
                post_date_index = response.text.index('<div class="post_news__date"')
                post_date = response.text[post_date_index + 29: post_date_index + 70]
                post_date = post_date.split("</div>")[0]
                days = {'Понеділок': 'Monday', 'Вівторок': 'Tuesday', 'Середа': 'Wednesday', 'Четвер': 'Thursday',
                        "П'ятниця": 'Friday', 'Субота': 'Saturday', 'Неділя': 'Sunday'}
                for day, d_tarns in days.items():
                    post_date = post_date.replace(day, d_tarns)
                months = {'січеня': 'January', 'лютого': 'February', 'березня': 'March', 'квітня': 'April',
                          'травня': 'May', 'червня': 'June', 'липня': 'July', 'серпня': 'August',
                          'вересня': 'September', 'жовтня': 'October', 'листопада': 'November', 'грудня': 'December'}
                for month, m_trans in months.items():
                    post_date = post_date.replace(month, m_trans)
                date_time_obj = datetime.strptime(post_date, '%A, %d %B %Y, %H:%M')
                reviews = response.html.xpath('//div[@class="post__views"]')
                reviews = [elem.text for elem in reviews]
                reviews = str(reviews[0]).split(' ')[0]
                try:
                    tags = response.html.xpath('//span[@class="post__tags__item"]/a/@href')
                except Exception as e:
                    tags = ['/tags/just-news/']
                new_tags = []
                for tag in tags:
                    new_tag = tag.replace("/tags/", '').replace("/", '')
                    new_tags.append(new_tag.upper())
                articles = {
                    'title': title,
                    'slug': slug,
                    'article_text': news_text,
                    'image': image_name,
                    'image_url': image_url[0],
                    'article_date': date_time_obj,
                    'article_source': url,
                    'parsing_date': datetime.now().date(),
                    'source_reviews': int(reviews),
                }

                with LOCKER:
                    try:
                        item = Article.objects.create(**articles)
                        global COUNTER
                        COUNTER += 1
                        print(f'[Item number {COUNTER} saved]', articles["title"], articles['article_date'])
                    except Exception as e:
                        print('Не удалось записать', type(e), e)
                        return
                for t in new_tags:
                    tag = {'name': t, 'slug': t}
                    tag, created = NewsTag.objects.get_or_create(**tag)
                    item.news_tag.add(tag)
                author_slug = '-'.join(author.split(" "))
                authors = {'name': author, 'slug': author_slug}
                authors, created = Author.objects.get_or_create(**authors)
                item.author_tag.add(authors)
        except Exception as e:
            print(url)
            print(type(e))
            qu.put(url)
        if qu.empty():
            break


def get_news_links(start, task):
    if task:
        task.status = 'Started Getting Links'
        task.save()

    for _ in range(10):
        with HTMLSession() as primary_session:
            prox = random.choice(proxies_list)
            proxies = {'http': prox, 'https': prox}
            user_agent = str(random.choice(user_agents)).strip("\t\t\t\t")
            headers = {'User-Agent': user_agent}
            #print(headers)
            #breakpoint()
            #headers = {'User-Agent': 'Googlebot-News'}
            try:
                prime_response = primary_session.get("https://www.pravda.com.ua/sitemap/sitemap-news.xml",
                                                     proxies=proxies, headers=headers, timeout=10)
                current_month = str(datetime.now().date()).replace("-", '/')[:8]
                urls = prime_response.html.xpath('//@href')
                if current_month in urls[30]:
                    urls = set(urls)
                    num_links = len(urls)
                    with open(f'News/management/commands/fresh_news_links.txt', 'w') as sitemap:
                        sitemap.write('\n'.join(urls))
                    break
                urls = prime_response.html.xpath('//url/loc/text()')
                if current_month in urls[30]:
                    urls = set(urls)
                    num_links = len(urls)
                    with open(f'News/management/commands/fresh_news_links.txt', 'w') as sitemap:
                        sitemap.write('\n'.join(urls))
                    break
            except Exception as e:
                print(type(e))
    if task:
        task.status = f'COLLECTED {num_links} TO TEXT FILE FOR BACK UP!'
        task.end_time = datetime.now()
        task.save()
    print('Fresh Links Collected!')


def run_news_scraper(start, task):
    if task:
        task.status = 'Started Getting News'
        task.save()
    workers_count = 30
    news_queue = Queue()

    with open(os.path.join('News/management/commands/fresh_news_links.txt'), 'r') as file:
        for url in file:
            if "/rus/" in url:
                continue
            elif "ua/news/" in url:
                global NEWS_COUNTER
                url = url.strip("\n")
                news_queue.put(url)
                NEWS_COUNTER += 1
    print('TOTAL NEWS TO PARSE', NEWS_COUNTER)
    with ThreadPoolExecutor(max_workers=workers_count) as executor:
        for _ in range(workers_count):
            executor.submit(news_scraper, news_queue)
    if task:
        global COUNTER
        task.status = f'THERE ARE {COUNTER} NEWS COLLECTED!'
        task.end_time = datetime.now()
        task.save()


def run_columns_scraper(start, task):
    if task:
        task.status = 'Started Getting Columns'
        task.save()
    columns_queue = Queue()
    with open(os.path.join('News/management/commands/fresh_news_links.txt'), 'r') as file:
        for url in file:
            if "/rus/" in url:
                continue
            elif "ua/columns/" in url:
                global COLUMNS_COUNTER
                url = url.strip("\n")
                columns_queue.put(url)
                COLUMNS_COUNTER += 1
                print(url)
    print('TOTAL COLUMNS TO PARSE', COLUMNS_COUNTER)
    with ThreadPoolExecutor(max_workers=COLUMNS_COUNTER) as executor:
        for _ in range(COLUMNS_COUNTER):
            executor.submit(columns_scraper, columns_queue)
    if task:
        task.status = 'COLUMNS COLLECTED!'
        task.end_time = datetime.now()
        task.save()
    print('COLUMNS COLLECTED!')


def run_articles_scraper(start, task):
    if task:
        task.status = 'Started Getting Articles'
        task.save()
    articles_queue = Queue()
    with open(os.path.join('News/management/commands/fresh_news_links.txt'), 'r') as file:
        for url in file:
            if "/rus/" in url:
                continue
            elif "ua/articles/" in url:
                global ARTICLES_COUNTER
                url = url.strip("\n")
                articles_queue.put(url)
                ARTICLES_COUNTER += 1
                print(url)
    print('TOTAL ARTICLES TO PARSE', ARTICLES_COUNTER)
    with ThreadPoolExecutor(max_workers=ARTICLES_COUNTER) as executor:
        for _ in range(ARTICLES_COUNTER):
            executor.submit(articles_scraper, articles_queue)
    if task:
        task.status = 'ARTICLES COLLECTED!'
        task.end_time = datetime.now()
        task.save()
    print('ARTICLES COLLECTED!')
    messages.add_message(messages.INFO, 'New Articles Needs To Be Moderated')


class Command(BaseCommand):
    help = 'Running news scraper to database'

    def handle(self, *args, **options):
        from task.models import Task
        #task = Task.objects.create(name='run_parser')
        task1 = Task.objects.create(name='get_fresh_links')
        task2 = Task.objects.create(name='get_articles')
        task3 = Task.objects.create(name='get_columns')
        task4 = Task.objects.create(name='get_news')
        get_news_links(1, task1)
        run_articles_scraper(1, task2)
        run_columns_scraper(1, task3)
        run_news_scraper(1, task4)
        #if task:
        #    task.status = 'Started Collecting Full Data'
        #    task.save()
        #    task.status = 'DATA COLLECTED!'
        #    task.end_time = datetime.now()
        #    task.save()
        print('Done')

