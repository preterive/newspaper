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
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import bcrypt
import uuid
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from roles import roles

import logging
logging.basicConfig(filename='webapp.log',level=logging.DEBUG)


c =  {
    "DEBUG":config.c_debug,
    "SQLALCHEMY_DATABASE_URI":config.alchemy_uri,
    "SECRET_KEY":config.secret_key,
    "SQLALCHEMY_TRACK_MODIFICATIONS":False,
    "CACHE_TYPE": "simple", # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
   }

app = Flask(__name__)
app.config.from_mapping(c)
cache = Cache(app)

app.jinja_env.globals['momentjs'] = momentjs

lm = LoginManager()
lm.init_app(app)

db = SQLAlchemy(app)

class LoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired()])
    pwd = PasswordField('Passwort', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        self.email.data = self.email.data.strip()
        user = User.query.filter_by(
            email=self.email.data).first()
        if user is None:
            self.name.errors.append('Falsche Daten')
            return False

        if not user.check_password(self.pwd.data):
            self.pwd.errors.append('Falsche Daten')
            return False

        self.user = user
        return True

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(300), index=True, unique=True, nullable=False)
    pwd_hash = db.Column(db.String(300), nullable=False)
    uuid = db.Column(db.String(300), index=True, unique=True, nullable=False)
    role = db.Column(db.String(300))
    
    def __init__(self, email, pwd, role=None):
        self.email = email
        self.pwd_hash = bcrypt.encrypt(pwd)
        self.uuid = str(uuid.uuid4())
        self.role = role
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False    
    
    def get_id(self):
        return str(self.id)

    def check_password(self, password):
        return bcrypt.verify(password, self.pwd_hash)

    def __repr__(self):
        return '<User %r>' % (self.email)

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@lm.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')

@app.before_request
def before_request():
    g.db = sqlite3.connect(config.db, detect_types=sqlite3.PARSE_DECLTYPES)
    g.user = current_user

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

def get_feeds():
    f = g.db.execute('select * from feeds').fetchall()
    #f = [(i[0],i[1],i[2],i[3],i[4],urlparse(i[2]).netloc.replace('www.','')) for i in f]
    return f

@cache.cached(timeout=60, key_prefix='feeds')
def get_feeds_dict():
    f = g.db.execute('select * from feeds').fetchall()
    f = [(i[0],i[1],i[2],i[3],i[4],urlparse(i[2]).netloc.replace('www.','')) for i in f]
    feeds = dict([(i[0],i) for i in f])
    return feeds

@cache.cached(timeout=60, key_prefix='entries')
def get_entries():
    now = datetime.utcnow() + timedelta(0,10)
    t = g.db.execute('Select * from entries where published<=? order by published desc limit 100',(now,)).fetchall()
    return t

@app.route("/")
def hello():
    t = get_entries()
    if g.user is not None and g.user.is_authenticated:
        return render_template('index.html', entries=t, feeds=get_feeds_dict(), uuid=g.user.uuid)
    return render_template('index.html', entries=t, feeds=get_feeds_dict())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect('/')
    
    form = LoginForm()
    if form.validate_on_submit():
        login_user(form.user, remember = form.remember_me)
        return redirect('/')
    return render_template('login.html', form=form)

@app.route("/logout")
@login_required
def logout():
    if g.user is not None and g.user.is_authenticated:
         logout_user()
    return redirect('/login')

@app.route("/add_feed/", methods=['POST'])
@login_required
@roles(roles=['god'])
def add_feed():
    try:
        if request.method == 'POST':
            if request.json:
                feed_url = request.json['feed_url'] 
                r = requests.get(str(feed_url))
                if r.status_code == 200:
                    feed = feedparser.parse(r.text)
                    dt = datetime.utcnow() - timedelta(0,800)
                    print(feed_url)
                    insert_new_feed(feed_url, feed.feed.title, last_parsed=dt,
                            website_link=feed.feed.link)
                    return Response("{'status':'success'}", status=201, mimetype='application/json')
                else:
                    return Response(json.dumps({'status':'no success', 'code':r.status_code, 'url':feed_url}), status=500, mimetype='application/json')
    except Exception as e:
            return Response(json.dumps({'status':'no success', 'error':str(e)}), status=500, mimetype='application/json')

@app.route("/feeds/")
@login_required
@roles(roles=['god'])
def feeds():
    return render_template('feeds.html', feeds=get_feeds(), uuid = g.user.uuid)


def insert_new_feed(url, title, last_parsed = None, better_name = None, website_link = None):
    g.db.execute('INSERT OR IGNORE INTO feeds(title, url, last_parsed, better_name, website_link) VALUES (?,?,?,?,?)', (title, url, last_parsed, better_name, website_link))
    g.db.commit()


if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')
