import requests
import datetime
import re
from bs4 import BeautifulSoup
from .BaseParser import BaseParser
import time
from multiprocessing import cpu_count


class Tass(BaseParser):

    """docstring for Tass"""

    def __init__(self, **kwargs):
        super(Tass, self).__init__(
            id='TASS',
            root_url='http://tass.ru',
            api_url='http://tass.ru/api/news/lenta',
            page_type='json', **kwargs)
        self.news_per_page = 25

    def _get_news_list(self, content):
        """ Getting list of news from page content """
        return sorted(content['articles'],
            key=lambda x: x['time'], reverse=True)

    def _get_news_params_in_page(self, news):
        news_url = self.root_url + news['url']
        news_date = self._str_to_time(news['time'])
        topic = news['section']['title']
        title = news['title']
        return news_url, news_date, topic, title

    def _page_url(self):
        # Example: http://tass.ru/api/news/lenta?before=1492523395&limit=25
        return self.api_url + '?limit=%d&before=%d' % (
            self.news_per_page, int(self._time_to_str(self.curr_date)))

    def _next_page_url(self):
        return self._page_url()

    def _handle_page_conn_error(self):
        """
            On page connection error
            Return True to end parsing parsing, False -- go to the next page
        """
        # self.curr_date -= datetime.timedelta(minutes=30)
        return True

    def _parse_news(self, news_params):
        """ Getting full news params by direct url """
        url = news_params[0]
        html = self._get_content(url)
        date = news_params[1]
        topic = news_params[2]
        title = news_params[3]
        paragraphs = html.find('div', 'b-material-text__l')
        if not paragraphs:
            return None
        paragraphs = paragraphs.find_all('p')
        text = self._remove_tass('\n'.join([p.get_text() for p in paragraphs]))
        news_out = {'title': title, 'url': url, 'text': text,
                    'topic': topic, 'date': date, 'other': {}}
        return news_out

    def _time_to_str(self, time):
        return time

    def _str_to_time(self, time_str):
        ts = int(time_str)
        return datetime.datetime.utcfromtimestamp(ts).replace(
            tzinfo=self.TZ).astimezone(self.TZ)

    def _remove_tass(self, text):
        prefix = text[:100]
        return text[max(0, prefix.find('/.')+1):]