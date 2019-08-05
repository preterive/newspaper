import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('feeds.db', detect_types=sqlite3.PARSE_DECLTYPES)

def create_feeds_table():
    c = conn.cursor()
    schema= 'CREATE TABLE feeds(id integer primary key,title TEXT, url Text UNIQUE, last_parsed timestamp, better_name TEXT, website_link TEXT);'
    c.execute(schema)
    conn.commit()
    conn.close

def add_better_name_to_feeds():
    c = conn.cursor()
    schema= 'ALTER TABLE feeds ADD better_name TEXT;'
    c.execute(schema)
    conn.commit()
    conn.close

def add_website_link_to_feeds():
    c = conn.cursor()
    schema= 'ALTER TABLE feeds ADD website_link TEXT;'
    c.execute(schema)
    conn.commit()
    conn.close

def create_entries_table():
    c = conn.cursor()
    schema= 'CREATE TABLE entries(id integer primary key,title TEXT, url Text UNIQUE, parsed timestamp, published timestamp, summary Text, feed_id integer);'
    c.execute(schema)
    conn.commit()

def insert_new_feed(url, title, last_parsed = None, better_name = None, website_link = None):
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO feeds(title, url, last_parsed, better_name, website_link) VALUES (?,?,?,?,?)', (title, url, last_parsed, better_name, website_link))
    conn.commit()
def update_last_parsed(url, last_parsed, website_link = None):
    c = conn.cursor()
    c.execute('UPDATE feeds SET last_parsed = ?, website_link = ? where url = ?', (last_parsed, website_link, url))
    conn.commit()

def delete_feed(url= None, feed_id = None):
    c = conn.cursor()
    if url:
        c.execute('DELETE FROM feeds where url = ?', (url,))
    else:
        c.execute('DELETE FROM feeds where id = ?', (feed_id,))

    conn.commit()
def select_all_feeds():
    c = conn.cursor()
    c.execute('select * from feeds')
    return c.fetchall()

def select_need_parsed_feeds():
    c = conn.cursor()
    n = datetime.utcnow() - timedelta(0,300)
    c.execute('select * from feeds where last_parsed <= ?',(n,))
    return c.fetchall()

def insert_new_entries(entries):
    c = conn.cursor()
    c.executemany('INSERT or ignore into entries (title, url, parsed, published, summary, feed_id) VALUES (?,?,?,?,?,?)', entries)
    conn.commit()

def select_all_entries():
    c = conn.cursor()
    c.execute('select * from entries')
    return c.fetchall()

    
if __name__ == '__main__':
    #create_feeds_table()
    #create_entries_table()
    #delete_feed(feed_id='https://www.spiegel.de/schlagzeilen/index.rss')
    #insert_new_feed('https://www.spiegel.de/schlagzeilen/index.rss', 'SPIEGEL ONLINE - Schlagzeilen')

    #update_last_parsed('https://www.spiegel.de/schlagzeilen/index.rss', )

    add_better_name_to_feeds()
    add_website_link_to_feeds()
