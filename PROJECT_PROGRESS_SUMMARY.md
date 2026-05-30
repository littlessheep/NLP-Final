# NLP Final Project Progress Summary

本文档总结当前项目已经完成的工作，包括每一步的处理方法、生成的文件以及目前得到的主要结论。

## 1. 数据清洗

### 做了什么

项目首先使用 `clean_abstracts.py` 对原始摘要文件 `abstracts.csv` 进行清洗。

主要处理内容包括：

- 删除摘要中的结构化段落标题，例如 `BACKGROUND`、`METHODS`、`RESULTS`、`CONCLUSION` 等。
- 处理复合标题，例如 `Materials and Methods`。
- 处理 `Objective is to` 这类标题式表达。
- 处理标题和正文粘连的问题，例如 `ConclusionsMore` 这类情况。
- 清理多余空格。

### 得到了什么

生成文件：

```text
abstracts_cleaned.csv
```

该文件是去除结构化标题后的摘要文本，作为后续 NLP 预处理的输入。

### 结论

这一步减少了摘要中格式化标题对后续词频和主题模型的干扰，使模型更多关注摘要正文内容，而不是 `Background`、`Method`、`Result` 这类结构词。

## 2. 文本预处理与矩阵构建

### 做了什么

项目使用 `process_abstracts.py` 对 `abstracts_cleaned.csv` 进行进一步处理。

处理流程如下：

```text
读取清洗后的摘要
-> 标点替换为空格
-> 小写化
-> 按空格分词
-> 初步停用词过滤
-> 删除单字符、纯数字、含数字 token
-> 词形还原
-> 近义词归一
-> 再次停用词过滤
-> 异常英文 token 过滤
-> 生成词频矩阵和 TF-IDF 矩阵
```

其中，停用词表保存在：

```text
stopwords.txt
```

项目补充了通用英文停用词，例如：

```text
the, and, of, to, in, is, are, was, were
```

也补充了一些领域高频词，例如：

```text
study, research, article, paper, result, analysis, finding, conclusion
```

为了避免 `studies -> study`、`findings -> finding`、`outcome -> result` 这类词在词形还原后重新出现，脚本已经改成：

```text
词形还原和近义词归一之后，再过滤一次停用词
```

### 得到了什么

生成的主要文件位于 `output/`：

```text
processed_docs.txt
count_matrix.npz
count_matrix.txt
count_matrix_nonzero.csv
tfidf_matrix.npz
tfidf_matrix.txt
tfidf_matrix_nonzero.csv
vocabulary.json
matrix_info.json
```

其中：

- `count_matrix.txt` 表示每篇摘要中每个词出现的次数。
- `tfidf_matrix.txt` 表示每个词对每篇摘要的重要程度。
- `vocabulary.json` 是最终进入矩阵的词汇表。
- `processed_docs.txt` 是每篇摘要预处理后的文本。

### 结论

重新预处理后，`the`、`and`、`in`、`study`、`result` 等不适合作为主题词的词已经从词汇表中移除。最终矩阵更适合后续主题建模。

当前矩阵规模为：

```text
文档数：12195
词汇量：23818
矩阵形状：12195 x 23818
非零元素数量：878114
稀疏度：0.9969768213930355
```

## 3. 预处理统计

### 做了什么

项目新增 `preprocessing_stats.py`，用于生成预处理阶段的描述性统计。

统计内容包括：

- 摘要数量
- 词汇总数
- 文档-词矩阵形状
- 非零元素数量
- 稀疏度
- 最短、最长、平均和中位文档长度
- 高频词 Top 30
- 每篇摘要词数分布
- 预处理前后样例对比

### 得到了什么

输出目录：

```text
output/preprocessing_stats/
```

主要文件：

```text
summary.md
summary.csv
summary.json
top_words.csv
top_words_bar.png
doc_lengths.csv
doc_length_distribution.png
before_after_examples.csv
before_after_examples.md
```

其中：

- `summary.md` 是中英文双语统计总表。
- `top_words_bar.png` 是高频词柱状图，每个柱子标注了具体词频。
- `doc_length_distribution.png` 是文档长度分布图，每个柱子标注了对应文档数量。
- `before_after_examples.md` 展示了预处理前后文本变化。

### 得到了什么结论

当前预处理后的语料具有以下特征：

```text
摘要数量：12195
词汇总数：23818
最短文档长度：6
最长文档长度：445
平均文档长度：108.39
文档长度中位数：102
```

高频词 Top 10 为：

```text
student
learning
use
teacher
program
teaching
effect
based
data
experience
```

这些高频词说明该语料整体上高度集中于学生、学习、教师、教学、课程项目和教育效果等教育研究主题。

## 4. LDA 主题建模

### 做了什么

项目新增 `topic_modeling_lda.py`，使用 Python 的 `sklearn.decomposition.LatentDirichletAllocation` 进行 LDA 主题建模。

模型输入为：

```text
output/count_matrix.npz
output/vocabulary.json
output/processed_docs.txt
```

LDA 输出内容包括：

- 每个主题的高概率词
- 每篇文档的主题分布
- 每篇文档的主导主题
- 每个主题的代表文档
- 每个主题在语料中的平均占比
- 主题词图和主题占比图

### 得到了什么

最终模型输出目录为：

```text
output/lda_k15/
```

主要文件包括：

```text
lda_k15_topic_words.md
lda_k15_topic_words.csv
lda_k15_topic_words.png
lda_k15_doc_topic_distribution.csv
lda_k15_dominant_topics.csv
lda_k15_representative_docs.md
lda_k15_topic_prevalence.csv
lda_k15_topic_prevalence.png
lda_k15_summary.md
```

### 结论

LDA 模型成功将 12195 篇摘要表示为不同主题的混合分布，并为每个主题生成了高概率关键词和代表性文档。这为后续主题解释和报告写作提供了基础。

## 5. 主题数量 K 的选择

### 做了什么

项目新增 `select_lda_k.py`，用于比较不同主题数量下的 LDA 模型。

测试的 K 值为：

```text
K = 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50
```

其中：

```text
K = 1, 2, 3, 4
```

只作为 coarse reference，也就是粗粒度参考模型，不参与最终最佳 K 的选择。

原因是：这些 K 值虽然可能在某些指标上表现较好，但主题数量太少，无法满足项目中“发现多个可解释研究主题”的目标。

最终选择只在：

```text
K >= 5
```

的模型中进行。

### 评判标准

最终综合评分使用：

```text
0.35 * NPMI coherence
+ 0.25 * exclusivity
+ 0.20 * topic separation
+ 0.10 * topic diversity
+ 0.10 * inverse perplexity
```

各指标含义：

- `NPMI coherence`：主题内部关键词是否经常共同出现，越高越好。
- `exclusivity`：主题关键词是否具有独特性，越高越好。
- `topic separation`：不同主题之间是否区分明显，越高越好。
- `topic diversity`：不同主题的 Top words 是否重复较少，越高越好。
- `inverse perplexity`：模型拟合程度，perplexity 越低越好。

### 得到了什么

输出目录：

```text
output/lda_k_selection/
```

主要文件：

```text
best_k.md
best_k.json
lda_k_selection_metrics.csv
lda_k_composite_score.png
lda_k_npmi_coherence.png
lda_k_exclusivity.png
lda_k_topic_diversity.png
lda_k_topic_separation.png
lda_k_perplexity.png
```

### 结论

最终选择：

```text
K = 15
```

选择理由：

- `K=15` 在所有合格候选模型中综合评分最高。
- `K=15` 的 NPMI coherence 最高，说明主题内部关键词共现关系较好。
- 相比 `K=5` 和 `K=10`，`K=15` 的主题分离度更高，能够提供更细致的主题划分。
- 相比更大的 K，例如 `K=30`、`K=40`、`K=50`，`K=15` 的主题解释性更好，避免了主题过度碎片化。

因此，当前项目最终采用：

```text
LDA, K = 15
```

作为最终主题模型。

## 6. 主题解释与人工命名

### 做了什么

项目新增 `interpret_lda_topics.py`，基于最终 `K=15` 的 LDA 结果，对每个主题进行人工命名和解释。

使用的信息包括：

- 每个主题的 Top words
- 每个主题的 high-probability words
- 每个主题的代表文档
- 每个主题在语料中的平均占比

因为本项目使用的是 Python LDA，而不是 R STM，所以没有生成 STM 特有的 FREX words。

### 得到了什么

输出目录：

```text
output/lda_k15/topic_interpretation/
```

主要文件：

```text
topic_interpretation_report.md
topic_interpretation_table.csv
```

`topic_interpretation_report.md` 中包含：

- 15 个主题的汇总表
- 每个主题的中文名称
- 每个主题的英文名称
- 每个主题的平均占比
- 每个主题的 Top words
- 每个主题的代表文档
- 每个主题的中文解释段落

### 得到了什么结论

最终识别出的 15 个主题如下：

| Topic | 主题名称 | 英文名称 |
|---:|---|---|
| 1 | 技术支持的在线与协作学习设计 | Technology-Enhanced Online and Collaborative Learning Design |
| 2 | STEM与工程科学教育 | STEM and Engineering Science Education |
| 3 | 教师教育、课程设计与专业发展 | Teacher Education, Curriculum Design, and Professional Development |
| 4 | 化学与实验室科学教学 | Chemistry and Laboratory Science Instruction |
| 5 | 在线学习中的自我调节、动机与参与 | Self-Regulation, Motivation, and Engagement in Online Learning |
| 6 | 学生成绩、测试与学习效果评估 | Student Achievement, Testing, and Learning Outcome Evaluation |
| 7 | 医学、护理与临床健康教育 | Medical, Nursing, and Clinical Health Education |
| 8 | 学业路径、职业发展与高等教育机构 | Academic Pathways, Career Development, and Higher Education Institutions |
| 9 | 英语语言、写作与读写能力 | English Language, Writing, and Literacy Development |
| 10 | 学生健康、性别与社会心理因素 | Student Health, Gender, and Psychosocial Factors |
| 11 | 批判性思维、问题解决与身份发展 | Critical Thinking, Problem Solving, and Identity Development |
| 12 | 同行反馈、学术出版与文献评审 | Peer Feedback, Academic Publishing, and Literature Review |
| 13 | 测量模型、量表验证与研究方法 | Measurement Models, Scale Validation, and Research Methods |
| 14 | 住院医师、外科与医学培训评价 | Residency, Surgery, and Medical Training Assessment |
| 15 | 国际学生、中国语境与跨文化高等教育 | International Students, Chinese Contexts, and Cross-Cultural Higher Education |

整体来看，该语料主要围绕教育研究展开，主题覆盖：

- 在线学习与技术支持教学
- STEM 和工程教育
- 教师教育与专业发展
- 实验室科学教学
- 学习动机、自我调节和参与
- 学生成绩和测评
- 医学和临床健康教育
- 高等教育路径和职业发展
- 英语语言与读写能力
- 学生健康、性别和社会心理因素
- 学术出版、反馈和研究方法
- 国际学生与跨文化教育

## 7. 当前项目总体结论

目前项目已经完成了从原始摘要到主题解释的完整 NLP 流程：

```text
数据清洗
-> 文本预处理
-> 词频矩阵和 TF-IDF 矩阵构建
-> 描述性统计
-> LDA 主题建模
-> K 值选择
-> 主题命名与解释
```

主要结论是：

1. 该语料包含 12195 篇英文摘要，预处理后得到 23818 个有效词汇。
2. 高频词显示该语料高度集中于学生、学习、教师、教学、课程和教育效果。
3. 通过多个 K 值的 LDA 模型比较，最终选择 `K=15`。
4. 最终识别出 15 个较为清晰的教育研究主题。
5. 这些主题覆盖在线学习、STEM 教育、教师教育、医学教育、语言学习、测量方法和国际高等教育等方向。

## 8. 当前仍可继续改进的地方

当前结果已经可以用于报告，但仍有一些可以继续优化的地方：

- 继续清理异常词，例如 `engineere`、`reade`、`nurs`、`sic`、`cours` 等。
- 如果老师要求 R 或 STM，可以进一步用 R 的 `stm` 包复现主题模型。
- 如果能获得年份、国家、期刊或学科类别等 metadata，可以进一步分析主题趋势和主题差异。
- 可以增加主题相关性热力图或主题聚类图。
- 可以进一步润色每个主题的中文解释，使其更适合正式论文写作。

## 9. 关键文件索引

| 文件或目录 | 说明 |
|---|---|
| `clean_abstracts.py` | 原始摘要清洗脚本 |
| `process_abstracts.py` | 文本预处理和矩阵生成脚本 |
| `preprocessing_stats.py` | 预处理统计脚本 |
| `topic_modeling_lda.py` | LDA 建模脚本 |
| `select_lda_k.py` | K 值选择脚本 |
| `interpret_lda_topics.py` | 主题解释和人工命名脚本 |
| `stopwords.txt` | 停用词表 |
| `output/preprocessing_stats/` | 预处理统计结果 |
| `output/lda_k_selection/` | K 值选择结果 |
| `output/lda_k15/` | 最终 LDA 模型结果 |
| `output/lda_k15/topic_interpretation/` | 最终主题解释结果 |
