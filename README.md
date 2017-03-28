## Wikisearch-example

**Wikisearch-example** is a small toolkit to demonstrate how to index Wikipedia XML dump into ElasticSearch and query from it using Python 3 in standalone mode (For indexing Wikipedia in distributed mode, check [Hedera](https://github.com/antoine-tran/Hedera) ). The program supports the following minimal features:

* Clean Wikimedia syntax and extract article title, contributor and text content using the modified version of [WikiExtractor tool](https://github.com/attardi/wikiextractor)
* Index into ElasticSearch using [Elasticsearch-python](https://github.com/elastic/elasticsearch-py)
* Query into ElasticSearch using three methods: Default ranking (simple), cache-and-re-ranking (rerank), and disk-based-re-ranking (externalrerank). The externalrerank is to demonstrated how to query the index when the client machine has limited memory and needs to process a large amount of results, and not suitable for real-time query scenarios.

Note that the original version of WikiExtractor uses multi-threading to achieve the parallelism, and might cause some troubles when running on Python 3 and Mac OS X. In this program, I changed to make the tool run in separate processes, thus have greater flexibility and avoid race conditions and dead locks.

## Getting started
### Using Docker

If you have Docker installed, simply download the code and cd into the directory. Then run:
```shell
$ docker-compose up
```

This will download the XML latest dump file, build the image with necessary libraries, start the Elasticsearch cluster, and run the indexing service. The whole process will take a while. If there is no error, run:

```shell
$ docker build -t essearch -f Dockerfile.search .
```

This will build the Docker image for the client. Now to run the demo query:

```shell
$ docker run -i essearch
```

and follow the instructions.


