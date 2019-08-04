import feedparser
import argparse
import os
import pickle


def get_feed_dirs(path):
    return [os.path.join(path, i) for i in os.listdir(path) if i is not 'headers' and os.path.isdir(path)]

def get_xml_files(path):
    return [os.path.join(path, i) for i in os.listdir(path) if i.endswith('.xml')]

def get_combined(path):
    try:
        return pickle.load((os.path.join(path, 'combined.p'),'rb'))
    except:
        return None, [], []


def combine_feeds(feed_xmls, feed=None, url_list=[], entries=[]):
    '''
    combines feeds
    '''
    for feed_xml in feed_xmls:
        f = open(feed_xml, 'r').read()
        d = feedparser.parse(f)
        for e in d.entries:
            url = e.link
            if url not in url_list:
                url_list.append(url)
                entries.append(e)
        feed = d.feed
    return feed, url_list, entries

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('xml_files')
    args = parser.parse_args()
    xml_files = args.xml_files
    for feed_dir in get_feed_dirs(xml_files):
        xml_files = get_xml_files(feed_dir)
        feed, url_list, entries = get_combined(feed_dir)
        pickle.dump(combine_feeds(xml_files,feed=feed,url_list=url_list,entries=entries), open(os.path.join(feed_dir, 'combined.p'), 'wb'))
        for xml in xml_files:
            os.remove(xml)
