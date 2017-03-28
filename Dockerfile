# 
# Dockerfile to set up application in standalone model
# 
# 1. Install python third-party libraries
# 2. Download the wikipedia XML dump
# 3. Run the system
# 
# Tuan Tran
# ttran@L3S.de
#

FROM library/python

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

# Upload source code
ADD python /home
WORKDIR "/home"

# Install the libraries
RUN pip install -r requirements.txt

# Download the data
RUN wget -O enwiki.xml.bz2 "http://download.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2" \
     && mkdir -p /data \
     && tar -xzC /data -f enwiki.xml.bz2 \
     && rm enwiki.xml.bz2

# Two phases:
# 1. Index. Default with 10 processes, flush to the index after every 10000 parsed pages, and does not pring the logging messages
#
# 2. Search. Follow the prompt instructions. First we choose the methods:
# simple - using ElasticSearch default setting;
# rerank - Rerank the ElasticSearch results using inversed ranking
# externalrerank - Rerank the ElasticSearch results when the number of results is large, and the memory is limited
#
# For each method, there are two subsequent parameters:
# term - a single term to query
# k - the number of desired results

CMD python WikiExtractor.py --json --processes 10 --quiet --batch 10000 /data/enwiki.xml && python search.py