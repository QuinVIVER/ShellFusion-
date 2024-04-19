import sys
import conf
sys.path.append(conf.offline)
from utils import posTagger,lemmatization,_spacy,readJson

def checkIfCategory(verb_list,cate):
    '''
    return category based on verb_list and category_list.
    '''
    res = [0] * len(verb_list)
    for category in cate:
        matched = set(verb_list) & set(category.split('/'))
        if len(matched) != 0:
            for m in list(matched):
                res[verb_list.index(m)] = ([m],category) 
    res = [r for r in res if r != 0]
    if len(res) != 0:
        iscate = True
        if len(res) != 1 and res[0][0][0] == 'do':
            # prevent choosing "do" or "be" in the first place
            verb = res[1][0][0]
            category = res[1][1]
        elif len(res) == 1 and len(res[0]) != 1 and res[0][0][0] == 'do':

            try:
                verb = res[0][0][1]
            except IndexError:
                verb = res[0][0][0]
            category = res[0][1]
        else: verb,category = res[0][0][0],res[0][1]
    else: iscate,verb,category = False,None,None
    return iscate,verb,category

def retrieveVerb(query):
    '''
    return F_verb: The first none "be" verb in the query.
    '''
    result = posTagger(query)
    verb_list = list()
    for word in result:
        if word[1][0] == "V" and word[0]!='be':
            verb_list.append(lemmatization(word[0]))
            continue
    return verb_list,result
def retrieveCategory(query,cate_list):
    '''
    Input query and cate_list,
    try to retrieve the f_verb,category and postagging_list of the query.
    '''
    verb_list,pos_list = retrieveVerb(query.lower())
    if len(verb_list) == 0: 
        # postagging没有verb，将query中的所有词作为verb进行category检索
        verb_list = [x.lemma_ for x in _spacy(query)]
        iscate,f_verb,cate = checkIfCategory(verb_list,cate_list)
        if iscate:
            return f_verb,cate,pos_list
        else:
            f_verb = 'None'
            return f_verb,'None_noVerb',pos_list
    else:
        # postagging有verb，使用query中的verb进行category检索
        iscate,f_verb,cate = checkIfCategory(verb_list,cate_list)
        if iscate:
            # match，返回类别
            return f_verb,cate,pos_list
        # 没有match的类别，将第一个verb作为F_verb返回
        verb_list = [lemmatization(x) for x in verb_list]
        verb_list = list(set(verb_list) - set(['do','be']))    
        if len(verb_list) != 0:
            f_verb = verb_list[0]
        else:f_verb = 'None'
        # 返回值：功能动词，类别（若不匹配则返回None_无类别类型，noCate为没有匹配类别，noVerb为没有识别到动词），postagging结果
        return f_verb,'None_noCate',pos_list


if __name__ == '__main__':
    with open(conf.category_dir ,'r',encoding='utf-8') as f:
        cate_list = [c.replace('\n','').replace('\xa0','') for c in f.readlines()]
    # 测试查询
    _test_query = 'create a single pdf from multiple text, images or pdf files'
    
    f_verb,_type,pos_list = retrieveCategory(_test_query,cate_list)
    # 输出
    print(f"query: {_test_query}\nf_verb: {f_verb}\nf_cate: {_type}\npos_list: {pos_list}")