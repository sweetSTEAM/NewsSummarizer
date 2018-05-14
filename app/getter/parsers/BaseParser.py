import requests
import re
import json
import datetime
from bs4 import BeautifulSoup
import logging
import time
import random
import os
import traceback
import pytz
from pymongo import MongoClient


logger = logging.getLogger(__name__)
if not len(logger.handlers):
    logger.setLevel(logging.INFO)
    console = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s', '%Y-%m-%d %H:%M:%S')
    console.setFormatter(formatter)
    console.setLevel(logging.INFO)
    logger.addHandler(console)


COLLECTION = None
def process_init():
    global COLLECTION
    db_client = MongoClient(
        'mongo',
        27017)
    db = db_client.news
    COLLECTION = db.raw_news


class BaseParser():

    """docstring for BaseParser"""

    def __init__(self, id, root_url, api_url, page_type='html'):
        self.id = id
        self.root_url = root_url  # url for news
        self.api_url = api_url  # url for pages
        self.page_type = page_type
        self.curr_date = None
        self.TZ = pytz.timezone('Europe/Moscow')

    def parse(self, pool,
                    start_time=datetime.datetime.now().replace(
            tzinfo=pytz.utc).astimezone(self.TZ), until_time=None,
                    news_count=None, topic_filter=None):
        """ Url extraction from pages in parant process """
        t_start = time.time()
        self._check_args(start_time, until_time, news_count,
                         topic_filter)
        # Some parsers do not have start time, so need to check
        start_time = start_time.timestamp()
        if until_time:
            until_time = until_time.timestamp()
        self.curr_date = start_time
        url_counter = 0
        url_to_fetch = self._page_url()
        while True:
            try:
                content = self._get_content(url_to_fetch, type_=self.page_type)
                news_list = self._get_news_list(content)
                if not news_list:
                    raise Exception('No content')
            except Exception as e:
                logger.error(
                    'Error: couldn\'t find content {} {}'.format(url_to_fetch, e))
                break

            logger.info('Look at page {}'.format(url_to_fetch))
            for news in news_list:
                try:
                    # Url always first, date always second in params
                    news_params = self._get_news_params_in_page(news)
                    if not news_params:
                        continue
                    url = news_params[0]
                    if news_params[1] > self.curr_date:
                        raise Exception('Next news should be older')
                    self.curr_date = news_params[1]
                    if ((news_count is not None and url_counter >= news_count) or
                            (until_time is not None and self.curr_date <= until_time)):
                        break
                    logger.debug('push to queue ' + str(news_params))
                    pool.map_async(self._process_news, [(news_params)])
                    url_counter += 1
                    if url_counter % 10000 == 0:
                        logger .warning(
                            '{} {} news put to queue'.format(self.id, url_counter))
                except Exception as e:
                    logger.error(
                        'Error on url {}: {} '.format(url_to_fetch, traceback.format_exc()))
            else:
                url_to_fetch = self._next_page_url()
                continue
            break

        logger.info('End of parsing, time: {}'.format(
            time.strftime('%H:%M:%S', time.gmtime(time.time() - t_start))))

    def _process_news(self, news_params):
        try:
            logger.debug('pulled ' + str(news_params))
            news_out = self._parse_news(news_params)
            logger.debug('processed ' + str(news_out))
            if not news_out:
                return
            news_out['media'] = self.id
            COLLECTION.insert_one(news_out)
            logger.info('Pushed to db ' + news_out['url'])
        except Exception as err:
            logger.error("Error {} on {}".format(
                traceback.format_exc(), news_params[0]))

    def _request(self, url):
        response = requests.get(url)
        response.raise_for_status()
        return response

    def _get_content(self, url, type_='html'):
        response = self._request(url)
        if type_ == 'html':
            return BeautifulSoup(response.text.encode('utf-8'), 'lxml')
        elif type_ == 'json':
            return response.json()
        else:
            raise Exception()

    def _check_args(self, start_time, until_time,
                    news_count, topic_filter):
        pass