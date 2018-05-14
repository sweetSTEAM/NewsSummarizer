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
    'localhost',
    27017)
db = db_client.news

config = dict(
    UPDATE_RATE=int(os.environ.get('ANALYZER_UPDATE_RATE', 10*60)),
    BOOTSTRAP_WAIT=int(os.environ.get('ANALYZER_BOOTSTRAP_WAIT', 1.5*60))
)


def analyze_news():
    analyzer = Analyzer()
    time.sleep(config['BOOTSTRAP_WAIT'])
    while True:
        if db.raw_news.count():
            new_data = list(db.raw_news.find())
            print('New data length: {}'.format(len(new_data)))
            analyzer.fit(new_data)
            for row in new_data:
                db.raw_news.delete_one({'url': row['url']})
            db.events.remove({})
            db.events.insert_many(analyzer.get_events())
        time.sleep(config['UPDATE_RATE'])


if __name__ == '__main__':
    analyze_news()
