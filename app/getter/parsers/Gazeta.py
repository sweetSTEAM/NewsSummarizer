import requests
from datetime import datetime, timedelta
import datetime
from bs4 import BeautifulSoup
from .BaseParser import BaseParser
import pytz


class Gazeta(BaseParser):

    def __init__(self, **kwargs):
        super(Gazeta, self).__init__(
            id='GAZETA', root_url='https://www.gazeta.ru',
            api_url='https://www.gazeta.ru/news/?p=page&d=',
            page_type='html', **kwargs)

    def _get_news_list(self, content):
        """ Getting list of news from page content """
        return content.find_all('article',
                                attrs={"itemprop": "itemListElement"})

    def _get_news_params_in_page(self, news):
        news_url = self.root_url + news.find('a',
                                             attrs={"itemprop": 'mainEntityOfPage url'})['href']
        timestamp = int(news.find('meta',
                                  attrs={"itemprop": "position"})['content'])
        return news_url, timestamp

    def _page_url(self):
        # Example: https://www.gazeta.ru/news/?p=page&d=09.04.2017_12:44
        return self.api_url + self._time_to_str(self.curr_date)

    def _next_page_url(self):
        return self._page_url()

    def _parse_news(self, news_params):
        """ Getting full news params by direct url """
        html = self._get_content(news_params[0])
        date = news_params[1]
        paragraphs = html.find('article').find_all('p')
        text = '\n'.join([p.get_text() for p in paragraphs])
        topic = html.find('div', 'b-navbar-main').find('div',
                                                       'item active').find('a').text
        try:
            tag = html.find('div', 'news_theme') or html.find(
                'div', 'border_up_red')
            tag = tag.find('a').text
        except Exception as e:
            tag = None
        title = html.find(
            'h1', 'article-text-header') or html.find('h1', 'txtclear')
        title = title.get_text()
        news_out = {'title': title, 'url': news_params[0], 'text': text,
                    'topic': topic, 'date': date, 'other': {'tag': tag}}
        return news_out

    def _time_to_str(self, time):
        return datetime.datetime.utcfromtimestamp(time).replace(
            tzinfo=pytz.utc).astimezone(self.TZ).strftime('%d.%m.%Y_%H:%M')

    def _get_content(self, url, type_='html'):
        response = self._request(url)
        if type_ == 'html':
            return BeautifulSoup(response.text.encode('cp1251'), 'lxml')
        elif type_ == 'json':
            return response.json()
        else:
            raise Exception()