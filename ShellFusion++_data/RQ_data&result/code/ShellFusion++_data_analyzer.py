"""
Analyze, calculate and output MAP,MRR metric for each RQ.
"""
from utils import *
import copy
queries_path = './queries.txt'
from decimal import Decimal

def acquireRecList(IDs,path):
    '''
    Acquire recommended command list
    from answers.
    '''
    ID_rec_cmd = dict()
    for ID in IDs:
        id_rec_list_path = f"{path}{ID}.json"
        rec_cmd_list = [x['Command'] for x in readJson(id_rec_list_path)['Answers']]
        ID_rec_cmd[ID] = rec_cmd_list
    return ID_rec_cmd

def acquireAPMetric(ID_rec_list,ID_cmd_rels,K):

    candi_rele = {ID:{_cmd:ID_cmd_rels[ID][_cmd] for _cmd in cmds} for ID,cmds in ID_rec_list.items()}
    return APAtK(candi_rele,ID_cmd_rels,K)

def acquireRRMetric(ID_rec_list,ID_cmd_rels,K):
    candi_rele = {ID:{_cmd:ID_cmd_rels[ID][_cmd] for _cmd in cmds} for ID,cmds in ID_rec_list.items()}
    return RRAtK(candi_rele,K)


def weight_analyze(ws_list):
    '''
    do RQ1.
    '''
    # w1:category similarity
    # w2:pattern
    # w3:word-embedding similarity

    ID_queries = {i.split(' ===> ')[0]:i.split(' ===> ')[1]for i in readTxt(queries_path)}
    IDs = list(ID_queries.keys())
    K_list = [1,3,5]

    new_path = './ShellFusion++_k5'
    _rels_path = new_path + '/query_cmdrels'
    _ans_path = new_path + '/answers_weight_analyze'
    cmd_rels = readJson('all_cmd_rels.json')
    AP_dict = {}
    '''
    for w_list in ws_list:
        _w = "_".join([str(i) for i in w_list])
        AP_dict[_w] = dict()
        rels_path = f"{_rels_path}_weight_analyze/{_w}"
        os.system(f"mkdir {rels_path}".replace('/','\\'))
        ans_path = f"{_ans_path}/answers{_w}/"
        w_rec_list = acquireRecList(IDs,ans_path)
        ##### Output Excel containing rel point
        for ID in IDs:
            origin_path = f"{_rels_path}/{ID}.xlsx"
            old_dict = readXlsx(origin_path)
            #old_dict = [[k] + v for k,v in old_dict.items()]
            new_dict = old_dict[:3]
            for i in range(5):
                new_cmd = w_rec_list[ID][i]
                if new_cmd not in cmd_rels[ID]:
                    print(ID)
                    print(old_dict[0][1])
                    print(new_cmd)
                    print(getSummary(new_cmd))
                    point = int(input())
                    cmd_rels[ID][new_cmd] = point
                    
                else:point = cmd_rels[ID][new_cmd]
                new_line = [w_rec_list[ID][i],point,getSummary(new_cmd)]
                new_line += old_dict[3+i][3:]
                new_dict.append(new_line)
            new_path = f"{rels_path}/{ID}.xlsx"
            new_dict = {i[0]:i[1:] for i in new_dict}
            outputXls(new_dict,new_path)
    '''
    # Recalculate SFmetric using latest rels
    SF_rec_list = acquireRecList(IDs,'./ShellFusion_k5/answers/')
    SF_AP_dict = {str(K):{} for K in K_list}
    for K in K_list:
        MAP,_AP = acquireAPMetric(SF_rec_list,cmd_rels,K)
        MRR,_RR = acquireRRMetric(SF_rec_list,cmd_rels,K)
        SF_AP_dict[str(K)] = {**{'AVG':{'MAP':MAP,'MRR':MRR}},**{ID:{'MAP':_AP[ID],'MRR':_RR[ID]} for ID in IDs}}
    dumpJson(SF_AP_dict,'./FINAL_SF_metric.json')
    for w_list in ws_list:
        _w = "_".join([str(i) for i in w_list])
        AP_dict[_w] = dict()
        ans_path = f"{_ans_path}/answers{_w}/"
        w_rec_list = acquireRecList(IDs,ans_path)
        for K in K_list:
            MAP,_AP = acquireAPMetric(w_rec_list,cmd_rels,K)
            MRR,_RR = acquireRRMetric(w_rec_list,cmd_rels,K)
            AP_dict[_w][str(K)] = {**{'AVG':{'MAP':MAP,'MRR':MRR}},**{ID:{'MAP':_AP[ID],'MRR':_RR[ID]} for ID in IDs}}
    ##### Generate Metric File
    #SF_AP_dict = readJson('./FINAL_SF_metric.json')
    sheets = ["_".join([str(i) for i in w_list]) for w_list in ws_list]
    SFAP_result_excel = {'ID':['SF AP@1','NEW AP@1',
                               'SF AP@3','NEW AP@3',
                               'SF AP@5','NEW AP@5'],'AVG':[]}
    excel_dict = list()
    for _w_list in sheets:
        excel_sheet = copy.deepcopy(SFAP_result_excel)
        path = f"{_rels_path}_weight_analyze/{_w_list}"
        for ID in IDs:
            ID_head = f'=HYPERLINK("{path}/{ID}.xlsx","{ID}")'
            data = list()
            for K in K_list:
                data.append(SF_AP_dict[str(K)][ID]['MAP'])
                data.append(AP_dict[_w_list][str(K)][ID]['MAP'])
            excel_sheet[ID_head] = data
        excel_dict.append(excel_sheet)
    outputXls_MultiSheet(excel_dict,'./0728_float_weight_APanalyze.xlsx',sheets)
    excel_dict = list()
    SFRR_result_excel = {'ID':['SF RR@1','NEW RR@1',
                               'SF RR@3','NEW RR@3',
                               'SF RR@5','NEW RR@5'],
                        'AVG':[]}
    for _w_list in sheets:
        excel_sheet = copy.deepcopy(SFRR_result_excel)
        path = f"{_rels_path}_weight_analyze/{_w_list}"
        for ID in IDs:
            ID_head = f'=HYPERLINK("{path}/{ID}.xlsx","{ID}")'
            data = list()
            for K in K_list:
                data.append(SF_AP_dict[str(K)][ID]['MRR'])
                data.append(AP_dict[_w_list][str(K)][ID]['MRR'])
            excel_sheet[ID_head] = data
        excel_dict.append(excel_sheet)
    outputXls_MultiSheet(excel_dict,'./weight_analytic.xlsx',sheets)
    dumpJson(AP_dict,'./weight_analyze_result.json')
    dumpJson(cmd_rels,'./all_cmd_rels.json')


def variant_weight_analyze():
    '''
    do RQ3.
    '''
    ID_queries = {i.split(' ===> ')[0]:i.split(' ===> ')[1]for i in readTxt(queries_path)}
    IDs = list(ID_queries.keys())
    K_list = [1,3,5]
    variants = ['ShellFusion++','ShellFusion++_QA','ShellFusion++_QA+MPs','ShellFusion++_QA+TLDR']
    cmd_rels = readJson('all_cmd_rels.json')
    AP_dict = {}
    for _v in variants:        
        _ans_path = _v + '/answers/'
        _v_rec_list = acquireRecList(IDs,_ans_path)
        # Annotate rel score for new command.
        for ID in IDs:
            for i in range(5):
                new_cmd = _v_rec_list[ID][i]
                if new_cmd not in cmd_rels[ID]:
                    print(ID)
                    print(ID_queries[ID])
                    print(new_cmd)
                    print(getSummary(new_cmd))
                    point = int(input())
                    cmd_rels[ID][new_cmd] = point    
                else: point = cmd_rels[ID][new_cmd]

    # Re-calculate MAP,MRR metric.
    SF_rec_list = acquireRecList(IDs,'./ShellFusion/answers/')
    SF_AP_dict = {str(K):{} for K in K_list}
    for K in K_list:
        MAP,_AP = acquireAPMetric(SF_rec_list,cmd_rels,K)
        MRR,_RR = acquireRRMetric(SF_rec_list,cmd_rels,K)
        SF_AP_dict[str(K)] = {**{'AVG':{'MAP':MAP,'MRR':MRR}},**{ID:{'MAP':_AP[ID],'MRR':_RR[ID]} for ID in IDs}}
    dumpJson(SF_AP_dict,'./FINAL_SF_metric.json')
    for _v in variants:
        AP_dict[_v] = dict()
        ans_path = f"{_v}/answers/"
        w_rec_list = acquireRecList(IDs,ans_path)
        for K in K_list:
            MAP,_AP = acquireAPMetric(w_rec_list,cmd_rels,K)
            MRR,_RR = acquireRRMetric(w_rec_list,cmd_rels,K)
            AP_dict[_v][str(K)] = {**{'AVG':{'MAP':MAP,'MRR':MRR}},**{ID:{'MAP':_AP[ID],'MRR':_RR[ID]} for ID in IDs}}
    # output result.
    dumpJson(AP_dict,'./variant_analyze_res.json')
    dumpJson(cmd_rels,'./all_cmd_rels.json')

def k_analysis():
    K_list = [1,3,5]
    ID_queries = {i.split(' ===> ')[0]:i.split(' ===> ')[1]for i in readTxt('k_queries.txt')}
    IDs = list(ID_queries.keys())    
    k_res_list = acquireRecList(IDs,'./ShellFusion++/answers/')
    cmd_rels = readJson('./all_cmd_rels.json')
    avg_dict = dict()
    for _k in K_list:
        _k_rec_list = {ID:rec_list[:_k] for ID,rec_list in k_res_list.items() }
        avg_dict[_k] = dict()
        [dumpJson(rec,f'../new_k_analysis/k_{_k}/{_i}.json') for _i,rec in _k_rec_list.items()]
        for K in K_list:
            MAP,_AP = acquireAPMetric(_k_rec_list,cmd_rels,K)
            MRR,_RR = acquireRRMetric(_k_rec_list,cmd_rels,K)   
            avg_dict[_k][K] = {**{'AVG':{'MAP':MAP,'MRR':MRR}},**{ID:{'MAP':_AP[ID],'MRR':_RR[ID]} for ID in IDs}}
            
    dumpJson(avg_dict,'.k_analyze_res.json')
    

if __name__ == "__main__":
    '''
    RQ1: What is the best setting of weights in ShellFusion++?
    RQ2: What is the best setting of parameter k in ShellFusion++?
    RQ3: How effective is ShellFusion++ in shell command recommendation?
    '''
    ##### RQ1 #####
    w = [float(i/10) for i in range(1,11,1)]
    ws_list = [[1,1,1]]
    for w1 in w:
        for w2 in w:
            w3 = float(1.0-w1-w2)
            w3 = float(Decimal(w3).quantize(Decimal('0.1'),rounding = 'ROUND_HALF_UP'))
            if w3 <= 0.0 or (w1==w2 and w2==w3):continue
            ws_list.append([w1,w2,w3])
    #weight_analyze(ws_list)
    ##### RQ2 #####

    ##### do k analysis
    #k_analysis()

    ##### RQ3 #####
    #variant_weight_analyze()
    

