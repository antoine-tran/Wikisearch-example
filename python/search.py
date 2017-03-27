#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interface to ElasticSearch for serving search requests
#
# Tuan Tran (ttran@l3s.de)
#

import sys
from conn import connect,close as es_close

QUERY = { "query":{ "multi_match" : {"query": "%s", "fields": [ "text", "title", "contributor" ]}}}

def search(client, term, k):
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
        print("%(title)s %(contributor)s" % hit["_source"])

if __name__ == "__main__":
    client = connect()
    search(client,sys.argv[1],int(sys.argv[2]))
    es_close(client)


