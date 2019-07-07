import feedparser

import requests

import multiprocessing as mp
from datetime import datetime
from time import mktime
import random
import os
from multiprocessing import Queue
from feeds_db import *

def time_struct_to_datetime(time_struct):
    return datetime.fromtimestamp(mktime(time_struct))

def datetime_converter(s):
    try:
        d = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
    except:
        d = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z')
    if d.tzinfo != None:
        p = d.strftime("%s")
        d = datetime.utcfromtimestamp(float(p))
    return d

def download(url):
    #time.sleep(random.randint(1,3))
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception("Status code: "+str(r.status_code))
    print(url, r.status_code)
    feed = feedparser.parse(r.text)
    return url, feed
    
processes = [ ]
url_list = ['https://www.spiegel.de/schlagzeilen/index.rss',
            'https://www.tagesschau.de/xml/rss2',
            'https://www.bild.de/rssfeeds/vw-alles/vw-alles-26970192,dzbildplus=false,sort=1,teaserbildmobil=false,view=rss2,wtmc=ob.feed.bild.xml',
            'https://www.welt.de/feeds/latest.rss',
            'https://www.n-tv.de/rss']

feeds = select_all_feeds()
url_list = [i[2] for i in feeds]

feed_ids = dict([(i[2],i[0]) for i in feeds])


num_workers = mp.cpu_count()


pool = mp.Pool(num_workers)
q = Queue()
feeds = pool.map(download, url_list)

entries = []
for url, i in feeds:
    print(i.feed.title, len(i.entries))
    for entry in i.entries:
        print(entry.link)
        e = (entry.title, entry.link, datetime.utcnow(),datetime_converter(entry.published),entry.summary, int(feed_ids[url]))
        entries.append(e)
    #insert_new_feed(url=url, title=i.feed.title, last_parsed=datetime.utcnow())
    update_last_parsed(url, datetime.utcnow())
insert_new_entries(entries)
