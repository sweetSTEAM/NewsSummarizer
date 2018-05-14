import requests
import datetime
import re
from bs4 import BeautifulSoup
from .BaseParser import BaseParser
import time
import pytz


class Lenta(BaseParser):

    def __init__(self, **kwargs):
        super(Lenta, self).__init__(
            id='LENTA', root_url='https://lenta.ru',
            api_url='https://lenta.ru/news',
            page_type='html', **kwargs)

    def _get_news_list(self, content):
        """ Getting list of news from page content """
        return reversed(list(content.find_all(
            'div', 'item news b-tabloid__topic_news')))

    def _get_news_params_in_page(self, news):
        news_url = self.root_url + news.find('a')['href']
        news_date = self._str_to_time(
            self._time_to_str(self.curr_date) + ' '
            + news.find('span', 'time').text)
        return news_url, news_date

    def _page_url(self):
        # Example: https://lenta.ru/news/2017/02/01/
        return self.api_url + self._time_to_str(self.curr_date)

    def _next_page_url(self):
        self.curr_date -= datetime.timedelta(days=1)
        return self._page_url()

    def _parse_news(self, news_params):
        """ Getting full news params by direct url """
        html = self._get_content(news_params[0])
        date = news_params[1]
        title = html.find('h1', 'b-topic__title').get_text()
        paragraphs = html.find('div', attrs={"itemprop": "articleBody"})
        paragraphs = paragraphs.find_all('p')
        text = '\n'.join([p.get_text() for p in paragraphs])
        try:
            topic = html.find('a', 'b-header-inner__block')
            topic = re.match(
                r'\/rubrics\/([A-z0-9]+)\/', topic['href']).group(1)
        except Exception:
            topic = None
        try:
            tag = html.find('a', 'item dark active')
            tag = re.match(
                r'\/rubrics\/[A-z0-9]+\/(([A-z0-9]+)\/)?', tag['href']).group(2)
        except Exception:
            tag = None

        news_out = {'title': title, 'url': news_params[0], 'text': text,
                    'topic': topic, 'date': date, 'other': {'tag': tag}}
        return news_out

    def _time_to_str(self, time):
        return datetime.datetime.utcfromtimestamp(time).replace(
            tzinfo=pytz.utc).astimezone(self.TZ).strftime('/%Y/%m/%d/')

    def _str_to_time(self, time_str):
        return datetime.datetime.strptime(time_str, '/%Y/%m/%d/ %H:%M').replace(tzinfo=self.TZ).timestamp()
