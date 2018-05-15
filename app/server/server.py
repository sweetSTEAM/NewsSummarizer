from flask import Flask, render_template, request,\
    redirect, url_for, jsonify
import datetime
import time
from threading import Thread
import os
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)
if not len(logger.handlers):
    logger.setLevel(logging.INFO)
    console = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s', '%Y-%m-%d %H:%M:%S')
    console.setFormatter(formatter)
    console.setLevel(logging.INFO)
    logger.addHandler(console)

app = Flask(__name__, template_folder='./frontend/templates',
                      static_folder='./frontend/static',
                      static_url_path='/static')
app.config.from_object(__name__)

app.config.update(dict(
    BOOTSTRAP_WAIT=int(os.environ.get('SERVER_BOOTSTRAP_WAIT', 4*60)),
    UPDATE_RATE=int(os.environ.get('SERVER_UPDATE_RATE', 5*60)),
    OFFSET=int(os.environ.get('OFFSET', 5)),
    PORT=int(os.environ.get('PORT', 5000)),
))

db_client = MongoClient(
    'mongo',
    27017)
db = db_client.news

@app.route('/')
def index():
    return redirect(
        url_for('get_content', topic_count=5))


@app.route('/<int:topic_count>')
def get_content(topic_count=5):
    events = list(db.events.find({}))
    if len(events) < topic_count:
        return redirect(
            url_for('get_content', topic_count=len(events)))
    events_sliced = events[:topic_count]
    count = sum(len(x['content']) for x in events)
    return render_template('main.html', groups_count=len(events),
                           count=count, groups=events_sliced)


@app.route('/api/<int:offset>')
def api_get_content(offset=app.config['OFFSET']):
    events = list(db.events.find({}))
    if offset >= len(events):
        response = jsonify(message="Topic number too large")
        response.status_code = 404
        return response
    if len(events) < offset + app.config['OFFSET']:
        events = events[offset:len(events)]
    events = events[offset:offset + app.config['OFFSET']]
    return jsonify({'data': render_template('view.html', groups=events)})


@app.template_filter('min')
def reverse_filter(s):
    return min(s)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=app.config['PORT'], threaded=True, use_reloader=False)
