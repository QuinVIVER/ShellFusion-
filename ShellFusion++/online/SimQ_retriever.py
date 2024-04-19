import os
import time
import sys
import conf
sys.path.append(conf.offline)
sys.path.append(conf.online)

from w2v_trainer import *
from conf import conf
from utils import readTxt, load
from similarity import transformDoc, docSySim
from query_preprocesser import preprocess
from category_analyzer import retrieveCategory
from pattern_extractor import retrieveQueryPattern,patternSimilarityCalculator

def candidateTaskSimilarityCalculator(query,qid_pat_dict,cate_list):
    """
    Calculate the similarity betweeen the query and each candidate Task. 
    """
    w1,w2 = 4.0,3.0;w_sum = 10.0
    f_verb,cate,pos_list = retrieveCategory(query,cate_list)
    qid_pat_points = {id:0 for id in qid_pat_dict.keys()}
    if cate[:4] != 'None':
        # category similarity
        for id in qid_pat_points.keys():
            if qid_pat_dict[id]['cate'] == cate:
                qid_pat_points[id] += float(w1/w_sum) 
            else:
                qid_pat_points[id] = 0
    # extract the pattern of the query
    query_p = retrieveQueryPattern(query,f_verb)
    for id in qid_pat_points.keys():
        candidate_pattern = [i.replace('\n','') for i in qid_pat_dict[id]['P_pat'].split()]
        pat_sim = float(w2*patternSimilarityCalculator(query_p.split(),candidate_pattern)/w_sum)
        qid_pat_points[id] += pat_sim
    qid_pat_points = dict(sorted(qid_pat_points.items(),key=lambda x:x[1],reverse=True))
    return qid_pat_points

def retrieveTopn(query, graph, cate_list, lucene_topN_dir, qid_doc_dict, kv, idf, res_dir,id=None):
    """
    Rerank the candidate docs retrieved by lucene for queries based on their sematic similarity,
    category similarity and pattern similarity.
    """  
    if not os.path.exists(res_dir):
        os.makedirs(res_dir)
    Pquery = preprocess(query)
    if not id:topN_txt = lucene_topN_dir + '/' + Pquery + '.txt'
    else:topN_txt = lucene_topN_dir + '/' + id + '.txt'
    candi_qids = set()
    topn_qids = set()
    for line in readTxt(topN_txt):
        sa = line.split()
        if len(sa) == 2:
            candi_qids.add(sa[0])
    # 挑出排序最前的nl2bash的qid
    nl2_sl = ('None','None')
    for qid in candi_qids:
        if qid[:2] == 'nl':
            nl2_sl = (qid,'nl2bash') #nl2bash的最接近问题 放在top-n文件的第一个
            break
    # 语义相似度计算
    qid_sim_dict = dict()
    qid_pat_dict = dict()
    matrix, idfv = transformDoc(Pquery,kv,idf)  
    if matrix is not None and idfv is not None:
        for qid in candi_qids:
            if qid.startswith('nl_'): nqid = qid.replace('nl_','nl2bash_')
            else :nqid=qid
            qid_sim_dict[nqid] = docSySim(matrix, qid_doc_dict[qid]['matrix'], idfv, qid_doc_dict[qid]['idf'])
            qid_pat_dict[nqid] = {'cate':graph[nqid]['cate'],'P_pat':graph[nqid]['pattern']}
    qid_pat_sim_dict = candidateTaskSimilarityCalculator(query,qid_pat_dict,cate_list)
    if qid_pat_sim_dict == 0:
        qid_pat_sim_dict = {x:0 for x in qid_pat_dict.keys()}
    qid_abs_sim_dict = dict() 
    for qid in candi_qids:
        if qid.startswith('nl_'): nqid = qid.replace('nl_','nl2bash_')
        qid_abs_sim_dict[nqid] = (qid_pat_sim_dict[nqid] + 3.0*float(qid_sim_dict[nqid]/10.0))
    sl = sorted(qid_abs_sim_dict.items(), key=lambda x:x[1], reverse=True)
    if not id: topn_path = res_dir + '/' + Pquery + '.txt'
    else: topn_path = res_dir + '/' + id + '.txt'
    with open(topn_path, 'w', encoding='utf-8') as f:
        # 写入nl2bash的qid
        if nl2_sl[0] != 'None':
            f.write(' ===> '.join([nl2_sl[0],graph[nl2_sl[0].replace('nl_','nl2bash_')]['task'] , str(nl2_sl[1])]) + '\n')
        else: 
            f.write(' ===> '.join([nl2_sl[0], str(nl2_sl[1])]) + '\n')
        for item in sl[:50]:
            topn_qids.add(item[0])
            # qid_doc_dict[item[0]]['doc']
            f.write(' ===> '.join([item[0],graph[item[0]]['task'] , str(item[1])]) + '\n')
            f.flush()


def readQueries(queries_txt):
    """
    Read queries.
    """
    queries_dict = {}
    lines = readTxt(queries_txt)
    for line in lines:
        sa = line.split(' ===> ')
        if len(sa) == 3:
            queries_dict[sa[0]] = { 'Query': sa[1], 'P-Query': sa[2] }
    return queries_dict

def readTransformLuceneDocs(lucene_docs_txt, kv, idf):
    """
    Read the docs file for lucene and transform them into matrix representation based on language models.
    """
    id_doc_dict = {}
    for line in readTxt(lucene_docs_txt):
        sa = line.split(' ===> ')
        if len(sa) == 2 or len(sa) == 3:
            _id, doc = sa[0], sa[1]
            matrix, idfv = transformDoc(doc, kv, idf)
            if matrix is not None and idfv is not None:
                id_doc_dict[_id] = { 'doc': doc, 'matrix': matrix, 'idf': idfv }
    return id_doc_dict

