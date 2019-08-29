import feedparser

import requests

import multiprocessing as mp
from datetime import datetime
from dateutil.parser import parse
import dateparser
from time import mktime, strftime
from calendar import timegm
import random
import os
from multiprocessing import Queue
from feeds_db import *
from bs4 import BeautifulSoup

def cestDateHandler(date_string):
    '''
    custom date handler for feedparser 
    handles cest 
    '''
    if 'CEST' in date_string:
        date_string = date_string.replace('CEST', '+0200')
        return feedparser._parse_date_rfc822(date_string)
    else:
        return None
feedparser.registerDateHandler(cestDateHandler)


def time_struct_to_datetime(time_struct):
    return datetime.utcfromtimestamp(timegm(time_struct))


def opml_to_db():
    import opml
    outline = opml.parse('news.xml')
    urls = []
    for category in outline:
        for source in category:
            urls.append(source.xmlUrl)
    for url, i in download_multiple(urls):
        insert_new_feed(url=url, title=i.feed.title, last_parsed=datetime.utcnow())

def download(url, save = True):
    # conditional get
    headers_path = 'xml_files/headers/'+url.replace('/','_').replace(':','')+'.headers'
    last_modified, etag = None, None
    if os.path.exists(headers_path):
        h = [i.rstrip() for i in open(headers_path, 'r').read().split('\n')]
        last_modified = h[0] if h[0] != 'None' else None
        etag = h[1] if h[1] != 'None' else None
    headers = {'If-Modified-Since':last_modified, 'If-None-Match':etag, 
            'Last-Modified':last_modified}
    r = requests.get(url, headers=headers)
    if r.status_code != 200 and r.status_code != 304:
        return None, None
    etag = r.headers.get('ETag')
    last_modified = r.headers.get('Last-Modified')
    h = open(headers_path, 'w')
    h.write(str(last_modified)+'\n'+str(etag))
    h.close()
    # parsing
    if r.status_code == 200:
        feed = feedparser.parse(r.text)
        # save xml 
        if save:
            dir_path = 'xml_files/'+feed.channel.link.replace('/','_').replace(':','')
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            dt = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
            f = open(dir_path+'/'+dt+'.xml', 'w')
            f.write(r.text)
            f.close()
        return url, feed
    return None, None

def download_multiple(url_list):
    num_workers = mp.cpu_count()*2
    pool = mp.Pool(num_workers)
    feeds = pool.map(download, url_list)
    return feeds

def input_entries_into_db(feeds, url_feeds):
    feed_ids = dict([(i[2],i[0]) for i in url_feeds])
    entries = []
    for url, i in feeds:
        if url != None:
            print(i.feed.title, len(i.entries), url)
            for entry in i.entries:
                #print(entry.link)
                try: 
                    summary = entry.summary
                except:
                    summary = None
                dt = time_struct_to_datetime(entry.published_parsed)
                #print(entry.published, time_struct_to_datetime(entry.published_parsed), entry.link)
                if dt:
                    if summary:
                        summary = BeautifulSoup(entry.summary, "lxml").text
                    e = (entry.title, entry.link, datetime.utcnow(),dt,summary, int(feed_ids[url]))
                    entries.append(e)
            update_last_parsed(url, datetime.utcnow(), website_link=i.feed.link)
        insert_new_entries(entries)

def create_file_structure():
    if not os.path.exists('xml_files/'):
        os.mkdir('xml_files/')
    if not os.path.exists('xml_files/headers/'):
        os.mkdir('xml_files/headers/')

def main():
    # url_feeds = select_all_feeds()
    url_feeds = select_need_parsed_feeds()
    url_list = [i[2] for i in url_feeds]
    input_entries_into_db(download_multiple(url_list), url_feeds)

if __name__ == '__main__':
    #opml_to_db()
    create_file_structure()
    print(datetime.utcnow()) # for log
    main()

