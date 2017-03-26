#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interface to ElasticSearch wiki index for search
#
# Tuan Tran (ttran@l3s.de)
#
from elasticsearch import Elasticsearch

ES_HOSTS = [{'host': 'localhost', 'port': 9200}]
es = Elasticsearch()
es.indices.create(index='wiki',ignore=400)