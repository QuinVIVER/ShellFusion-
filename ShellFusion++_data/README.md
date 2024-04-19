此文件夹存储了功能类别和句型模式的标注结果文件和用户实验的相关数据文件。

## Func_category
1. Step1_verb_analysis.xlsx: 展示从四个信息源解析的每个功能动词的出现情况。
2. Step2_delete_noneVerb.xlsx: 展示我们决定从功能动词列表中删除的动词。
3. Step3_newVerb_categorize.xlsx: 展示了我们将每个功能动词分类为功能类别的标注结果。
4. categories.xlsx: 展示了最终的功能类别标注结果，列表中的每一行代表一个功能类别，每一列存储一个动词。
5. categories.txt：展示了最终的功能类别标注结果，每一行代表一个功能类别，类别中的动词以斜杠分割。
5. funcverbnet_categories.txt: 展示了funcverbnet标注的功能类别。

## Phrase_pattern
1. pattern_annotation_result.xlsx: 记录了以是否来自Q&A论坛作为分类条件的最终的句型模式标注结果与每个模式的出现次数。
2. annotation_coverage.xlsx: 记录了每轮迭代标注的句型模式覆盖率
3. iterate_annotation: 文件夹，记录了每轮迭代查询的结果
4. NOQA_pattern_annotation.json: 记录来自TLDR，NL2Bash数据集的句型模式标注结果。
5. QA_pattern_annotation.json: 记录来自Q&A论坛的句型模式标注结果。
6. pattern_list.json: 记录了以是否来自Q&A论坛作为分类条件的最终的句型模式标注结果。

## RQ_data&result
存储了关键步骤的流程图与RQ问题的相关统计数据文件。
1. RQ1_weight_analysis: 存储了ShellFusion++在不同权重分布下的推荐结果与数据分析文件。
2. RQ2_k_analysis: 存储了ShellFusion++在不同k值下的推荐结果与数据分析文件。
3. RQ3_app_compare: 存储了ShellFusion++各个变体与相似答案推荐方法的推荐结果与数据分析文件。
4. RQ4_efficiency: 存储了ShellFusion++的数据处理时间与平均推荐时间。
6. code: 计算指标时使用到的辅助代码
### RQ1_weight_analysis
1. queries.txt: 434个候选问题
2. answers_weight_analyze: 存储了不同权重设置下ShellFusion++对434个候选问题的推荐结果
3. ShellFusion++_weight_analyze_MAP.xlsx: 存储了不同权重设置下ShellFusion++对434个候选问题的MAP指标计算结果。每一行代表一个查询问题，存储了MAP@1,MAP@3,MAP@5的值与ShellFusion对同一问题的指标。
4. ShellFusion++_weight_analyze_MAP.xlsx: 存储了不同权重设置下ShellFusion++对434个候选问题的MRR指标计算结果。每一行代表一个查询问题，存储了MRR@1,MRR@3,MRR@5的值与ShellFusion对同一问题的指标。
5. weight_analytic.xlsx: 存储了ShellFusion++在不同权重分布下对434个候选问题的最终MAP，MRR指标结果。
6. weight_analytic.json: 同上，但存储了434个问题在不同权重分布和不同K值下各自的MAP，MRR指标，键依次为方法，K值和问题ID。
### RQ2_k_analysis
1. k_queries.txt: 50个候选问题
2. rec_result: 存储了50个候选问题在k=1,3,5,10,15,20下的答案推荐结果
3. k_analyze_res.json: 存储了50个候选问题在k=1,3,5,10,15,20下的MAP,MRR指标
4. k_app_avgmetrics.xlsx: 存储了在不同k值下的MAP,MRR指标最终计算结果
### RQ3_app_compare
1. queries.txt: 434个候选问题
2. all_cmd_rels.json: 记录了ShellFusion++与其变种方法对434个候选问题所推荐命令的相似度(0-4)。
3. Magnum.json: 记录了Magnum对434个候选问题所推荐命令的相似度(0-4)。
4. ShellFusion: 记录了原始ShellFusion方法对434个候选问题生成的答案。
5. ShellFusion++: 记录了ShellFusion++方法对434个候选问题生成的答案。
6. ShellFusion++_QA:记录了只使用Q&A信息进行答案推荐的ShellFusion++方法对434个候选问题生成的答案。
7. ShellFusion++_QA+MPs:记录了使用Q&A和MPs信息进行答案推荐的ShellFusion++方法对434个候选问题生成的答案。
8. ShellFusion++_QA+TLDR:记录了使用Q&A和TLDR信息进行答案推荐的ShellFusion++方法对434个候选问题生成的答案。
9. app_avgmetrics.xlsx: 各方法在434个候选问题中的最终MAP，MRR指标结果，含统计显著性检测结果。
10. app_avgmetrics.json: 同上，但存储了每个问题在不同方法和不同K值下的MAP，MRR值，键依次为方法，K值和问题ID。


## User_study
存储了用户实验的相关文件与统计数据文件。
1. material: 提供给用户的评估文件，包含使用说明与评估用文件。
2. evaluation: 20个用户返回的评估文件。
3. user_study_avg&std.xlsx: 根据用户评估结果计算得到的各方法平均值与方差值，每一行代表一个方法，每列则是不同的指标。（含显著性检验结果）
4. userstudy_compare.xlsx: 统计显著性检验结果的计算文件。
5. queries_answered.xlsx: 四组参与者使用三种方法回答问题的数量。每个单元格中的“m(n)”表示 m 个查询中 n 个的答案是正确的。
