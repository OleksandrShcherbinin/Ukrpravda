from django.core.management.base import BaseCommand, CommandError
from concurrent.futures import ThreadPoolExecutor
from requests_html import HTMLSession
from googletrans import Translator
from datetime import datetime
from slugify import slugify
from threading import Lock
from News.models import *
from queue import Queue
import random
import logging
import sys
import os

LOCKER = Lock()
logger = logging.getLogger('django')

#translator = Translator()
#text = 'якийсь текст'
#result = translator.translate(text, dest='en')

with open(os.path.join('News/management/commands/user_agents.txt'), 'r') as f:
    user_agents = f.read().split('\n')

with open(os.path.join('News/management/commands/fresh_socks.txt'), 'r') as f:
    proxies_list = f.read().split('\n')


def scraper(qu):
    while True:
        url = qu.get()
        prox = random.choice(proxies_list)
        proxies = {'http': prox, 'https': prox}
        user_agent = str(random.choice(user_agents)).strip("\t\t\t\t")
        headers = {'User-Agent': user_agent}
        print(user_agent)

        with HTMLSession() as session: #browser_args=["--no-sandbox", f'--user-agent={user_agent}']) as session:
            try:
                response = session.get(url, proxies=proxies, headers=headers, timeout=10)
                response.html.render()
                print(response.html.text)
                breakpoint()
                title = response.html.xpath('//h1')[0].text
                #h1_start, h1_end = response.text.index('<h1 class="post_news__title">'), response.text.index('</h1>')
                #title = response.text[h1_start+29: h1_end]
                print(title)
                title = [elem.text for elem in title]
                print(title)
                breakpoint()
                #title_code = [ord(c) for c in title]
                #print(title_code)
                #news_text = response.html.find('div[@class="post_news__text"]')
                news_text = response.html.xpath('//div[@class="post_news__text"]/p[4]/text()')
                print(news_text)
                #news_text1 = response.text.index('<div[@class="post_news__text">')
                #news_text2 = response.text.index('</div>')
                #news_text = response.text[news_text1+30: news_text2]
                news_text = [elem.text for elem in news_text]
                #news_text = ''.join([f'<p>{p}</p>' for p in news_text[0].split("\n") if p])
                print(news_text)
                breakpoint()

                slug = url.split('/')[-2]
                print(url)
                print(slug)
                try:
                    image_url = response.html.xpath('//div[@class="post_news__photo clearfix"]/img/@src')
                except Exception as e:
                    image_url = ""
                print(image_url)
                try:
                    with HTMLSession() as session2:
                        resp_img = session2.get(image_url[0])
                        image_name = 'images/' + image_url[0].split("/")[-1]
                    with open(f'media/{image_name}', 'wb') as picture:
                        picture.write(resp_img.content)
                    del resp_img
                except Exception as e:
                    print(e, type(e), sys.exc_info()[-1].tb_lineno)
                    image_name = 'default.jpg'
                print(image_name)
                post_date = response.html.xpath('//div[@class="post_news__date"]')
                post_date = [elem.text for elem in post_date]
                print(post_date)
                reviews = response.html.xpath('//div[@class="post__views"]')
                reviews = [elem.text for elem in reviews]
                reviews = str(reviews[0]).split(' ')[0]
                print(reviews)
                tags = response.html.xpath('//span[@class="post__tags__item"]/*')
                tags = [elem.text for elem in tags]

                print(tags)

                news = {
                    'title': title[0],
                    'slug': slug,
                    'news_text': news_text[0],
                    'image': image_name,
                    'image_url': image_url,
                    'news_date': post_date[0],
                    'news_source': url,
                    'parsing_date': datetime.now().date(),
                    'source_reviews': int(reviews),
                }
                print(news)

                with LOCKER:
                    try:
                        item = News.objects.create(**news)
                        print('[Item saved]', news["title"])
                    except Exception as e:
                        print('Не удалось записать позицию', type(e), e)
                        return

                    breakpoint()
                    tags = {'name': tags[0], 'slug': slugify(tags[0])}
                    tags, created = NewsTag.objects.get_or_create(**tags)
                    item.news_tag.add(tags)
                    #logger.debug(item)

            except Exception as e:
                print(e, type(e))
                qu.put(url)
        if qu.empty():
            break


def get_news_links():

    with HTMLSession() as primary_session:
        try:
            prime_response = primary_session.get("https://www.pravda.com.ua/sitemap/sitemap-news.xml")
            urls = prime_response.html.xpath('//url/loc/text()')
            # adding sitemap file for backup just in case
            with open(f'News/management/commands/fresh_news_links.txt', 'w') as sitemap:
                sitemap.write('\n'.join(urls))
        except Exception as e:
            print(e, type(e))

    run_news_scraper()


def run_news_scraper():
    workers_count = 1
    print('Start')

    news_queue = Queue()
    articles_queue = Queue()
    columns_queue = Queue()
    with open(os.path.join('News/management/commands/fresh_news_links.txt'), 'r') as file:
        count = len(open(os.path.join('News/management/commands/fresh_news_links.txt')).readlines())
        print('Number of News', count)
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
                url = url.strip("\n")
                news_queue.put(url)
            elif "ua/articles/" in url:
                url = url.strip("\n")
                articles_queue.put(url)
            elif "ua/columns/" in url:
                url = url.strip("\n")
                columns_queue.put(url)

    with ThreadPoolExecutor(max_workers=workers_count) as executor:
        for _ in range(workers_count):
            executor.submit(scraper, news_queue)


class Command(BaseCommand):
    help = 'Running fashion_items parser to database'

    def handle(self, *args, **options):
        #from task.models import Task
        #task = Task.objects.create(name='run_parser')
        get_news_links()

        print('Done')
