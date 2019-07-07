import feedparser

import requests

import multiprocessing as mp
import time
import random
import os
from multiprocessing import Queue


def download(url):
    #time.sleep(random.randint(1,3))
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception("Status code: "+str(r.status_code))
    print(url, r.status_code)
    feed = feedparser.parse(r.text)
#    for item in feed.entries:
#        q.put(item)
    return feed
    
processes = [ ]
url_list = ['https://www.spiegel.de/schlagzeilen/index.rss',
            'https://www.tagesschau.de/xml/rss2',
            'https://www.bild.de/rssfeeds/vw-alles/vw-alles-26970192,dzbildplus=false,sort=1,teaserbildmobil=false,view=rss2,wtmc=ob.feed.bild.xml',
            'https://www.welt.de/feeds/latest.rss',
            'https://www.n-tv.de/rss']

num_workers = mp.cpu_count()

pool = mp.Pool(num_workers)
q = Queue()
feeds = pool.map(download, url_list)
for i in feeds:
    print(i.feed.title, len(i.entries))
'''
for url in url_list:
    pool.apply_async(download, args = (url, q,))

pool.close()
pool.join()
'''
'''
q = Queue()
#for i in range(10):
for i in url_list:
    t = multiprocessing.Process(target=download, args=(i,q))
    processes.append(t)
    t.start()
for process in processes:
    process.join()

mylist = [ ]
while not q.empty():
    rss = q.get()
    mylist.append(rss)
print("Done!")
print(len(mylist))
'''
