import urlclustering
from urlclustering.reimprover import improve_patterns

import sys
import logging
import traceback
import re
import urllib2
import json
from copy import deepcopy
from lxml import etree
from gzip import GzipFile
from StringIO import StringIO

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def _fetch_url(url):
    logging.debug('Fetching: ' + url)
    webpage = ''
    try:
        request = urllib2.Request(url)
        request.add_header('Accept-encoding', 'gzip')
        response = urllib2.urlopen(request, timeout=10)
        if response.getcode() != 200:
            return ''
        webpage = response.read()
        if response.info().get('Content-Encoding') == 'gzip':
            webpage = GzipFile(fileobj=StringIO(webpage)).read()
    except:
        logging.debug(traceback.format_exc())
        webpage = ''
    return webpage


def _read_sitemap(xml, urls, sitemaps):
    """Reads a sitemap (xml) and returns all sitemaps and all urls found"""
    tree = etree.fromstring(xml)
    ns = [('sm', 'http://www.sitemaps.org/schemas/sitemap/0.9')]

    for node in tree.xpath('//sm:sitemap | //sitemap', namespaces=ns):
        for loc in node.xpath('sm:loc | loc', namespaces=ns):
            if loc.text.strip() not in sitemaps:
                sitemaps.append(loc.text.strip())

    for node in tree.xpath('//sm:url | //url', namespaces=ns):
        for loc in node.xpath('sm:loc | loc', namespaces=ns):
            urls.add(loc.text)


def read_sitemaps(sitemaps, max_urls=10000):
    """
        Read one or more sitemaps and return all urls.
        sitemaps: a list of sitemap urls
        max_urls: stop processing more sitemaps if max_urls already found
    """
    urls = set()
    while len(sitemaps) > 0:
        url = sitemaps.pop(0)
        webpage = _fetch_url(url)
        if len(webpage) == 0:
            continue
        # not every server returns correct Content-Encoding
        if 'sitemaps' not in webpage[:1000]:
            try:
                webpage = GzipFile(fileobj=StringIO(webpage)).read()
                if 'sitemaps' not in webpage[:1000]:
                    continue
            except:
                logging.debug(traceback.format_exc())
                continue
        # read sitemap
        logging.debug('Reading sitemap: ' + url)
        if isinstance(webpage, unicode):
            webpage = webpage.encode('utf-8')
        _read_sitemap(webpage, urls, sitemaps)
        logging.debug('URLs so far: %s' % len(urls))
        if len(urls) > max_urls:
            break
    return list(urls)[:max_urls]


def sitemaps_from_robots(url):
    """Return list of sitemaps extracted from robots.txt"""
    sitemaps = []
    webpage = _fetch_url(url)
    if len(webpage) > 0:
        matches = re.findall(ur'^\s*Sitemap\s*:\s*(.*?)$',
                             webpage, re.I | re.M)
        for match in matches:
            if match[:4] != 'http':
                if match[:1] == '/':
                    match = match[1:]
                match = url[0:url.find('/', 8)] + '/' + match
            sitemaps.append(match)
    return sitemaps


def cluster(url):
    """
    Read URLs from sitemaps and return clusters
    url is either a website (and we detect sitemaps) or a sitemap
    """
    data = {}
    if url[:4] != 'http':
        url = 'http://' + url

    if re.search(r'https?://[^/?#]+[/?#].+', url):
        sitemaps = [url]  # sitemap URL given
    else:
        robots = url.strip('/') + '/robots.txt'
        sitemaps = sitemaps_from_robots(robots)
        if not sitemaps:
            # assume sitemap.xml
            sitemaps = [url.strip('/') + '/sitemap.xml']

    if sitemaps:
        try:
            urls = read_sitemaps(sitemaps)
            if not urls:
                data['error'] = 'No URLs found in sitemap'
            else:
                data['count'] = len(urls)
                # cluster URLs
                c = urlclustering.cluster(urls)
                tmp = deepcopy(c['clusters'])
                try:
                    improve_patterns(c['clusters'])
                except:
                    c['clusters'] = tmp
                    pass
                # prepare HTML
                html = '<pre>CLUSTERS:'
                keys = sorted(c['clusters'],
                              key=lambda k: len(c['clusters'][k]),
                              reverse=True)
                for key in keys:
                    urls = c['clusters'][key]
                    html += '\n' + key[1] + ' [%s URLs]<br/>' % len(urls)
                    html += '\t' + '\n\t'.join(urls[:5])
                    html += '\n\t...%s more' % (len(urls)-5)
                html += '\n\nUNCLUSTERED:\n'
                html += '\t' + '\n\t'.join(c['unclustered'])
                html += '</pre>'
                data['html'] = html
        except:
            logging.debug(traceback.format_exc())
            data['error'] = 'An error happened while fetching sitemaps'
    else:
        data['error'] = 'No sitemaps found'

    return json.dumps(data)
