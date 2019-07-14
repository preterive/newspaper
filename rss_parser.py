import feedparser

import requests

import multiprocessing as mp
from datetime import datetime
from dateutil.parser import parse
from time import mktime
import random
import os
from multiprocessing import Queue
from feeds_db import *

def time_struct_to_datetime(time_struct):
    return datetime.fromtimestamp(mktime(time_struct))

def datetime_converter(s):
    d = parse(s)
    n = d.strftime("%Y-%m-%d %H:%M:%S %z")
    n = datetime.strptime(n, "%Y-%m-%d %H:%M:%S %z")
    d = n
    if d.tzinfo != None:
        print(s, ' - - ', d,d.tzinfo)
        p = d.strftime("%s")
        print(p, '--', d.timestamp())
        d = datetime.utcfromtimestamp(float(p))
    return d

def opml_to_db():
    import opml
    outline = opml.parse('news.xml')
    urls = []
    for category in outline:
        for source in category:
            urls.append(source.xmlUrl)
    for url, i in download_multiple(urls):
        insert_new_feed(url=url, title=i.feed.title, last_parsed=datetime.utcnow())

def download(url):
    r = requests.get(url)
    if r.status_code != 200:
        #raise Exception("Status code: "+str(r.status_code))
        return None, None
    feed = feedparser.parse(r.text)
    return url, feed

def download_multiple(url_list):
    num_workers = mp.cpu_count()
    pool = mp.Pool(num_workers)
    feeds = pool.map(download, url_list)
    return feeds

def input_entries_into_db(feeds, url_feeds):
    feed_ids = dict([(i[2],i[0]) for i in url_feeds])
    entries = []
    for url, i in feeds:
        if url != None:
            print(i.feed.title, len(i.entries))
            for entry in i.entries:
                #print(entry.link)
                try: 
                    summary = entry.summary
                except:
                    summary = None
                e = (entry.title, entry.link, datetime.utcnow(),datetime_converter(entry.published),summary, int(feed_ids[url]))
                entries.append(e)
            update_last_parsed(url, datetime.utcnow())
        insert_new_entries(entries)

def main():
    url_feeds = select_all_feeds()
    url_list = [i[2] for i in url_feeds]
    input_entries_into_db(download_multiple(url_list), url_feeds)

if __name__ == '__main__':
    #opml_to_db()
    main()

