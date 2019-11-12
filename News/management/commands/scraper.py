from django.core.management.base import BaseCommand
from concurrent.futures import ThreadPoolExecutor
from requests_html import HTMLSession
from googletrans import Translator
from datetime import datetime, timezone
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


def news_scraper2(qu):
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
                news_text = response.text[news_text1 + 101: news_text2]
                news_text = ''.join([f"<p>{p}</p>" for p in news_text.split("\n") if p])

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
                    print(e, type(e))
                    #print(e, type(e), sys.exc_info()[-1].tb_lineno)
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
                        global COUNTER
                        COUNTER += 1
                        print(f'[Item number {COUNTER} saved]', news["title"], news['news_date'])

                    except Exception as e:
                        print('Не удалось записать', type(e), e)
                        return

                for t in new_tags:
                    tag = {'name': t, 'slug': t}
                    tag, created = NewsTag.objects.get_or_create(**tag)
                    item.news_tag.add(tag)
                    # logger.debug(item)
        except Exception as e:
            #print(e, type(e))
            qu.put(url)

        if qu.empty():
            break


def columns_scraper2(qu):
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
                print(title)
                news_text1 = response.text.index('<div class="post_news__text"')
                news_text2 = response.text.index('<div class="post__tags">')
                news_text = response.text[news_text1 + 104: news_text2]
                news_text = ''.join([f"<p>{p}</p>" for p in news_text.split("\n") if p])
                print(news_text)
                breakpoint()
                slug = url.split('columns')[-1]
                slug = f"column-{slug[1:-1].replace('/', '-')}"
                author_index1 = response.text.index('<div class="post_news__author"')
                author_index2 = response.text.index('</a><span class="post_news__author__link"')
                author = response.text[author_index1+31: author_index2]
                author = author.split(">")[-1]
                author = translator.translate(author, dest='en')
                sleep(1)
                author = author.text
                print(author)
                breakpoint()
                try:
                    image_url = response.html.xpath('//div[@class="post_news__column-author"]/img/@src')
                    with HTMLSession() as session2:
                        resp_img = session2.get(image_url[0])
                        image_name = 'images/' + image_url[0].split("/")[-1]
                    with open(f'media/{image_name}', 'wb') as picture:
                        picture.write(resp_img.content)
                    del resp_img
                except Exception as e:
                    print(e, type(e))
                    # print(e, type(e), sys.exc_info()[-1].tb_lineno)
                    image_name = 'images/default.jpg'
                    image_url = ['default.jpg']
                post_date_index = response.text.index('<div class="post_news__date"')
                post_date_index2 = response.text.index('<div class="post__social-container">')
                post_date = response.text[post_date_index + 29: post_date_index2 - 7]
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
                print(reviews)
                breakpoint()
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
            print(e)
            qu.put(url)

        if qu.empty():
            break


def articles_scraper2(qu):
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
                news_text2 = response.text.index('<div class="post__tags">')
                news_text = response.text[news_text1 + 105: news_text2]
                news_text = ''.join([f"<p>{p}</p>" for p in news_text.split("\n") if p])
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
                    print(e, type(e))
                    # print(e, type(e), sys.exc_info()[-1].tb_lineno)
                    image_url = ['http://default.jpg']
                    image_name = 'images/default.jpg'
                post_date_index = response.text.index('<div class="post_news__date"')
                post_date_index2 = response.text.index('<div class="post__social-container">')
                post_date = response.text[post_date_index + 29: post_date_index2 - 14]

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
                print(reviews)

                try:
                    tags = response.html.xpath('//span[@class="post__tags__item"]/a/@href')
                except Exception as e:
                    tags = ['/tags/just-news/']
                new_tags = []
                for tag in tags:
                    new_tag = tag.replace("/tags/", '').replace("/", '')
                    new_tags.append(new_tag.upper())
                print(new_tags)

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
                print(author_slug)
                authors = {'name': author, 'slug': author_slug}
                authors, created = Author.objects.get_or_create(**authors)
                item.author_tag.add(authors)

        except Exception as e:
            print(e)
            qu.put(url)
        if qu.empty():
            break


def get_news_links2():

    for _ in range(10):
        with HTMLSession() as primary_session:
            prox = random.choice(proxies_list)
            proxies = {'http': prox, 'https': prox}
            user_agent = str(random.choice(user_agents)).strip("\t\t\t\t")
            headers = {'User-Agent': user_agent}
            try:
                prime_response = primary_session.get("https://www.pravda.com.ua/sitemap/sitemap-news.xml",
                                                     proxies=proxies, headers=headers, timeout=10)
                current_month = str(datetime.now().date()).replace("-", '/')[:8]
                urls = prime_response.html.xpath('//@href')
                if current_month in urls[30]:
                    urls = set(urls)
                    with open(f'News/management/commands/fresh_news_links.txt', 'w') as sitemap:
                        sitemap.write('\n'.join(urls))
                    break
                urls = prime_response.html.xpath('//url/loc/text()')
                if current_month in urls[30]:
                    urls = prime_response.html.xpath('//url/loc/text()')
                    urls = set(urls)
                    with open(f'News/management/commands/fresh_news_links.txt', 'w') as sitemap:
                        sitemap.write('\n'.join(urls))
                    break

            except Exception as e:
                print(e, type(e))

    run_news_scraper2()


def run_news_scraper2():
    workers_count = 30
    news_queue = Queue()

    with open(os.path.join('News/management/commands/fresh_news_links.txt'), 'r') as file:
        #start = start if start <= count else 0
        #end = end if end <= count else count
        #try:
        #    urls = file.readlines()[start:end]
        #except Exception as e:
        #    print(e, type(e))
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
            executor.submit(news_scraper2, news_queue)


def run_columns_scraper():
    #workers_count = 30
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
    print('TOTAL COLUMNS TO PARSE', COLUMNS_COUNTER)
    with ThreadPoolExecutor(max_workers=1) as executor:
        for _ in range(1):
            executor.submit(columns_scraper2, columns_queue)


def run_articles_scraper():
    #workers_count = 1
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
            executor.submit(articles_scraper2, articles_queue)


class Command(BaseCommand):
    help = 'Running news scraper to database'

    def handle(self, *args, **options):
        #from task.models import Task
        #task = Task.objects.create(name='run_parser')
        get_news_links2()
        #run_news_scraper2()
        #run_columns_scraper()
        #run_articles_scraper()
        print('Done')