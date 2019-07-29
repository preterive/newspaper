import sqlite3
from flask import Flask, render_template, request, g, redirect, Response
from datetime import datetime, timedelta
import os
app = Flask(__name__)

db = os.path.dirname(os.path.dirname(__file__))+'/feeds.db'

@app.before_request
def before_request():
    g.db = sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES)

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

@app.route("/")
def hello():
    now = datetime.utcnow() + timedelta(0,300)
    now = now.strftime("%Y/%m/%d %H:%M:%S")
    t = g.db.execute('Select * from entries where published<=? order by published desc limit 200',(now,)).fetchall()
    return render_template('index.html', entries=t)


if __name__ == '__main__':
    app.run(debug=False, port=5000, host='0.0.0.0')
