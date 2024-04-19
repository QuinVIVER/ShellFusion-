import conf
import sys
import re
import os
import codecs

sys.path.append(conf.offline)
sys.path.append(conf.online)
from utils import *
from w2v_trainer import train as w2v_train
from tfidf_trainer import buildIDF4docs
from query_preprocesser import preprocess


graph_path = conf.exp_graph_dir + '/task_graph.json'
w2v_input_path = conf.exp_models_dir + '/w2v.input'
idf_input_path = conf.exp_models_dir + '/tfidf.input'
lucene_docs_txt = conf.exp_models_dir + '/lucene_docs.txt'
import time
def corpusGene(graph, tfidf_input, w2v_input):
    """ 
    Build inputs for two language models and lucene.
    """
    tfidf_f = codecs.open(tfidf_input, 'w', encoding='utf-8')
    w2v_f = codecs.open(w2v_input, 'w', encoding='utf-8')
    lucene_f = codecs.open(lucene_docs_txt, 'w', encoding='utf-8')
    start = time.time()

    for taskID, task in graph.items():
        title =  preprocess(task['task'])
        if task['source'] == 'qa':
            tags = task['P-tags']
            body = task['P-body']
        else:
            tags = ''
            body = ''
        tb = title + ' ' + tags
        ttb = tb + ' ' + body
        tfidf_f.write(' '.join(ttb.split()) + '\n')
        tfidf_f.flush()
        w2v_f.write('\n'.join([title, body, '']))
        w2v_f.flush()
        lucene_f.write(taskID + ' ===> ' + ' '.join(tb.split()) + '\n')
        lucene_f.flush()

    tfidf_f.close()
    w2v_f.close()
    print(f"corpus generate time:{time.time() - start}") #122s
    lucene_f.close()
    
def trainer(idf_input_path,w2v_input_path):
    """
    Train a word embedding model,
    build a IDF vocabulary.
    """
    start = time.time()
    # TFIDF
    buildIDF4docs(idf_input_path,
        conf.exp_models_dir + '/token_idf.dump',
        conf.exp_models_dir + '/token_df.dump','','')
    # w2v
    w2v_train(w2v_input_path, '', conf.exp_models_dir + '/w2v.kv')
    print(f"model generate time:{time.time() - start}") # 5087s
if __name__ == '__main__':
    corpusGene(readJson(graph_path),idf_input_path,w2v_input_path)
    trainer(idf_input_path,w2v_input_path)
    