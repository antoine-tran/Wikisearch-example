#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interface to ElasticSearch for serving search requests
#
# Tuan Tran (ttran@l3s.de)
#

import sys
from sys import argv

import os
from os.path import join,isfile,exists
from shutil import rmtree

from conn import connect,close as es_close
from elasticsearch import helpers

import pickle as pkl
import time
import logging
import heapq


QUERY = {"query":{ "multi_match" : {"query": "%s", "fields": ["text", "title", "contributor"]}}}

def empty_iter():
    '''
    a dummy generator that does not return anything. Patterns from:
    http://stackoverflow.com/questions/13243766/python-empty-generator-function
    '''
    return
    yield

def docs_iter(res):
    '''
    Wrap the ES response and return an iterator of documents, where text contents are removed on the fly
    to avoid memory overflow
    '''
    for hit in res['hits']['hits']:
        hit['_source']['text'] = ''
        yield hit

def simplesearch(es, term, k):
    '''
    Get the top-k results from ES using default ranking function. The results are stored in the
    main memory
    '''
    res = es.search(
        index='wiki',
        doc_type='page',
        body={ 
            "query": { 
                "multi_match" : {
                    "query": "%s" % term, 
                    "fields": [ "text", "title", "contributor" ]
                }
            },
            "size": k
        })

    if res == None or len(res) == 0: return empty_iter();
    return docs_iter(res)

def normalized_score(hit):
    score = hit['_score']
    if score == None: score = 0.0;
    return float(score)

def inverve_score(es, term, hit):
    '''
    An example ranking function that takes input a document, the query term, the ES connection,
    and return a new score, and at the same time update the document score to this new one

    We feed the term and ES connection to the ranking function because in general case, the ranking
    function might need additional information about the document. For example, in Learning-to-rank
    case, the document features are extracted / retrieved, including query-dependent features. Such
    extraction might need access to the index. Also, a model can be stored as a special document
    type in ES and retrieved later to provide the prediction used as the ranking score for the
    documents. 

    Note however that in our simple example here, the re-ranking are done in the client side, and
    no parallelism is employed. Some third-party plugins such as Elasticsearch Learning-to-rank
    (https://github.com/o19s/elasticsearch-learning-to-rank) can do the re-ranking in the shard
    side and thus can be parallelized easier (using sorted iterator aggregation for example).

    In this simple function, we simple take the score of a document and inverse it.
    '''
    score = normalized_score(hit)
    score = 1 / score if score != 0 else 0
    hit['_score'] = score
    return score

def rerank(results, es, term, func):
    '''
    internal sorting of the result list. NOTE: This is not in-place sorting, a new list is created. 
    It is okay because the input res can be a generator depending on the versions of ES client
    '''
    reranked = sorted(results, key=lambda x: func(es, term, x), reverse=True)
    return reranked

def rerankedsearch(es, term, k, func):
    '''
    Get the results and re-rank the scores. The ranking function has a signature: (es client, hit)
    and return a normalized score
    '''
    res = simplesearch(es, term, k)
    reranked = rerank(res, es, term, func)    
    return iter(reranked) # We return iterator to have the same format with simplesearch

def pklLoader(f):
    try:
        with open(f,'rb') as fh:
            while True:
                yield pkl.load(fh)
    except EOFError:
        pass

TMP_DIR = 'tmp'
MEMSIZE = 104857600 # The size of memory to allocate the cached array is 100MB. Must be tuned later

def memefficientrerankedsearch(es, term, k, func):
    '''
    The re-ranking of ES search results when the k is very large and the memory is limited. The algo
    is that instead of loading the big list and make the in-memory sort, we load the results page by
    page using Elasticsearch scrolling feature, and perform the external sorting.
    '''
    max_batch = min(k,100) # The maximal number of results returned in one batch. This number should be
                           # tuned based on the average size of document length, the number of shards,
                           # and the main memory of the client.
    res = helpers.scan(es,
        index='wiki',
        doc_type='page',
        scroll='1m', # Keep the connection alive for max 1 min
        size=max_batch,
        query={
            "query": { 
                "multi_match" : {
                    "query": "%s" % term, 
                    "fields": [ "text", "title", "contributor" ]
                }
            }
        })
    # sid = res['_scroll_id']
    # batch_size = res['hits']['total']

    # Write all partially sorted results into binary files in the same directory
    tmp_out_dir = join(TMP_DIR, str(time.time()))
    if not exists(tmp_out_dir):
        os.makedirs(tmp_out_dir)

    cnt = 0           # The number of results received so far
    file_counter = 0  # The file counter to check no. of I/O
    cache = []        # The list of currently fetched pages

    try:
        while cnt < k and sys.getsizeof(cache) < MEMSIZE:
            doc = next(res)
            doc['_source']['text'] = ''  # enable GC

            if sys.getsizeof(doc) > MEMSIZE - sys.getsizeof(cache): # do not have enough space to expand cache.
                                                                    # This is just an estimation, because lists
                                                                    # in python are backed by an array, and the 
                                                                    # array expansion is done by doubling the size

                # Step 1: Internal sorting for each chunk of data. This must be in-place to save memory
                cache.sort(key=lambda x: func(es, term, x), reverse=True)
                
                written_items_no = len(cache) # Only get maximum k results in total

                # Step 2: Write sorted output temp dir
                with open(join(tmp_out_dir, '%d.es' % file_counter), 'wb') as fh:
                    # We do not use comprehension or slicing here to save memory
                    for i in range(written_items_no): 
                        pkl.dump(reranked[i], fh, pkl.HIGHEST_PROTOCOL)

                file_counter += 1
                del cache[:]

            cache.append(doc)
            cnt += 1
    except StopIteration:
        pass

    if len(cache) > 0 and cnt < k: # Write the remaining results to the last file

        cache.append(doc)
        cache.sort(key=lambda x: func(es, term, x), reverse=True)
        written_items_no = min(k-cnt, len(cache))
        with open(join(tmp_out_dir, '%d.es' % file_counter), 'wb') as fh:
            # We do not use comprehension or slicing here to save memory
            for i in range(written_items_no): 
                pkl.dump(reranked[i], fh, pkl.HIGHEST_PROTOCOL)

        file_counter += 1
        cnt += written_items_no

        del cache[:] # enable GC

    logging.info('Total number of I/O writes: %d ' % file_counter)

    # Step 3: Merge sorted files using priority queue, size of the queue: O(file_counter)
    files_lst = [join(tmp_out_dir,f) for f in os.listdir(tmp_out_dir) 
            if isfile(join(tmp_out_dir,f)) and f.endswith('es')]
    merged_results = heapq.merge(*map(pklLoader, files_lst), key=lambda d: -float(d['_score']))

    return merged_results, tmp_out_dir # We return the directory of tmp files to remove them when finishing

if __name__ == "__main__":
    method = argv[1]
    if method == 'simple' or method == 'rerank' or method == 'externalrerank':
        term = argv[2]
        k = int(argv[3])
        tmpdir = None
        try:
            client = connect()
            if method == 'simple':
                res = simplesearch(client, term, k)
            elif method == 'rerank':
                res = rerankedsearch(client, term, k, inverve_score)
            else:
                res, tmpdir = memefficientrerankedsearch(client, term, k, inverve_score)
            for hit in res:
                print(str(hit).encode('utf-8'))
        finally:
            if tmpdir != None: 
                rmtree(tmpdir)
            es_close(client)


