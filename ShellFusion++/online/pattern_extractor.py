import conf
import sys
sys.path.append(conf.offline)
from utils import _spacy
import re
import json

pattern_path = conf.exp_pattern_dir + '/pattern_list.json'

prep_list = ['for', 'over', 'without', 'if', 'inside', 'while', 'off', 'that', 'during', 'outside', 'with', 'and', 'below', 'under', 'via', 'onto', 'as', 'in', 'back', 'using', 'against', 'alongside', 'upto', 'when', 'up', 'to', 'including', 'beyond', 'into', 'until', 'across', 'through', 'whilst', 'of', 'out', 'since', 'within', 'on', 'from', 'after', 'then', 'check', 'at', 'down', 'except', 'about', 'by', 'between', 'before']

clause_introducer_list = ['for', 'whichever', 'why', 'those', 'whom', 'unless', 'whoever', 'what', 'if', 'whose', 'while', 'which', 'who', 'that', 'whether', 'even', 'when', 'whomever', 'where']

def patternSimilarityCalculator(query_pattern, candidate_pattern):
    '''
    query_pattern:list, 由extractor提取出的pattern，又称ground truth pattern.
    candidate_pattern:list, 从pattern_list.json中读取出的pattern.
    '''
    
    j = 0 # 指向query_pattern的指针
    k = 0 # 指向上一次成功匹配位置的指针
    cnt = 0
    for i in range(len(candidate_pattern)):
        j = k # 从上一次成功匹配的位置，开始寻找query_pattern下一个与之匹配的token
        while j < len(query_pattern) and candidate_pattern[i] != query_pattern[j]:
            j += 1 # 一直递增到query_pattern中的token与candidate_pattern中的token相同
        if j < len(query_pattern) and candidate_pattern[i] == query_pattern[j]:
            k = j # 更新k
            cnt += 1 # 匹配成功，cnt加1
    similarity = cnt/max(len(query_pattern),len(candidate_pattern))
    # 返回两个pattern的相似度 分母为两个pattern中较长的那个的长度
    # latex公式代码：\text{cnt} =  {\textstyle \sum_{i=0}^{len(candidate\_pattern)-1}} \begin{cases} 1, & \text{if } \text{candidate_pattern}[i] \text{ matches an element in } \text{query\_pattern} \\ 0, & \text{otherwise} \end{cases}
    # latex公式代码：\text{similarity} = \frac{\text{cnt}}{\text{max}(\text{len(query\_pattern)},\text{len(candidate\_pattern)})}
    return similarity


def readFullPatternJson(file_path):
    # 获取pattern_list.json中的所有pattern
    qa_data_list = []
    noqa_data_list = []
    with open(file_path, 'r',encoding='utf-8') as f:
        data = json.load(f)
        if 'qa' in data:
            for item in data['qa']:
                qa_data_list.append(item)
        if 'noqa' in data:
            for item in data['noqa']:
                noqa_data_list.append(item)
    return qa_data_list, noqa_data_list

def get_V(token_list, doc):
    for i, token in enumerate(doc):
        if token.pos_ == "VERB":
            if token_list[i][-1] == -1:
                token_list[i][-1] = 'V'
            else:
                token_list[i].append('V')
    return token_list


def get_S_INF(token_list, doc):
    for i, token in enumerate(doc):
        if i < len(doc) - 1:
            if doc[i + 1].pos_ == "VERB" and token.dep_ in ["aux", "auxpass"]:
                if token_list[i][-1] == -1:
                    token_list[i][-1] = 'S_INF'
                else:
                    token_list[i].append('S_INF')
                if token_list[i + 1][-1] == -1:
                    token_list[i + 1][-1] = 'S_INF'
                else:
                    token_list[i + 1].append('S_INF')
    return token_list


def get_prep(token_list, doc, prep_list):
    for i, token in enumerate(doc):
        if i < len(doc) - 1:
            #if token.pos_ == "ADP" or str(token) in prep_list:
            if str(token) in prep_list:
                if token_list[i][-1] == -1:
                    token_list[i][-1] = str(token)
                else:
                    token_list[i].append(str(token))
    for token in doc:
        if token.pos_ == "ADP":
            prepositional_phrase = ""
            for child in token.children:
                if child.dep_ in ["pobj", "dobj"]:
                    if token_list[child.i][-1] == -1:
                        token_list[child.i][-1] = 'NP'
                    else:
                        token_list[child.i].append('NP')
    return token_list


def get_NP(token_list, doc):
    noun_chunks = list(doc.noun_chunks)
    for chunk in noun_chunks:
        start = chunk.start
        end = chunk.end
        for i in range(start, end):
            if token_list[i][-1] == -1:
                token_list[i][-1] = 'NP'
            else:
                token_list[i].append('NP')
    return token_list


def get_cla_intro(token_list, doc, clause_introducer_list):
    cla_list = []
    for i, token in enumerate(doc):
        
        #if token.dep_ in ["mark", "advmod"] or str(token) in clause_introducer_list:
         if str(token) in clause_introducer_list:
            cla_list.append(i)
            if token_list[i][-1] == -1:
                token_list[i][-1] = str(token)
            else:
                token_list[i].append(str(token))
    while len(cla_list) > 0:
        for i in range(cla_list[-1], len(token_list)):
            if token_list[i][-1] == -1:
                token_list[i][-1] = 'S'
            else:
                token_list[i].append('S')
        cla_list.pop()
    return token_list


def get_S_ING(token_list, doc):
    for i, token in enumerate(doc):
        if len(str(token)) >= 4:
            if token.head.pos_ == "VERB" and token.pos_ == "VERB" and str(token)[-3:] == 'ing':
                if token_list[i][-1] == -1:
                    token_list[i][-1] = 'S_ING'
                else:
                    token_list[i].append('S_ING')
    return token_list

def patternExtractor(sentence, F_verb,pat=None):
    #### 获取含有语法成分的token_list ####
    sentence = re.sub(r'[^\w\s]', '', sentence)
    doc = _spacy(sentence)
    F_verb_id = -1
    for token in doc:
        if str(token.lemma_) == F_verb.lower():
            F_verb_id = token.i
            break
    token_list = []
    new_sen = ' '.join(sentence.split()[F_verb_id:]) # 从F_verb开始的句子切片
    doc = _spacy(new_sen) # 重新分词
    for token in doc:
        token_list.append([token, -1]) # -1代表该token没有被标记/找不到对应占位符
    F_verb_id = 0
    token_list = get_V(token_list, doc)
    token_list = get_S_INF(token_list, doc)
    token_list = get_S_ING(token_list, doc)
    token_list = get_prep(token_list, doc, prep_list)
    token_list = get_NP(token_list, doc)
    token_list = get_cla_intro(token_list, doc, clause_introducer_list)

    # 例输出：token_list=[[create, 'V'], [a, 'NP'], [single, 'NP'], [pdf, 'NP'], [from, 'from'], [multiple, 'NP'], [text, 'NP'], [images, 'NP', 'NP'], [or, -1], [pdf, 'NP'], [files, 'NP']]
    
    #### 对token_list进行去重和处理，获取句型模式 ####

    pat_list = []
    labels = token_list[F_verb_id:]
    for i, label in enumerate(labels):
        label[0] = str(label[0])
        # print(label)
        label = [i for i in label if i != -1]
        if i == 0:
            pat_list.append('V')
            continue
        elif len(label) == 2 and label[-1] == 'V':
            label.remove('V')
            pat_list.append(label[-1]) 
            continue
        elif len(label) == 2:
            pat_list.append(label[-1]) # 将此token的标记加入pat_list
            continue
        else: # len(label) > 2 在token_list中的该token先前被标记为多个占位符 进行从句，不定式等判断
            for k in label:
                if k in clause_introducer_list:
                    pat_list.append(k)
                    break # 如果此token的标记是clause leader，将此token的标记加入pat_list，并且将之后标记为从句引领词，跳出该循环
            if 'S' in label:
                pat_list.append('S') # 从句 加入pat_list后跳出循环 结束句型模式提取
                break

            if 'to' in label and 'S_INF' in label:
                label.remove('to')
                pat_list.append('S_INF')
                continue # to be 不定式
            flag = False
            for k in label:
                if k in prep_list or k in clause_introducer_list:
                    flag = True
                    pat_list.append(k)
                    break # 如果此token的标记是介词/clause leader，将此token的标记加入pat_list，并且将之后标记为从句引领词，跳出该循环
            if flag:
                continue # 如果识别到介词/clause leader，跳过后续的判断
            if len(label) == 1: # 无标记的token默认为NP
                pat_list.append('NP')
                continue
            cnt = 1
            while len(label) > 1 and cnt > 0:
                for j, k in enumerate(label): # 对剩余的标记进行判断 j:token在label中的位置 k:token的标记
                    if j > 0 and len(label) > 2 and k not in prep_list and k not in clause_introducer_list and k not in ['NP',
                                                                                                                'S_ING',
                                                                                                                'S_INF']:
                        label.remove(k) # 删除成分标记
                cnt -= 1
            if len(label) > 1:
                pat_list.append(label[-1]) 
                continue
    pat_pred = []
    for item in pat_list:
        if len(pat_pred) == 0 or item != pat_pred[-1]:
            pat_pred.append(item)

    # 例输出：pat_pred = ['V', 'NP', 'from', 'NP']
    return ' '.join(pat_pred)

def retrieveTaskPattern(task,f_verb,is_QA):
    # 生成图谱时用的接口 用于生成task的句型模式
    # 根据来源设置retrievePattern函数的is_QA参数
    return retrievePattern(task,f_verb,is_QA)

def retrieveQueryPattern(query,f_verb):
    # 为查询提取句型模式时用的接口
    # 将 retrievePattern函数的is_QA参数和is_online参数均设置为True
    return retrievePattern(query,f_verb,True,True)

def retrievePattern(query,f_verb,is_QA=True,is_online=False):
    # is_QA: True 如果输入的query是Q&A shell related question，否则为False
    # is_online: True 如果是在推荐流程中使用，否则为False
    qa_pat_list, noqa_pat_list = readFullPatternJson(pattern_path)
    pat = ''
    pat_pred = patternExtractor(query,f_verb,pat) # 获取query的句型模式，即ground truth pattern
    candi_pats = []
    if is_online:qa_pat_list = list(set(qa_pat_list) | set(noqa_pat_list));is_QA=True
    if is_QA:
        for qa_pat in qa_pat_list:
            # 在所有的pattern中寻找一个与ground truth pattern最相似的pattern
            candiPList = set(qa_pat.split()) & set(prep_list)
            predPList = set(pat_pred.split()) & set(prep_list)
            queryPList = set(query.split()) & set(prep_list)
            if (len(candiPList - queryPList) + len(candiPList - predPList)) > 0:
                # 如果备选pattern中存在query中没有的prep，跳过
                continue
            
            candiCLAList = set(qa_pat.split()) & set(clause_introducer_list)
            claLList = set(pat_pred.split()) & set(clause_introducer_list)
            queryCLAList = set(query.split()) & set(clause_introducer_list)
            if (len(candiCLAList - queryCLAList)) > 0:
                # 如果备选pattern中存在query中没有的clause leader，跳过
                continue 
            
            _sim = patternSimilarityCalculator(qa_pat.split(),pat_pred.split())
            candi_pats.append((qa_pat,_sim))
        if len(candi_pats) == 0:
            return 'V NP'
        _pat = list(sorted(candi_pats,key=lambda x:x[1],reverse=True))[0][0]
        
        return _pat
    else:
        for noqa_pat in noqa_pat_list:
             
            candiPList = set(noqa_pat.split()) & set(prep_list)
            predPList = set(pat_pred.split()) & set(prep_list)
            queryPList = set(query.split()) & set(prep_list)
            if (len(candiPList - queryPList) + len(candiPList - predPList)) > 0:
                # 如果备选pattern中存在query中没有的prep，跳过
                continue
                    
            candiCLAList = set(noqa_pat.split()) & set(clause_introducer_list)
            claLList = set(pat_pred.split()) & set(clause_introducer_list)
            queryCLAList = set(query.split()) & set(clause_introducer_list)
            
            if (len(candiCLAList - queryCLAList)) > 0:
                # 如果备选pattern中存在query中没有的clause leader，跳过
                continue
            
            _sim = patternSimilarityCalculator(noqa_pat.split(),pat_pred.split())
            candi_pats.append((noqa_pat,_sim))
        if len(candi_pats) == 0:
            return 'V NP'
        _pat = list(sorted(candi_pats,key=lambda x:x[1],reverse=True))[0][0]
        return _pat

if __name__ == "__main__":
    # 测试patternExtractor
    sentence = "create a single pdf from multiple text, images or pdf files"
    F_verb = "create"
    pat = retrievePattern(sentence,F_verb,True,True)
    print(pat)
    # 输出：V NP from NP
    # 测试patternSimilarityCalculator
    query_pattern = ['V', 'NP', 'from', 'NP']
    candidate_pattern = ['V', 'NP', 'on', 'NP']    
    sim = patternSimilarityCalculator(query_pattern, candidate_pattern)
    print(sim)
    # 输出：0.75

