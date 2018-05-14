from parsers import Gazeta, Tass, Lenta, Vedomosti, Novaya, Meduza, process_init
import logging
import time
import os
import csv
import json
import datetime
import pytz
from pymongo import MongoClient
from multiprocessing import Pool, cpu_count

db_client = MongoClient(
    'mongo',
    27017)
db = db_client.news

config = dict(
    UPDATE_RATE=int(os.environ.get('GETTER_UPDATE_RATE', 10*60)),
    HOURS_INIT=int(os.environ.get('HOURS_INIT', 12)),
    NUM_PROCESSES=int(os.environ.get('NUM_PROCESSES', cpu_count())),
)

logger = logging.getLogger('getter')
if not len(logger.handlers):
    logger.setLevel(logging.INFO)
    console = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s', '%Y-%m-%d %H:%M:%S')
    console.setFormatter(formatter)
    console.setLevel(logging.INFO)
    logger.addHandler(console)

def load_news():
    last_dt = None
    while True:
        logger.info('iteration started')
        pool = Pool(processes=config['NUM_PROCESSES'], initializer=process_init)
        parsers_ = [
            Gazeta(),
            Tass(),
            Meduza(),
            Lenta(),
            Vedomosti(),
            Novaya()
        ]
        now = datetime.datetime.now()
        if not last_dt:
            last_dt = now - datetime.timedelta(hours=config['HOURS_INIT'])
        for parser in parsers_:
            logger.info(parser.id + ' ' + str(last_dt))
            parser.parse(pool, until_time=last_dt)
        last_dt = now

        pool.close()
        pool.join()
        logger.info('New news: {}'.format(db.raw_news.count()))
        time.sleep(config['UPDATE_RATE'])


if __name__ == '__main__':
    load_news()
