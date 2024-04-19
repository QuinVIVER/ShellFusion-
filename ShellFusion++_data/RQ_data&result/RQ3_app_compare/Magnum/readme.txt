
Magnum.xlsx：Magnum 为 434 个实验查询生成/推荐的 Shell Command Templates。

各字段解释如下：
1. Query Id：查询Id；
2. Query：查询条件；
3. Magnum Result：Magnum 为查询条件生成的结果，即 Shell Command Templates；
4. Cmd Relevance (0-4)：记录 Magnum 生成结果中与查询最相关的 Shell Command 及相关性等级，其中已有的记录是在前期评估中已识别的最相关 Shell Command 及评分。
                        -- 注意：Magnum 生成结果中可能存在前期未评估的、更为相关的 Shell Commands！
6. Cmd Summary：Magnum 生成结果中在前期评估中已识别的最相关 Shell Command 或者 Magnum 生成结果中首个 Shell Command 的功能摘要，用于帮助快速理解并进行人工评估。
                -- 注意：并未显示 Magnum 生成结果中所有涉及的 Shell Commands 的功能摘要。
