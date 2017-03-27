#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Utility for connecting to ElasticSearch
'''
from elasticsearch import Elasticsearch

# By default, the elasticsearch runs on the same machine
ES_HOSTS = [{'host': 'localhost', 'port': 9200}]

def connect():
    return Elasticsearch(ES_HOSTS)

def close(client):
    for conn in client.transport.connection_pool.connections:
        conn.pool.close()