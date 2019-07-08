import sqlite3
from flask import Flask, render_template, request, g, redirect, Response
app = Flask(__name__)

DATABASE = '/Users/moritzjager/Desktop/Python/newspaper/feeds.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.route("/")
def hello():
    return "Hello World!"


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
