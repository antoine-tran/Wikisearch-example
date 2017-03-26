
#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Index Wikipedia into ElasticSearch
#
# Tuan Tran (ttran@l3s.de)
#
# 
from elasticsearch import Elasticsearch, helpers
import logging
import json
from timeit import default_timer

# By default, the elasticsearch runs on the same machine
ES_HOSTS = [{'host': 'localhost', 'port': 9200}]

# Global variable to keep track of indexed pages for reporting
page_cnt = 0

def create_index():
    es = Elasticsearch(ES_HOSTS)
    # Create one index for wiki, ignore the warning of index already exists
    es.indices.create(index='wiki',ignore=400)

    return es

def es_doc(page_id,title,text,contributor):
    '''
    Convert a list of attributes into json objects ready to be indexed into ES
    '''
    return {
        '_index': 'wiki', 
        '_type': 'page',
        '_id': page_id,
        '_source': {'title': title, 'text': text, 'contributor': contributor}
    }

def index_process(opts, es, data):
    '''
    a reduce process that takes output from WikiExtractor and write out to elasticsearch
    The list of arguments are identical to reduce_process in WikiExtractor. The 'out_file'
    arguments are set to None in this mode.
    :param opts: logging options
    :param es: reference to ES index
    :param data: the buffer of page contents
    '''
    global page_cnt
    
    if not opts.write_json:
        logging.warn('Current version only supports Json output from WikiExtractor')

    interval_start = default_timer()
    helpers.bulk(es, data)
    interval_rate = len(data) / (default_timer() - interval_start)
    page_cnt += len(data)
    logging.info("Indexed %d articles (%.1f art/s)", page_cnt, interval_rate)
