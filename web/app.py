import sqlite3
from flask import Flask, render_template, request, g, redirect, Response
from datetime import datetime, timedelta
import os
from urllib.parse import urlparse
import config
from momentjs import momentjs
from pytz import timezone
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required


c =  {
    "DEBUG":config.c_debug,
    "SQLALCHEMY_DATABASE_URI":config.alchemy_uri,
    "SECURITY_PASSWORD_SALT":config.pwd_salt,
    "SECRET_KEY":config.secret_key,
    "CACHE_TYPE": "simple", # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
   }

app = Flask(__name__)
app.config.from_mapping(c)
cache = Cache(app)

app.jinja_env.globals['momentjs'] = momentjs

userdb = SQLAlchemy(app)

# Define models
roles_users = userdb.Table('roles_users',
        userdb.Column('user_id', userdb.Integer(), userdb.ForeignKey('user.id')),
        userdb.Column('role_id', userdb.Integer(), userdb.ForeignKey('role.id')))

class Role(userdb.Model, RoleMixin):
    id = userdb.Column(userdb.Integer(), primary_key=True)
    name = userdb.Column(userdb.String(80), unique=True)
    description = userdb.Column(userdb.String(255))

class User(userdb.Model, UserMixin):
    id = userdb.Column(userdb.Integer, primary_key=True)
    email = userdb.Column(userdb.String(255), unique=True)
    password = userdb.Column(userdb.String(255))
    active = userdb.Column(userdb.Boolean())
    confirmed_at = userdb.Column(userdb.DateTime())
    roles = userdb.relationship('Role', secondary=roles_users,
    backref=userdb.backref('users', lazy='dynamic'))

user_datastore = SQLAlchemyUserDatastore(userdb, User, Role)
security = Security(app, user_datastore)

#@app.before_first_request
def create_user():
    userdb.create_all()
    user_datastore.create_user(email='test@test.de', password='test')
    userdb.session.commit()


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

@app.route("/add_feed")
@login_required
def add_feed():
    return render_template("feeds.html")


if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')
