import sqlite3

conn = sqlite3.connect('feeds.db')
c = conn.cursor()

def create_feeeds_table():
    schema= 'CREATE TABLE feeds(id integer primary key,title TEXT, url Text UNIQUE, last_parsed Real);'
    c.execute(schema)
    conn.commit()
    conn.close

def insert_new_feed(url, last_parsed = None):
    c.execute('INSERT OR IGNORE INTO feeds(url, last_parsed) VALUES (?,?)', (url, last_parsed))
    conn.commit()
def select_all_feeds():
    c.execute('select * from feeds')
    return c.fetchall()
#insert_new_feed('https://www.spiegel.de/schlagzeilen/index.rss')
print(select_all_feeds())
