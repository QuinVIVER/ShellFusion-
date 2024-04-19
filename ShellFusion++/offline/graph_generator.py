import conf
import sys
import numpy as np
import copy
sys.path.append(conf.offline)
sys.path.append(conf.online)
from utils import *
from post_parser import detectCmdsOpsInGraphScript
from category_analyzer import *
from pattern_extractor import retrieveTaskPattern


mpcmd = conf.exp_manual_dir + '/mpcmd_info.json'


import re
# nl\tl counter
nl2bash_num = 0
tldr_num = 0


cmd_info_dict, cmd_mid_desc_dict = readCmdInfo(mpcmd)

def graph_generate():
    """
    Generate knowledge graph.
    """
    import time
    start = time.time()
    global nl2bash_num,tldr_num
    qa_parsed_path = conf.exp_tasks_dir + '/QAParsed_shell_questions.json'
    tldr_parsed_path = conf.exp_tasks_dir + '/TLDRParsed_task-script_pairs.json'
    nl2bash_parsed_path = conf.exp_tasks_dir + '/NL2BashParsed_task-script_pairs.json'
    with open(conf.category_dir ,'r',encoding='utf-8') as f:
        cate_list = [c.replace('\n','').replace('\xa0','') for c in f.readlines()]
    qa_count = 0
    dataDict = {'qa':readJson(qa_parsed_path),'tl':readJson(tldr_parsed_path),'nl':readJson(nl2bash_parsed_path)}
    task_data = dataDict['qa']
    qa_data = [task for tasks in {**task_data['cate'],**task_data['none']}.values() for task in tasks]
    for task in qa_data:
        if len(task['script']) == 0:continue
        else :qa_count += 1
    print(qa_count)

    midGraph = {c:[] for c in cate_list}
    midGraph['None'] = []
    for source,task_data in dataDict.items():            
        full_tasks = [task for tasks in {**task_data['cate'],**task_data['none']}.values() for task in tasks]
        for task in full_tasks:
            task['task'] = task['task'].replace('\n','')
            if len(task['script']) == 0:continue
            is_QA = True
            # split multiple task
            task_divided_list = re.split(' and | or ',task['task'])    
            #midGraph = subTask(task_divided_list,task,source,midGraph,cate_list)
            for task_divided in task_divided_list:
                _task = copy.deepcopy(task)
                if task_divided == "": continue
                script_dict = dict()
                
                if source == 'qa':
                    f_verb, cate, pos_list = retrieveCategory(task_divided,cate_list)
                    if cate[:4] == 'None': cate = 'None'
                    _task.pop('P-body')
                    _task.pop('P-tags')
                    
                    for script_num,script in _task['script'].items():
                        script = script[2:]
                        biker_cmd,cmd_ops_dict = detectCmdsOpsInGraphScript(script,cmd_info_dict)
                        result_cmd_op_desc = generateOpsDes(cmd_ops_dict,cmd_info_dict,cmd_mid_desc_dict)
                        result_cmd_tldr_dict = generateCmdTLDR(cmd_ops_dict,cmd_mid_desc_dict)
                        script_dict[script_num] = {
                            'script':script,
                            'command-options': result_cmd_op_desc,
                            'TLDR_inform':result_cmd_tldr_dict
                        }
                    qa_count += 1
                else:
                    is_QA = False
                    script_num = 0
                    f_verb, cate, pos_list = retrieveCategory(task_divided,cate_list)
                    if cate[:4] == 'None': cate = 'None'
                    for script in _task['script']:
                        biker_cmd,cmd_ops_dict = detectCmdsOpsInGraphScript(script,cmd_info_dict)
                        result_cmd_op_desc = generateOpsDes(cmd_ops_dict,cmd_info_dict,cmd_mid_desc_dict)
                        result_cmd_tldr_dict = generateCmdTLDR(cmd_ops_dict,cmd_mid_desc_dict)
                        script_dict[script_num] = {'script':script,
                            'command-options':result_cmd_op_desc,
                            'TLDR_inform':result_cmd_tldr_dict
                        }
                        script_num += 1
                if source == 'nl':
                    _task['id'] = f"nl2bash_{nl2bash_num}"
                    nl2bash_num += 1
                elif source == 'tl':
                    _task['id'] = f"tldr_{tldr_num}"
                    tldr_num += 1
                _task['script'] = script_dict
                _task['F_verb'] = f_verb
                #_task['pos_list'] = pos_list 
                _task['source'] = source
                _task['pattern'] = retrieveTaskPattern(task_divided,f_verb,is_QA)
                _task['cate'] = cate
                _task.pop('pos_list')
                midGraph[cate].append(_task)

    graph_dir = conf.exp_graph_dir + "/task_graph.json"
    graph = {t['id']:t for ts in midGraph.values() for t in ts}
    print(f"graph time{time.time() - start}")
    print(f"QA count: {qa_count}") #516322
    dumpJson(graph,graph_dir) # 18180.3s 



if __name__ == "__main__":
    graph_generate()