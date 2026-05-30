# NLP Final Project README

这个项目目前的目标是：对英文摘要数据进行清洗和预处理，生成词频矩阵与 TF-IDF 矩阵，并在此基础上继续完成主题建模分析。

## 1. 项目当前已经完成的内容

项目已经完成了前期文本处理流程：

```text
原始摘要 abstracts.csv
-> 去除摘要中的结构化标题
-> 分词、小写化、停用词过滤
-> 词形还原与近义词归一
-> 再次停用词过滤
-> 异常 token 过滤
-> 生成 count matrix 和 TF-IDF matrix
```

当前主要脚本如下：

| 文件 | 作用 |
|---|---|
| `clean_abstracts.py` | 清洗原始摘要，去掉 Background、Methods、Results、Conclusion 等段落标题 |
| `process_abstracts.py` | 对清洗后的摘要做分词、停用词过滤、词形还原、近义词归一，并生成矩阵 |
| `stopwords.txt` | 停用词表，包括通用英文停用词和部分领域高频词 |
| `abstracts.csv` | 原始摘要数据 |
| `abstracts_cleaned.csv` | 清洗结构化标题后的摘要数据 |
| `output/` | 保存所有预处理结果和矩阵文件 |

## 2. 第一步：清洗原始摘要

运行：

```bash
python clean_abstracts.py
```

作用：

- 读取 `abstracts.csv`
- 去除摘要中常见的结构化标题，例如 `BACKGROUND`, `METHODS`, `RESULTS`, `CONCLUSION`
- 处理标题与正文粘连的问题
- 输出 `abstracts_cleaned.csv`

完成后检查：

```text
abstracts_cleaned.csv
```

确认摘要正文中不再大量出现 `Background:`、`Methods:`、`Results:` 这类标题。

## 3. 第二步：补充和检查停用词

停用词表在：

```text
stopwords.txt
```

这个文件用于删除不适合进入主题模型的词，例如：

```text
the
and
of
to
in
is
are
was
were
```

项目中还加入了一些领域高频词，例如：

```text
study
research
article
paper
education
result
analysis
finding
conclusion
```

注意：暂时保留 `not`、`no`、`without` 这类否定词，因为它们可能影响语义。

## 4. 第三步：预处理文本并生成矩阵

运行：

```bash
python process_abstracts.py
```

如果默认 `python` 环境缺少依赖，可以使用已经能运行的解释器：

```bash
F:\python\python.exe process_abstracts.py
```

这个脚本会执行：

```text
分词
-> 初步停用词过滤
-> 删除数字和含数字 token
-> 词形还原
-> 近义词归一
-> 再次停用词过滤
-> 异常英文 token 过滤
-> 生成词频矩阵和 TF-IDF 矩阵
```

为什么要“词形还原后再过滤一次停用词”：

```text
studies -> study
findings -> finding
outcome -> result
```

这些词可能在还原或映射之后才变成停用词，所以需要二次过滤。

## 5. 第四步：理解输出文件

所有结果保存在：

```text
output/
```

主要输出文件如下：

| 文件 | 含义 |
|---|---|
| `processed_docs.txt` | 每一行是一篇预处理后的摘要 |
| `count_matrix.npz` | 程序读取用的词频稀疏矩阵 |
| `count_matrix.txt` | 人可以直接看的词频结果 |
| `count_matrix_nonzero.csv` | 词频矩阵的非零元素表 |
| `tfidf_matrix.npz` | 程序读取用的 TF-IDF 稀疏矩阵 |
| `tfidf_matrix.txt` | 人可以直接看的 TF-IDF 结果 |
| `tfidf_matrix_nonzero.csv` | TF-IDF 矩阵的非零元素表 |
| `vocabulary.json` | 矩阵中的全部词汇 |
| `matrix_info.json` | 文档数、词汇量、矩阵形状、稀疏度等信息 |

### count_matrix.txt 是什么

`count_matrix.txt` 是词频矩阵的可读版本。

每一行代表一篇摘要，格式为：

```text
词:出现次数 词:出现次数 词:出现次数
```

例如：

```text
student:10 technology:9 gender:7 ability:6 gap:5
```

表示这一篇摘要中：

```text
student 出现 10 次
technology 出现 9 次
gender 出现 7 次
```

### tfidf_matrix.txt 是什么

`tfidf_matrix.txt` 是 TF-IDF 矩阵的可读版本。

每一行代表一篇摘要，格式为：

```text
词:TF-IDF权重 词:TF-IDF权重 词:TF-IDF权重
```

TF-IDF 权重表示一个词对当前文档的重要程度。一个词在当前摘要中出现较多，但在其他摘要中不太常见，它的 TF-IDF 权重就会更高。

简单区别：

```text
count_matrix.txt = 看词出现了几次
tfidf_matrix.txt = 看词对这篇摘要有多重要
```

## 6. 第五步：检查预处理是否干净

运行完 `process_abstracts.py` 后，先检查：

```text
output/count_matrix.txt
output/tfidf_matrix.txt
output/vocabulary.json
```

重点看是否还出现大量无意义词，例如：

```text
the
and
of
to
in
is
are
study
result
analysis
```

如果这些词仍然出现在前几位，说明停用词表还需要继续补充，或者处理顺序需要调整。

当前项目已经改成“词形还原后再次过滤停用词”，所以 `study`、`result`、`the`、`and`、`in` 这类词应当已经从词汇表中移除。

## 7. 第六步：做预处理统计

在正式建模前，需要做一些描述性统计，用于报告中的 Data Preprocessing 部分。

建议统计：

- 摘要数量
- 词汇总数
- 文档-词矩阵形状
- 非零元素数量
- 稀疏度
- 高频词 Top 20 或 Top 30
- 每篇摘要的词数分布

可以从这些文件中获得信息：

```text
output/matrix_info.json
output/count_matrix.txt
output/processed_docs.txt
output/vocabulary.json
```

建议生成的图表：

```text
1. 高频词柱状图
2. 每篇摘要词数分布图
3. 预处理前后样例对比表
```

## 8. 第七步：开始主题建模

根据课堂白板内容，项目后面应该继续做 Topic Modeling。

主题模型要回答：

```text
这些摘要主要可以分成哪些主题？
每个主题由哪些关键词代表？
每篇摘要更接近哪些主题？
```

可以选择两种路线：

| 方法 | 说明 |
|---|---|
| Python LDA | 使用 `sklearn.decomposition.LatentDirichletAllocation` |
| R STM | 使用 R 的 `stm` 包，更接近课堂白板和投影内容 |

如果老师要求 R，建议使用 STM。

如果继续用 Python，建议先用 LDA 完成主题模型。

## 9. 第八步：选择主题数量 K

不要只随便设一个 K。需要尝试多个主题数，例如：

```text
K = 5
K = 8
K = 10
K = 12
K = 15
K = 20
```

然后比较：

- 主题是否清楚
- 主题之间是否重复
- 每个主题的关键词是否有解释性
- 模型指标是否合理
- residual / coherence / exclusivity 是否可接受

最终报告中要解释：

```text
为什么选择这个 K？
```

例如：

```text
本文最终选择 K=10，因为该模型在主题可解释性、主题区分度和模型诊断结果之间取得了较好的平衡。
```

## 10. 第九步：解释每个主题

确定最终 K 后，需要输出每个主题的信息：

- Top words
- High probability words
- FREX words，如果使用 STM
- 代表文档
- 人工命名的主题名称

建议整理成表：

| Topic | 主题名称 | 高频词 | 代表文档 |
|---|---|---|---|
| Topic 1 | 医学教育与临床训练 | medical, clinical, patient, training | doc 2, doc 15 |
| Topic 2 | 技术学习与性别差异 | technology, gender, skill, student | doc 0, doc 31 |

每个主题都要写一小段解释，例如：

```text
Topic 1 主要关注医学教育中的临床训练。该主题的高频词包括 medical、clinical、patient、training，代表文档多讨论医学生在真实或模拟临床环境中的技能训练，因此将该主题命名为“医学教育与临床训练”。
```

## 11. 第十步：做主题可视化

建议至少完成以下图：

```text
1. 每个主题的 Top words 图
2. 主题相关性热力图
3. 主题聚类树状图
4. 每篇文档的主题分布图
```

如果数据中有年份字段，还可以做：

```text
5. 主题随时间变化趋势图
```

但是当前 `abstracts.csv` 主要是摘要文本。如果没有年份字段，就不需要做 trend，报告中说明数据缺少时间变量即可。

## 12. 第十一步：写最终报告

建议报告结构：

```text
1. Introduction
2. Data Description
3. Data Preprocessing
4. Feature Construction
5. Topic Modeling Method
6. Selection of Topic Number K
7. Topic Results and Interpretation
8. Topic Correlation Analysis
9. Conclusion
```

每一部分应该写什么：

| 部分 | 内容 |
|---|---|
| Introduction | 项目目标：分析英文摘要中的主要研究主题 |
| Data Description | 数据来源、摘要数量、字段说明 |
| Data Preprocessing | 清洗标题、分词、停用词、词形还原、矩阵生成 |
| Feature Construction | 说明 count matrix 和 TF-IDF matrix |
| Topic Modeling Method | 说明 LDA 或 STM 的基本思想 |
| Selection of K | 展示不同 K 的比较，并解释最终选择 |
| Topic Results | 展示每个主题的关键词、主题名和代表文档 |
| Correlation Analysis | 展示主题之间的相关关系 |
| Conclusion | 总结主要发现和项目局限 |

## 13. 最终提交文件建议

最终项目建议包含：

```text
README.md
clean_abstracts.py
process_abstracts.py
topic_modeling.py 或 topic_modeling.R
visualization.py 或 visualization.R
stopwords.txt
abstracts.csv
abstracts_cleaned.csv
output/
report.pdf 或 report.docx
```

其中最重要的是：

```text
1. 能复现的代码
2. 干净的预处理结果
3. 主题模型结果
4. 可视化图表
5. 最终报告
```

## 14. 下一步该做什么

当前最建议做的下一步是：

```text
1. 检查 output/count_matrix.txt 和 output/tfidf_matrix.txt，确认停用词已经清理干净
2. 做预处理统计图和高频词表
3. 开始尝试主题模型，先跑 K=5、10、15
4. 比较不同 K 的主题解释效果
5. 选择最终 K 并输出主题关键词和代表文档
```

简化成一句话：

```text
现在预处理基本完成，接下来进入“主题建模 + 结果解释 + 可视化 + 写报告”阶段。
```
