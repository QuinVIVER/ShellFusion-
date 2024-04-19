import sys
import conf
import json
sys.path.append(conf.online)
from utils import *
from category_analyzer import retrieveCategory,retrieveVerb,checkIfCategory

import re
def getFirstWord(task):
    """
    Input nl_task(as str), return the first word, exclude comma or sth else.
    """
    remove_list = ["(GNU specific)","(GNU specific: top)","(Linux specific)","(Mac OSX specific)"]
    for _r in remove_list:
        task = task.split(_r)[-1]
    return re.search("([\w']+)", task).group(1)

#Q&A shell-related questions
def parseQAQuestions(qa_data_path,cate_list):
    """
    Parse QAPairs_det.json,
    obtain shell related-questions.
    """
    qa_parsed_data = {'cate':[],'none':[]}
    qa_iscategory_data = dict()
    qa_nocategory_data = dict()
    qa = readJson(qa_data_path)
    for qaid,cmd in qa.items():
        f_verb,cate,pos_list = retrieveCategory(cmd['Title'],cate_list)
        scripts = cmd['AcceptedAnswer']['Scripts']
        options = cmd['AcceptedAnswer']['Command-Options in Scripts']
        # ShellFusion Command-Options
        if len(scripts) == 0: continue # neglect question without scripts
        Cbody = cmd['AcceptedAnswer']["C-Body"]
        Ptags = cmd['P-Tags']
        task = {'id':qaid,'task':cmd['Title'],'P-task':cmd['P-Title'],'script':scripts,'option':options,'pos_list':pos_list,'F_verb':f_verb,
                'P-body':Cbody,'P-tags':Ptags}
        if cate[:4] != 'None':
            if cate not in qa_iscategory_data.keys():
                qa_iscategory_data[cate] = list()
            qa_iscategory_data[cate].append(task)
        else:
            if f_verb not in qa_nocategory_data.keys():
                qa_nocategory_data[f_verb] = list()
            qa_nocategory_data[f_verb].append(task)
    qa_parsed_data = {'cate':qa_iscategory_data,'none':qa_nocategory_data}
    return qa_parsed_data
#NL2Bash task-script pairs
def parseNL2BashTaskScriptPairs(nl2bash_path,cate_list):

    """
    Parse NL2Bash dataset,
    obtain task-script pairs.
    """
    nl_path = nl2bash_path + '/all.nl'
    bash_path = nl2bash_path + '/all.cm'
    nl_task_script_dict = dict()
    nl_list = list()
    bash_list = list()
    with open(nl_path,'r') as f:
        nl_list = f.readlines()
    with open(bash_path,'r') as f:
        bash_list = f.readlines()
    for i in range(len(nl_list)):
        if nl_list[i] not in nl_task_script_dict.keys():
            nl_task_script_dict[nl_list[i]] = list()
        nl_task_script_dict[nl_list[i]].append(bash_list[i])
    
    nl2bash_nocategory_dict = dict()
    nl2bash_iscategory_dict = dict()
    for nl_task,script_list in nl_task_script_dict.items():
        verb_list = retrieveVerb(nl_task)
        if len(verb_list) == 0:
        # If no verb is detected, choose the first verb of the task as its f_verb,
        # as most of the tasks in NL2bash are imperative sentence.
            f_verb = lemmatization(getFirstWord(nl_task))
            _verb,cate,pos_list = retrieveCategory(f_verb,cate_list)
        else:
            f_verb,cate,pos_list = retrieveCategory(nl_task,cate_list)
        
        if cate.split("_")[0] == "None": isCate=False
        else: isCate = True

        if isCate:
            if cate not in nl2bash_iscategory_dict.keys():
                nl2bash_iscategory_dict[cate] = list()
            nl2bash_iscategory_dict[cate].append({"task":nl_task,'F_verb':f_verb,'script':script_list,'pos_list':pos_list})
        else:
            if f_verb not in nl2bash_nocategory_dict.keys():
                nl2bash_nocategory_dict[f_verb] = list()
            nl2bash_nocategory_dict[f_verb].append({'task':nl_task,'F_verb':f_verb,'script':script_list,'pos_list':pos_list})
    
    nl2bash_parsed_data = {'cate':nl2bash_iscategory_dict,'none':nl2bash_nocategory_dict}
    return nl2bash_parsed_data

#TLDR task-script pairs
def parseTLDRTaskScriptPairs(tldr_path,cate_list):
    """
    Parse TLDR dataset,
    obtain task-script pairs.
    """
    origin_tldr_data = readJson(tldr_path)
    tldr_data = dict()
    # some script share the same task
    for cmd,cmd_data in origin_tldr_data.items():
        for t,s in cmd_data['Task-Script'].items():
            if t not in tldr_data.keys():
                tldr_data[t] = list()
            tldr_data[t].append(s)
    #tldr_data = {t:s for cmd in tldr_data.values() for t,s in cmd['Task-Script'].items()}
    tldr_nocategory_dict = dict()
    tldr_iscategory_dict = dict()
    tldr_parsed_data = dict()

    for tldr_task,scripts in tldr_data.items():
        verb_list = retrieveVerb(tldr_task)
        if len(verb_list) == 0:
        # If no verb is detected, choose the first verb of the task as its f_verb,
        # as most of the tasks in TLDR are imperative sentence. 
            f_verb = lemmatization(getFirstWord(tldr_task))
            _verb,cate,pos_list = retrieveCategory(f_verb,cate_list)
        else:
            f_verb,cate,pos_list = retrieveCategory(tldr_task,cate_list)
        if cate.split("_")[0] == "None": isCate=False
        else: isCate = True
        task_dict = {'task':tldr_task,'F_verb':f_verb,'script':scripts,'pos_list':pos_list}
        if isCate:
            if cate not in tldr_iscategory_dict.keys():
                tldr_iscategory_dict[cate] = list()
            tldr_iscategory_dict[cate].append(task_dict)
        else:
            if f_verb not in tldr_nocategory_dict.keys():
                tldr_nocategory_dict[f_verb] = list()
            tldr_nocategory_dict[f_verb].append(task_dict)
    tldr_parsed_data = {'cate':tldr_iscategory_dict,'none':tldr_nocategory_dict}
    return tldr_parsed_data


def main():
    """
    Parse Q&A posts, TLDR tutorials and NL2Bash dataset
    to obtain shell-related questions and task-script pairs.
    """
    import time
    start = time.time()
    qa_data_path = conf.exp_posts_dir + '/QAPairs_det.json'
    tldr_data_path = conf.exp_tldr_dir + '/linux_tldrcmds.json'
    nl2bash_data_path = conf.exp_nl2bash_dir 
    cate_list = readTxt(conf.exp_cate_dir + '/funcverbnet_categories.txt')

    start = time.time()
    nl2bash_parsed_data = parseNL2BashTaskScriptPairs(nl2bash_data_path,cate_list)
    nl2bash_parsed_path = conf.exp_tasks_dir + '/NL2BashParsed_task-script_pairs.json'
    dumpJson(nl2bash_parsed_data,nl2bash_parsed_path)
    print(f"nl2bash parsed time:{time.time() - start}") # 249s

    qa_parsed_data = parseQAQuestions(qa_data_path,cate_list)
    qa_parsed_path = conf.exp_tasks_dir + '/QAParsed_shell_questions.json'
    dumpJson(qa_parsed_data,qa_parsed_path)
    print(f"qaparsed time:{time.time() - start}") # 5909s
    start = time.time()
    tldr_parsed_path = conf.exp_tasks_dir + '/TLDRParsed_task-script_pairs.json'
    tldr_parsed_data = parseTLDRTaskScriptPairs(tldr_data_path,cate_list)
    dumpJson(tldr_parsed_data,tldr_parsed_path)
    print(f"tldrparsed time:{time.time() - start}") # 154s

    

if __name__ == "__main__":
    main()