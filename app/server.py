from flask import Flask, render_template, request,\
    redirect, url_for, jsonify
import datetime
import time
from threading import Thread
import os
from pymongo import MongoClient

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

# global events
events = []

@app.route('/')
def index():
    return redirect(
        url_for('get_content', topic_count=5))


@app.route('/<int:topic_count>')
def get_content(topic_count=5):
    # global events
    if len(events) < topic_count:
        return redirect(
            url_for('get_content', topic_count=len(events)))
    events_sliced = events[:topic_count]
    return render_template('main.html', groups_count=len(events),
                           count=analizer.get_count(), groups=events_sliced)


@app.route('/api/<int:offset>')
def api_get_content(offset=app.config['OFFSET']):
    # global events
    if offset >= len(events):
        response = jsonify(message="Topic number too large")
        response.status_code = 404
        return response
    if len(events) < offset + app.config['OFFSET']:
        events = events[offset:len(groups)]
    events = events[offset:offset + app.config['OFFSET']]
    return jsonify({'data': render_template('view.html', groups=events)})


@app.template_filter('min')
def reverse_filter(s):
    return min(s)


def update_events():
    # global events
    while True:
        if db.events.count():
            events = list(db.events.find())
        time.sleep(app.config['UPDATE_RATE'])


if __name__ == "__main__":
    # global events
    thread = Thread(target=update_events)
    thread.start()
    while not events:
        print('Waiting for data...')
        time.sleep(app.config['BOOTSTRAP_WAIT'])
    app.run(host='0.0.0.0', port=app.config['PORT'], threaded=True, use_reloader=False)
    thread.join()