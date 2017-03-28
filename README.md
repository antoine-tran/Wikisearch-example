** Wikisearch ** is a small example to demonstrate how to index Wikipedia XML dump into ElasticSearch and query from it using Python 3. The program supports the following minimal features:

* Clean Wikimedia syntax and extract article title, contributor and text content using the modified version of [WikiExtractor tool](https://github.com/attardi/wikiextractor)
* Index into ElasticSearch using [Elasticsearch-python](https://github.com/elastic/elasticsearch-py)

Note that the original version of WikiExtractor uses multi-threading to achieve the parallelism, and might cause some troubles when running on Python 3 and Mac OS X. In this program,  
