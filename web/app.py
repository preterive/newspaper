import sqlite3
from flask import Flask, render_template, request, g, redirect, Response
from datetime import datetime, timedelta
import os
from urllib.parse import urlparse
from config import *
from momentjs import momentjs
from pytz import timezone
from flask_caching import Cache


c =  {
    "DEBUG":c_debug,
    "CACHE_TYPE": "simple", # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
   }

app = Flask(__name__)
app.config.from_mapping(c)
cache = Cache(app)

app.jinja_env.globals['momentjs'] = momentjs

#db = os.path.dirname(os.path.dirname(__file__))+'/feeds.db'

@app.before_request
def before_request():
    print(db)
    g.db = sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES)

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

@cache.cached(timeout=60, key_prefix='feeds')
def get_feeds():
    f = g.db.execute('select * from feeds').fetchall()
    f = [(i[0],i[1],i[2],i[3],i[4],urlparse(i[5]).netloc.replace('www.','')) for i in f]
    feeds = dict([(i[0],i) for i in f])
    return feeds

@cache.cached(timeout=60, key_prefix='entries')
def get_entries():
    now = datetime.utcnow() + timedelta(0,10)
    #now = now.strftime("%Y-%m-%d %H:%M:%S")
    t = g.db.execute('Select * from entries where published<=? order by published desc limit 200',(now,)).fetchall()
    #t = [(i[0],i[1],i[2],i[3],i[4].astimezone(timezone('Europe/Berlin')),i[5],i[6]) for i in t]
    # TODO convert datetime to local de time, so that mometjs is not needed
    return t

@app.route("/")
def hello():
    t = get_entries()
    return render_template('index.html', entries=t, feeds=get_feeds())


if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')
