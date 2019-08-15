import sqlite3
from flask import Flask, render_template, request, g, redirect, Response
from datetime import datetime, timedelta
import os
from urllib.parse import urlparse
import config
from momentjs import momentjs
from pytz import timezone
from flask_caching import Cache
import json
import feedparser
import requests


c =  {
    "DEBUG":config.c_debug,
    "CACHE_TYPE": "simple", # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
   }

app = Flask(__name__)
app.config.from_mapping(c)
cache = Cache(app)

app.jinja_env.globals['momentjs'] = momentjs


@app.before_request
def before_request():
    g.db = sqlite3.connect(config.db, detect_types=sqlite3.PARSE_DECLTYPES)

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

@cache.cached(timeout=60, key_prefix='feeds')
def get_feeds():
    f = g.db.execute('select * from feeds').fetchall()
    f = [(i[0],i[1],i[2],i[3],i[4],urlparse(i[2]).netloc.replace('www.','')) for i in f]
    feeds = dict([(i[0],i) for i in f])
    return feeds

@cache.cached(timeout=60, key_prefix='entries')
def get_entries():
    now = datetime.utcnow() + timedelta(0,10)
    t = g.db.execute('Select * from entries where published<=? order by published desc limit 200',(now,)).fetchall()
    return t

@app.route("/")
def hello():
    t = get_entries()
    return render_template('index.html', entries=t, feeds=get_feeds())

@app.route("/add_feed/<string:key>/<path:feed_url>")
def add_feed(key, feed_url):
    if key == '345513':
        r = requests.get(str(feed_url))
        if r.status_code == 200:
            feed = feedparser.parse(r.text)
            dt = datetime.utcnow() - timedelta(0,800)
            insert_new_feed(feed_url, feed.feed.title, last_parsed=dt,
                    website_link=feed.feed.link)
            return Response("{'status':'success'}", status=201, mimetype='application/json')
        else:
            return Response(json.dumps({'status':'no success', 'code':r.status_code}), status=500, mimetype='application/json')


def insert_new_feed(url, title, last_parsed = None, better_name = None, website_link = None):
    g.db.execute('INSERT OR IGNORE INTO feeds(title, url, last_parsed, better_name, website_link) VALUES (?,?,?,?,?)', (title, url, last_parsed, better_name, website_link))
    g.db.commit()


if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')
