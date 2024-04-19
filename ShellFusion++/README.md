此文件夹包含了ShellFusion++的代码和数据。
ShellFusion++ 是一种通过融合从四个数据源中挖掘的知识来生成 shell 编程任务答案的方法，数据源包括 1) 来自 Stack Overflow、Ask Ubuntu、Super User 和 Unix & Linux 的问答帖子； 2) Ubuntu 手册页 (MP)：http://manpages.ubuntu.com； 3) TLDR 教程：https://github.com/tldr-pages/tldr。 4) NL2Bash 数据集。

## 代码
代码分别存储在两个文件夹中: 
1. offline: 包含ShellFusion++的offline数据处理代码;
2. online: 包含ShellFusion++的online答案推荐代码.
### offline
1. mp_analyzer: 
检测 MP 中的 shell 命令知识。
2. post_parser: 从 Stack Overflow、Ask Ubuntu、Super User 和 Unix & Linux 的Q&A帖子中收集与 shell 编程相关的帖子。
3. post_preprocessor: 用于词干提取(stemming)和停用词删除(stop word removal)。
4. tldr_parser, tldr_analyzer: 从 TLDR 教程中收集 shell 命令知识。
5. data_parser: 解析Q&A帖子、TLDR 教程和 NL2Bash 数据集，获得与 shell 相关的问题/任务脚本对。
6. graph_generator: 从解析的数据生成基于shell 相关任务的知识图谱。
7. tdidf_trainer, w2v_trainer, model_trainer: 创建一个包含 555,650 个 shell 相关问题的 lucene 文档文件，并训练词嵌入模型和得到 IDF 词汇表。
8. ES_indexer: 使用 lucene 文档构建 elasticsearch 索引。
### online
1. query_preprocesser: 对用户查询进行预处理。
2. ES: 使用elasticsearch，为用户查询返回 top-N 相似任务
3. category_analyzer: 找到用户查询所归属的功能类别
4. pattern_extractor: 提取用户查询的句型模式，计算两个所输入句型模式的相似度。句型模式相似度计算公式如下

$$\text{cnt} =  {\textstyle \sum_{i=0}^{len(candidate\_pattern)-1}} \begin{cases} 1, & \text{如果 } \text{candidate\_pattern}[i] \text{ 与 } \text{query\_pattern的一个元素相同} \\ 0, & \text{否则} \end{cases}$$

$$\text{pattern\_sim} = \frac{\text{cnt}}{\text{max}(\text{len(query\_pattern)},\text{len(candidate\_pattern)})}$$

5. similarity: 基于 IDF 词汇表和词嵌入模型计算两个文档之间的语义相似度。
6. SimQ_retriever: 基于语义相似度、功能类别相似度和短语模式相似度检索 top-n 个相似任务。相似度计算公式如下

$$C_{1}:\text{功能类别相似度},C_{2}:\text{语义模式相似度},C_{3}:\text{语义相似度}$$

$$\text{task\_sim} = 0.4*C_{1} + 0.3*C_{2} + 0.3 * C_{3}$$

7. answer_generator: 对 top-n 任务中的命令进行重新排序，并为 top-k 命令生成完整的答案。


## 数据

1. exp_models_dir: 包含了 lucene 文档与由此训练得到的词嵌入模型和IDF 文档、在研究中归纳得到的功能类别、句型模式列表和代码所生成的知识图谱、官方手册信息文件。
2. exp_tasks_dir: 包含了NL2Bash、TLDR数据集与Q&A论坛的shell相关帖子。
3. exp_evaluation_dir: 包含了434个用户查询的top-N和top-n相似任务。
4. retrievePattern.png/xml: 生成知识图谱/构建推荐系统流程中，获取任务/用户查询句型模式的流程图。

### exp_models_dir
1. task_graph.json: 所生成的知识图谱，以键值对方式组织。其中task的id作为主键(来自Q&A论坛的task，id取其post id，nl2bash和tldr的task则根据出现顺序进行编号)，每个键值对下存储了自然语言描述的任务、任务id、任务对应Shell脚本，脚本中使用到的命令及选项在MPs、TLDR中的解释、功能动词、所属功能类别以及句型模式。
2. lucene_docs.txt: 生成的Lucene语料，每一行代表一个Shell task。
3. categories.txt: 功能类别列表，每一行代表一个功能类别，类别中的动词以斜杠进行划分。
4. pattern_list.json: 句型模式列表，以标注时是否来自Q&A帖子进行划分，数字代表其在标注时出现的次数。在在线推荐流程中，会将qa与noqa的句型模式进行合并。
5. w2v.input/w2v.kv/w2v.kv.vectors.npy: 构建的word2vec语料与训练得到的词嵌入模型。
6. tfidf.input/token_df.dump/token_idf.dump: 构建的tfidf语料与得到的idf词库。
7. mpcmd_info.json: 从MPs中提取的Shell命令相关知识。

### exp_tasks_dir
1. exp_nl2bash_dir: 存储了nl2bash数据集的原始文件，all.nl存储的是自然语言任务，在all.cm中与之行号相同的脚本即为任务对应的脚本。
2. exp_posts_dir: 存储了从Q&A论坛中提取的Shell相关帖子。
3. exp_tldr_dir: 存储了tldr数据集中提取的相关知识。
4. NL2Bash/TLDRParsed_task-script_pairs.json/QAParsed_shell_questions.json: 知识图谱构建流程的中间产物，主键为功能类别（来自funcverbnet），每个键值对下存储了自然语言描述的任务、任务id、任务对应Shell脚本、对任务的pos-tagging结果。




