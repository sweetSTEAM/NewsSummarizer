import logging
import time
import os
import csv
import json
import datetime
import pytz
from nlp.analysis import Analyzer
from pymongo import MongoClient

db_client = MongoClient(
    'mongo',
    27017)
db = db_client.news

config = dict(
    UPDATE_RATE=int(os.environ.get('ANALYZER_UPDATE_RATE', 10*60)),
    BOOTSTRAP_WAIT=int(os.environ.get('ANALYZER_BOOTSTRAP_WAIT', 1.5*60))
)

logger = logging.getLogger(__name__)
if not len(logger.handlers):
    logger.setLevel(logging.INFO)
    console = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s', '%Y-%m-%d %H:%M:%S')
    console.setFormatter(formatter)
    console.setLevel(logging.INFO)
    logger.addHandler(console)


def analyze_news():
    analyzer = Analyzer()
    time.sleep(config['BOOTSTRAP_WAIT'])
    while True:
        logger.info('News in db {}'.format(db.raw_news.count()))
        if db.raw_news.count():
            new_data = list(db.raw_news.find())
            logger.info('New data length: {}'.format(len(new_data)))
            analyzer.fit(new_data)
            for row in new_data:
                db.raw_news.delete_one({'url': row['url']})
            events = analyzer.get_events()
            logger.info('New events length: {}'.format(len(events)))
            if events:
                db.events.remove({})
                db.events.insert_many(events)
        time.sleep(config['UPDATE_RATE'])


if __name__ == '__main__':
    analyze_news()
