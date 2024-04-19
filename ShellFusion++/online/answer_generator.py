import conf
import sys
import re
import os


sys.path.append(conf.online)
sys.path.append(conf.offline)
from utils import *
from query_preprocesser import preprocess
from similarity import transformDoc, docSySim
from w2v_trainer import loadKV
from mp_analyzer import rankDocsBySimilarityToTarget
from SimQ_retriever import readTransformLuceneDocs,retrieveTopn
from ES import doQuery

mpcmd = conf.exp_manual_dir + '/mpcmd_info.json'

import math
import cmath
cmd_info_dict, cmd_mid_desc_dict = readCmdInfo(mpcmd)
check_list = ['the','of','a','an','-',':']

def answerGenerator(queries_dict, graph, check_list, embed_topn_dir, cmd_mid_desc_dict, kv, idf, k, res_dir):
    """
    extract, rerank and generate full answer for each top-k command.
    """
    queries_dict = {v:k for k,v in queries_dict.items()}
    if not os.path.exists(res_dir):
        os.makedirs(res_dir)
    query_id = 0
    for name in os.listdir(embed_topn_dir):
        if name[-3:] != 'txt': continue
        if name == ".txt":continue
        query = queries_dict[name[:-4]]
        p_query = preprocess(query)
        qid_sim_dict, cmd_qids_dict, cmd_desc_dict,qid_ops_dict = {},{},{},{}
        cmd_tldr_dict, mid_tldr_dict = {},{}
        #start = time.time()
        topn_q = readTxt(embed_topn_dir + '/' + name)
        nl_q = topn_q[0].split(' ===> ')
        nl_q = {'task':nl_q[1],'script':graph[nl_q[0].replace('nl_','nl2bash_')]['script']} if len(nl_q) == 3 else {'task':'None','script':'None'}
        topn_q = topn_q[1:]
        for line in topn_q:
            sa = line.split(' ===> ')
            if len(sa) == 3:
                qid = sa[0]
                if qid in graph.keys():
                    qid_sim_dict[qid] = float(sa[2].strip())
                    accans = graph[qid]['script']
                    candi_cmdOps = dict()
                    for num,cmdDict in accans.items():
                        for cmd, opsDict in cmdDict['command-options'].items():
                            if cmd not in cmd_mid_desc_dict or cmd in check_list:
                                continue
                            for mid, TLDRdes in cmdDict['TLDR_inform'][cmd].items():
                                mid_tldr_dict[mid] = TLDRdes
                            cmd_desc_dict[cmd] = opsDict['mpsum']
                            qid_ops_dict[qid] = {cmd:{ops:des for ops,des in opsDict.items() if ops != 'mpsum'}}
                            if cmd not in cmd_qids_dict:
                                cmd_qids_dict[cmd] = set()
                            cmd_qids_dict[cmd].add(qid)
        """ Measure the similarities between detected commands and the query """
        cmd_sim_dict = rankDocsBySimilarityToTarget(cmd_desc_dict, p_query, kv, idf, False)
        tldr_mid_sim_dict = rankDocsBySimilarityToTarget(mid_tldr_dict, p_query, kv, idf, False)
        cmd_tldr_dict = {mid[mid.find('_')+1:mid.rfind('_')]:0 for mid in tldr_mid_sim_dict.keys()}
        cmd_sim_dict1 = {x:0 for x in cmd_sim_dict.keys()}
        for mid, sim in tldr_mid_sim_dict.items():
            cmdname = mid[mid.find('_')+1:mid.rfind('_')]
            if sim > cmd_tldr_dict[cmdname]:
                cmd_tldr_dict[cmdname] = sim
        for cmd in cmd_tldr_dict.keys():
            if cmd in cmd_sim_dict.keys():
                cmd_sim_dict1[cmd] = 0.5 * cmd_tldr_dict[cmd] + 0.5 * cmd_sim_dict[cmd] 
            else:
                cmd_sim_dict1[cmd] = cmd_tldr_dict[cmd]

        """ Filter irrelevant commands and rank the retained top-k commands """
        cmd_likelihood_dict = dict()
        for item in sorted(cmd_sim_dict1.items(), key=lambda x:x[1], reverse=True):
            cmd,simdoc = item[0],item[1]
            if cmd not in cmd_likelihood_dict:
                simso = sum([ qid_sim_dict[qid] for qid in cmd_qids_dict[cmd] ]) / len(cmd_qids_dict[cmd]) * math.log2(1+len(cmd_qids_dict[cmd]))
                simso = min(simso, 1.0)
                cmd_likelihood_dict[cmd] = 2 * simso * simdoc / (simso + simdoc) \
                    if simso + simdoc > 0.0 else 0.0
                if len(cmd_likelihood_dict) == k:
                    break
        # generate answer for each candidate cmd
        generated_answers = []  # generated answer for each candidate cmd
        """ Most Similar NL2Bash Task-Script Pair """

        sorted_qids = [ item[0] for item in sorted(qid_sim_dict.items(), key=lambda x:x[1], reverse=True) ]
        """ 1. MP Summary """
        for item in sorted(cmd_likelihood_dict.items(), key=lambda x:x[1], reverse=True)[:k]:
            cmd = item[0]
            mpsumm = cmd_desc_dict[cmd]
            """ 2.1 Top-3 Similar Questions with Accepted Scripts """
            top3_qtitles, top3_scripts, top3_ops, top3_abodies = [], [], set(), []
            op_desc_dict = {}
            for qid in sorted_qids:
                if qid in cmd_qids_dict[cmd]:
                    if len(top3_qtitles) < 3:
                        top3_qtitles.append(qid + ': ' + graph[qid]['task'])
                    if len(top3_scripts) < 3:
                        accans = graph[qid]['script']
                        scripts = []
                        ops = set()
                        ind_scriptcmdops_dict = sorted(accans.items(), key=lambda x:int(x[0]))
                        for _item in ind_scriptcmdops_dict :
                            script, cmd_ops_dict = _item[1]['script'], _item[1]['command-options']
                            if cmd != script  and cmd in cmd_ops_dict and len(script.split('\n')) <= 10:
                                scripts.append(script)
                                ops = set([x for x in cmd_ops_dict[cmd].keys() if cmd in cmd_ops_dict and x != 'mpsum'])
                                for op in ops:
                                    if op not in op_desc_dict.keys():
                                        op_desc_dict[op] = cmd_ops_dict[cmd][op] 
                        scripts = '\n\n'.join(scripts).replace('&amp;', '&').replace('&gt;', '>').\
                            replace('&lt;', '<').replace('&quot;', '"').replace('&nbsp;', ' ').strip('\n ')      
         
                        if scripts != '':
                            top3_scripts.append(qid + ': ' + scripts)
                            # if qid[:2] == 'qa': top3_abodies.append(graph[qid]['C-Body'])
                            top3_ops |= ops
                        else: top3_scripts.append(qid+ ': ')
            """ 2.2、Most Similar TLDR Task-Script Pair"""
            mostsim_task, mostsim_script, tldr_ops = '', '', set()
            if cmd in cmd_info_dict.keys():
                for midDict in cmd_info_dict[cmd].values():
                    if 'TLDR Task-Script' in midDict:
                        task_script_dict, id_task_dict = midDict['TLDR Task-Script'], {}
                        for i, task in enumerate(task_script_dict.keys()):
                            id_task_dict[i] = task
                        id_sim_dict = rankDocsBySimilarityToTarget(id_task_dict, p_query, kv, idf, True)
                        mostsim_id = sorted(id_sim_dict.items(), key=lambda x:x[1], reverse=True)[0][0]
                        mostsim_task = id_task_dict[mostsim_id]
                        mostsim_script = task_script_dict[mostsim_task]
                        tldr_ops = detectOpsInTLDRScript(mostsim_script)
            
            """ 3. Explanations about Options """
            op_cdesc_dict = {}
            for abody in top3_abodies:
                for sen in re.split('\. +[a-zA-Z]', abody):
                    if not abody.startswith(sen):
                        sen = abody[abody.find(sen)-1] + sen
                    sen = sen.rstrip('. ')
                    if sen != '' and not sen.endswith(':'):
                        matched_ops = set(sen.split()).intersection(top3_ops)
                        if len(matched_ops) > 0:
                            op = sorted(matched_ops)[0]
                            if op not in op_cdesc_dict:
                                op_cdesc_dict[op] = set()
                            op_cdesc_dict[op].add(sen + '.')
            has_manual = False
            has_explan = False
            top3_op_desc_dict = {}
            for op in top3_ops:
                if op in op_desc_dict.keys():
                    top3_op_desc_dict[op] = op_desc_dict[op]
                    has_manual = True
                    has_explan = True
                if op in op_cdesc_dict and not has_manual:
                    top3_op_desc_dict[op + '(C)'] = ' '.join(op_cdesc_dict[op])
                    top3_op_desc_dict[op] = ' '.join(op_cdesc_dict[op])
                    has_explan = True
            if not has_explan:
                top3_op_desc_dict = {}
            if len(top3_qtitles) != len(top3_scripts):
                all_id = {x.split(":")[0]+": " for x in top3_qtitles}
                part_id = {x.split(":")[0]+": " for x in top3_scripts}
                not_present_scripts = all_id - part_id
                top3_scripts += list(not_present_scripts)
            generated_answers.append({
                'Command': cmd, 'MP Summary': mpsumm,
                'Most Similar TLDR Task': mostsim_task, 'Most Similar TLDR Script': mostsim_script,
                'Most Similar NL2Bash Task': nl_q['task'], 'Most Similar NL2Bash Script': nl_q['script'],
                'Top-3 Similar Questions': top3_qtitles, 'Top-3 Scripts': top3_scripts,
                'Explanations about Options': top3_op_desc_dict
            })
        result_json = { 'Query': query, 'Answers': generated_answers }
        query_id += 1
        dumpJson(result_json,f"{res_dir}/{name.replace('.txt','')}.json")

    

    
if __name__ == '__main__':
    graph_path = conf.exp_graph_dir + '/task_graph.json'
    lucene_doc = conf.exp_models_dir + '/lucene_docs.txt'
    lucene_topN_dir = conf.exp_evaluation_dir + '/elasticsearch_topN/'
    embed_topn_dir = conf.exp_evaluation_dir + '/topn/'
    kv_path = conf. exp_models_dir + '/w2v.kv'
    idf_path = conf.exp_models_dir + '/token_idf.dump' 
    queries_list = conf.exp_evaluation_dir + '/candidate_queries.txt' # 从query_txt中读取query 测试时可以修改此处指向的文件
    graph = readJson(graph_path)
    
    #query = 'Create a single pdf from multiple text, images or pdf files'
    queries = [x.split(' ===> ')[1] for x in readTxt(queries_list)] # 从query_txt中读取query
    queries_dict = {x.split(' ===> ')[1]:x.split(' ===> ')[0] for x in readTxt(queries_list)}
    #queries = [query] 
    _kv = loadKV(kv_path)
    _idf = load(idf_path)
    qid_doc_dict = readTransformLuceneDocs(lucene_doc, _kv, _idf)
    with open(conf.category_dir ,'r') as f:
        # 获取类别列表
        cate_list = [c.replace('\n','').replace('\xa0','') for c in f.readlines()]
        

    for query in queries:
        Pquery = preprocess(query) # stemming, stopword removal
        doQuery(Pquery,lucene_topN_dir,queries_dict[query]) # ES查询，生成top-N文件
        retrieveTopn(query, graph, cate_list, lucene_topN_dir, qid_doc_dict, _kv, _idf, embed_topn_dir,queries_dict[query]) # 生成top-n文件
    answerGenerator(queries_dict, graph, check_list, embed_topn_dir, cmd_mid_desc_dict, _kv,_idf, 50, conf.exp_evaluation_dir + '/answers') # 生成答案
        