import time

from elasticsearch import Elasticsearch
from elasticsearch import helpers
import sys
import os
import conf
sys.path.append(conf.offline)
from query_preprocesser import preprocess
import nltk
_lucene_docs_txt = conf.exp_models_dir + '/lucene_docs.txt'


"""
The meta-field '_type' (i.e., index_type or doc_type in some tutorials) was removed since ElasticSearch 7.0.0.
See: https://www.elastic.co/guide/en/elasticsearch/reference/current/removal-of-types.html.
https://medium.com/elasticsearch/introduction-to-elasticsearch-queries-b5ea254bf455
"""

index_name = 'shellfusion_plusplus'
#es = Elasticsearch(["https://elastic:Qgh3mGbgvQsuXu-zXEZ_@172.21.144.1:9200"],verify_certs=False)
#es = Elasticsearch([f"https://elastic:Wy6DGGO+C2vKv2b_ODX_@quinv.mistgpu.xyz:9401"],verify_certs=False)#es01
es = Elasticsearch([f"https://elastic:w6Cu4xOWITrZWZpNPA-_@quinv.mistgpu.xyz:9401"],verify_certs=False)#es02

def readTxt(txt):
    data = []
    with open(txt,"r") as f:
        docs = f.readlines()
    return docs

def createIndex():
    """
    Create an index which will be used for indexing a set of docs (id, content).
    """
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        print('delete index: ' + index_name)
    body = {
        "mappings": {
            "properties": {
                "id": {
                    "type": "text"
                },
                "content": {
                    "type": "text",
                    "analyzer": "whitespace"
                }
            }
        }
    }

    es.indices.create(index=index_name, body=body)
    print('create index: ' + index_name)


def indexDocs(docs_txt):   
    """
    Index the docs in a txt file
    """
    createIndex()

    batch = []
    doc = readTxt(docs_txt)
    for line in doc:
        sa = line.split('===>')
        #print(sa[0])
        if len(sa) == 2:
            batch.append({
                '_index': index_name,
                '_source': {
                    'id': sa[0].strip(),
                    'content': sa[1].strip()
                }
            })
            if len(batch) == 50000:
                print('indexing a batch ...')
                helpers.bulk(es, batch, request_timeout=100)
                batch = []

    if len(batch) > 0:
        print('indexing a batch ...')
        helpers.bulk(es, batch, request_timeout=100)

def boostSearch(originQuery, Importance, res_txt):
    """
    Search for a query string.
    with importance boost
    """
    topImportance = preprocess(' '.join([' '.join(word) for imporE,word in Importance.items() if imporE=="4"]))
    query = {
        "query": {
            "boosting":{
            "positive":{
            'match': {
                'content': originQuery
            }
            },
            "negative":{
            'match': {
                'content': topImportance
            }
            },
            "negative_boost":1.0,
            "negative":{
            'match': {
                'content': ' '.join([' '.join(word) for imporE,word in Importance.items() if imporE=="3"])
            }
            },
            "negative_boost":0.8,
            "negative":{
            'match': {
                'content': ' '.join([' '.join(word) for imporE,word in Importance.items() if imporE=="2"])
            }
            },
            "negative_boost":0.4,
            "negative":{
            'match': {
                'content': ' '.join([' '.join(word) for imporE,word in Importance.items() if imporE=="1"])
            }
            },
            "negative_boost":0.2
            
            }
        }
    }


    # scroll = '5m' means keep the search context active for 5 minutes;
    # size = 100 sets the maximum number of hits per scroll
    res = es.search(index=index_name, body=query, scroll='1m', size=5000) 
    print('# hits:', res['hits']['total']['value'])
    with open(res_txt, 'w') as f:
        for hit in res['hits']['hits'][:1000]:
            #f.write(hit['_source']['id'] + '\n')
            f.write(f"{hit['_source']['id']} {hit['_score']}\n")
    return  res['hits']['total']['value']


def search(s, res_txt):
    """
    Search for a query string.
    """
    query = {
        "query": {
            'match': {
                'content': s
            }
        }
    }

    # scroll = '5m' means keep the search context active for 5 minutes;
    # size = 100 sets the maximum number of hits per scroll
    res = es.search(index=index_name, body=query, scroll='1m', size=5000)
    print('# hits:', res['hits']['total']['value'])
    with open(res_txt, 'w') as f:
        for hit in res['hits']['hits'][:1000]:
            #f.write(hit['_source']['id'] + '\n')
            f.write(f"{hit['_source']['id']} {hit['_score']}\n")
    return  res['hits']['total']['value']


if __name__ == '__main__':

    # need to start the elasticsearch serive in cmd line
    #_lucene_docs_txt = conf.exp_model_dir + './lucene_docs.txt'
    #_lucene_docs_txt = './lucene_docs.txt'
    #_query = 'increas partit size'
    #_res_txt = conf.exp_evaluation_dir + '/1.txt'
    
    #_res_txt = './1.txt'
    indexDocs(_lucene_docs_txt)
    nltk.download('stopwords')
    nltk.download('punkt')
    start = time.time()
    #indexDocs(_lucene_docs_txt)
    #search(_query, _res_txt)
    #print(time.time() - start, 's')  # 20.193s

def doQuery(query,res,id=None):
    if not id:_res_txt = f"{res}/{query}.txt"
    else: _res_txt = f"{res}/{id}.txt"
    if not os.path.exists(res):
        os.makedirs(res)
    return search(query, _res_txt)
