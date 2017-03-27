#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interface to ElasticSearch for serving search requests
#
# Tuan Tran (ttran@l3s.de)
#

import sys
from sys import argv
from conn import connect,close as es_close

QUERY = { "query":{ "multi_match" : {"query": "%s", "fields": [ "text", "title", "contributor" ]}}}

def simplesearch(client, term, k):
    '''
    Get the top-k results from ES using default ranking function. The results are cached into 
    main memory
    '''
    res = client.search(index='wiki',body= { 
        "query": { 
            "multi_match" : {
                "query": "%s" % term, 
                "fields": [ "text", "title", "contributor" ]
            }
        }
    })

    if res == None or len(res) == 0: return [];
    for hit in res['hits']['hits']:
        yield hit["_source"]

def rerankedsearch(client, term, k):
    '''
    Get the results and rerank 
    '''
    return

if __name__ == "__main__":
    if argv[1] == 'simple':
        try:
            client = connect()
            for hit in simplesearch(client,argv[2],int(argv[3])):
                print(hit.encode('utf-8'))
        finally:
            es_close(client)


