# 摘要文本处理输出说明文档

本文档解释 `process_abstracts.py` 脚本的处理逻辑，以及如何阅读和理解输出文件。

---

## 一、整体处理流程

脚本对摘要文本依次执行以下处理步骤：

```
原始摘要 (abstracts.csv)
    ↓  [clean_abstracts.py] 去除结构化标题（如 "Background", "Methods", "Results" 等）
清理后摘要 (abstracts_cleaned.csv)
    ↓  [process_abstracts.py] ① 空格分词 + ② 停用词过滤 + ③ 词形还原与近义词消除
预处理文本 (processed_docs.txt)
    ↓  [process_abstracts.py] ④ 构建词频矩阵 + ⑤ 构建 TF-IDF 矩阵
矩阵输出 (count_matrix / tfidf_matrix)
```

---

## 二、分词与词形处理逻辑

### 2.1 空格分词（Whitespace Tokenization）

- 将文本中的**所有标点符号替换为空格**
- 按空白字符分割
- 全部转为**小写**
- 过滤掉空字符串

> **注意**：此脚本不使用 NLTK 或 spaCy 的语义分词，而是采用简单的"空格分词"。因此像 "state-of-the-art" 会被拆成 "state", "the", "art"；"don't" 会被拆成 "don", "t"。

### 2.2 停用词与杂质过滤

从 `stopwords.txt` 加载停用词表，过滤掉以下 token：

1. **停用词**：如 `the`, `and`, `of`, `to` 等通用词，以及 `study`, `research`, `result`, `analysis`, `education`, `university` 等学术领域常见但对主题区分无贡献的词。

2. **长度过滤**：长度 `<= 1` 的词（如 "a", "i"）。

3. **纯数字**：如 `"2023"`, `"100"`。

4. **含数字的词**：**任何包含阿拉伯数字的 token 都会被过滤**，例如：
   - `09000016804586ba`, `0year`, `10month`, `16year`, `1973a`, `1a2`
   - `100mhz`, `12k`, `14k`, `16pf`, `103u`

> 这意味着所有最终保留的词都是**纯英文字母**组成的正常单词。

### 2.3 轻量级词形还原 + 近义词消除

这是最关键的一步。脚本使用**纯离线的规则引擎**（不依赖 NLTK 数据下载）将不同形态的词还原为标准形式，同时**保留完整单词拼写**。

#### 规则引擎处理示例

| 原始词形 | 还原规则 | 还原结果 |
|---------|---------|---------|
| technologies | -ies → -y | **technology** |
| abilities | -ies → -y | **ability** |
| studies | -ies → -y | **study** |
| lives | -ves → -fe | **life** |
| shelves | -ves → -fe | **shelf** |
| taxes | -es → 去掉 | **tax** |
| churches | -es → 去掉 | **church** |
| students | -s → 去掉 | **student** |
| participating | -ing 规则（加 e） | **participate** |
| stopped | -ed 规则（双写辅音） | **stop** |
| baked | -ed 规则（加 e） | **bake** |
| tried | -ied → -y | **try** |
| dying | -ying → -ie | **die** |
| curricula | 不规则复数表 | **curriculum** |
| analyses | 不规则复数表 | **analysis** |

> **与旧版 Porter Stemmer 的区别**：旧版会把 `technology` → `technolog`（截掉最后一个字母），`individual` → `individu`，`participate` → `particip`。新版使用规则还原，所有词都是**完整、可读的英文单词**。

#### 黑名单保护机制

规则引擎内置了黑名单，避免对非变形词进行错误还原：
- `-ing` 黑名单：`thing`, `something`, `string`, `during`, `morning`, `learning`, `teaching` 等
- `-ed` 黑名单：`bed`, `red`, `need`, `advanced`, `based`, `related`, `involved` 等
- `-s` 黑名单：`this`, `bus`, `class`, `status`, `crisis`, `focus`, `corpus` 等

#### 自定义近义词映射表

在词形还原后，脚本会根据教育/学术领域常见用法，将语义相近的词统一为一个标准形式：

| 被映射的词 | 统一为 |
|-----------|--------|
| pupil, learner, undergraduate, graduate, scholar | **student** |
| instructor, professor, educator, faculty | **teacher** |
| programme | **program** |
| curricula | **curriculum** |
| instruction | **teaching** |
| assessment, examination, exam | **evaluation** / **test** |
| skill | **ability** |
| knowledges | **knowledge** |
| technological | **technology** |
| methodology | **method** |
| outcome | **result** |
| impact | **effect** |
| utilize, utilizing, utilized, using, used, uses | **use** |

> **示例**：原文中的 `"students"`, `"learners"`, `"undergraduates"`, `"pupils"` 先经规则还原为 `"student"`, `"learner"`, `"undergraduate"`, `"pupil"`，再通过映射表统一变为 **`student`**，方便后续统计时语义一致。

---

## 三、输出文件阅读指南

### 3.1 预处理文本

| 文件 | 说明 |
|------|------|
| `processed_docs.txt` | 每行一篇预处理后的摘要文本，词之间用空格分隔。可以直接打开阅读，查看分词、停用词过滤、词形还原与近义词消除后的效果。 |

**示例**（第1行片段）：
```
study in gender have offer many reason for the different attitude and ability level ...
```
- 注意："study"（而非旧版的 "studi"）、"different"（而非 "differ"）、"attitude"（完整拼写）。

---

### 3.2 可读矩阵文件（推荐人工阅读）

| 文件 | 说明 |
|------|------|
| `count_matrix.txt` | **词频矩阵**的可读版本。每行对应一篇文档，格式为 `词:出现次数`。每行内部按出现次数**降序排列**。 |
| `tfidf_matrix.txt` | **TF-IDF 矩阵**的可读版本。每行对应一篇文档，格式为 `词:TF-IDF权重`。每行内部按权重**降序排列**。 |

**阅读方法**：
- 每行 = 一篇摘要
- `词:值` = 该词在该文档中的统计量
- 行内的顺序已经按重要性排序（词频高的/TF-IDF高的排在前面）

**count_matrix.txt 示例**：
```
technology:9 gender:7 ability:6 different:6 student:6 gap:5 ...
```
含义：这篇摘要中，"technology" 出现了 9 次，"gender" 出现了 7 次，"ability" 出现了 6 次……

**tfidf_matrix.txt 示例**：
```
technology:0.2871 gender:0.2745 ability:0.1752 student:0.0786 ...
```
含义：这篇摘要中，"technology" 的 TF-IDF 权重最高（0.2871），说明这个词对该文档的区分度最高。

> **TF-IDF 含义**：TF-IDF（词频-逆文档频率）不仅考虑词在文档中出现的次数，还会**惩罚在太多文档中都出现的常见词**。因此，TF-IDF 值高的词更能代表该文档的**独特主题**。

---

### 3.3 非零元素 CSV 文件（推荐用 Excel 分析）

| 文件 | 说明 |
|------|------|
| `count_matrix_nonzero.csv` | 词频矩阵中所有非零元素的列表 |
| `tfidf_matrix_nonzero.csv` | TF-IDF 矩阵中所有非零元素的列表 |

**格式**：四列，分别为
```
doc_index, term_index, term, value
```

| 列名 | 含义 |
|------|------|
| `doc_index` | 文档序号（从 0 开始，对应 `processed_docs.txt` 的行号） |
| `term_index` | 词汇序号（从 0 开始，对应 `vocabulary.json` 中的索引） |
| `term` | 词本身（还原/标准化后的完整英文单词） |
| `value` | 词频（整数）或 TF-IDF 权重（浮点数） |

**用途**：
- 用 Excel 打开后，可以**按词筛选**，查看某个特定词在哪些文档中出现过
- 可以**按文档筛选**，查看某篇文档包含哪些词
- 可以**按值排序**，快速找到高频词或高 TF-IDF 词

**示例**：
```csv
doc_index,term_index,term,value
0,17907,study,2
0,8827,in,13
0,7371,gender,7
```
含义：第 0 篇文档中，"study"（序号 17907）出现了 2 次，"in"（序号 8827）出现了 13 次，"gender"（序号 7371）出现了 7 次。

---

### 3.4 词汇表

| 文件 | 说明 |
|------|------|
| `vocabulary.json` | 所有出现在矩阵中的词（列名），按列索引顺序排列的 JSON 数组。 |

**用途**：
- 查看完整的词表
- 通过索引号找到某个序号对应的词
- 了解总共有多少个不同的词（即矩阵的列数）

> **注意**：由于已过滤含数字的词并做了词形还原，词汇表中不会出现如 `09000016804586ba`、`10month`、`1973a` 等杂质词，所有词都是正常的完整英文单词。

---

### 3.5 矩阵元信息

| 文件 | 说明 |
|------|------|
| `matrix_info.json` | 矩阵的基本统计信息 |

**包含内容**：
| 字段 | 含义 |
|------|------|
| `文档数量 (行数)` | 摘要总篇数（矩阵行数） |
| `词汇数量 (列数)` | 不同词的总数（矩阵列数） |
| `词频矩阵形状` | [行数, 列数] |
| `TF-IDF矩阵形状` | [行数, 列数] |
| `词频矩阵非零元素数` | 词频矩阵中非零项的总数 |
| `TF-IDF矩阵非零元素数` | TF-IDF 矩阵中非零项的总数 |
| `词频矩阵稀疏度` | 零元素所占比例（越接近 1 表示矩阵越稀疏） |
| `TF-IDF矩阵稀疏度` | 同上 |

> **稀疏度说明**：文本矩阵通常是极度稀疏的（稀疏度 > 0.99），因为每篇摘要只使用了词汇表中的一小部分词。

---

### 3.6 二进制矩阵文件（供程序读取）

| 文件 | 说明 |
|------|------|
| `count_matrix.npz` | 词频稀疏矩阵的 SciPy 二进制格式 |
| `tfidf_matrix.npz` | TF-IDF 稀疏矩阵的 SciPy 二进制格式 |

**用途**：供 Python 等程序直接加载进行后续分析（如聚类、主题建模、机器学习）。

**Python 读取示例**：
```python
import scipy.sparse as sparse
import json

# 加载矩阵
count_matrix = sparse.load_npz('output/count_matrix.npz')
tfidf_matrix = sparse.load_npz('output/tfidf_matrix.npz')

# 加载词汇表
with open('output/vocabulary.json', 'r', encoding='utf-8') as f:
    vocab = json.load(f)

# 查看矩阵形状
print(count_matrix.shape)

# 获取第 0 篇文档的词频向量
doc0 = count_matrix[0]
print(doc0.toarray())  # 转为密集数组（注意：可能会很大）
```

---

## 四、常见问题 FAQ

### Q1: 为什么现在看到的都是完整英文单词，不像以前那样被截断了？

因为脚本已将 **Porter Stemmer**（粗暴截断词尾）替换为**纯离线的规则词形还原引擎**。

| 对比 | 旧版 (Porter Stemmer) | 新版 (规则还原) |
|------|----------------------|--------------------------|
| technologies | `technolog` ❌ | `technology` ✅ |
| individual | `individu` ❌ | `individual` ✅ |
| participate, participated | `particip` ❌ | `participate` ✅ |
| studies | `studi` ❌ | `study` ✅ |
| abilities | `abil` ❌ | `ability` ✅ |

新版基于后缀规则（-ies→-y, -ves→-f, -ing→原形, -ed→原形 等）将词还原为标准形式，同时**保留完整可读性**，且不依赖任何外部数据或网络下载。

### Q2: 为什么词汇表里没有含数字的词了？

脚本在停用词过滤步骤中新增了一条规则：`any(ch.isdigit() for ch in token)`。只要 token 中包含任何阿拉伯数字（如 `10month`、`1973a`、`100mhz`），就会被直接丢弃。因此最终词汇表中所有词都是纯英文字母组成的正常单词。

### Q3: 词频和 TF-IDF 有什么区别？我该用哪个？

| 指标 | 含义 | 适用场景 |
|------|------|----------|
| **词频 (Count)** | 词在文档中出现的次数 | 了解文档的实际用词量；需要绝对数量时 |
| **TF-IDF** | 词频 × 逆文档频率 | 找出文档的**代表性/区分性**词汇；进行文档相似度计算、聚类、分类时 |

**建议**：
- 如果想看一篇摘要主要讲了什么（按实际出现次数）→ 看 `count_matrix.txt`
- 如果想找出某篇摘要区别于其他摘要的**特色词** → 看 `tfidf_matrix.txt`

### Q4: 如何找到包含某个特定词的文档？

打开 `count_matrix_nonzero.csv` 或 `tfidf_matrix_nonzero.csv`，用 Excel 的筛选功能在 `term` 列中搜索该词，所有 `doc_index` 就是包含该词的文档序号。然后到 `processed_docs.txt` 中找到对应行号（从 0 开始计数）即可阅读原文。

### Q5: 文档序号怎么对应回原始数据？

`processed_docs.txt` 的第 `N` 行（从 0 开始）对应 `abstracts_cleaned.csv` 的第 `N+1` 行数据（因为 CSV 有表头，且第 1 行是表头）。

### Q6: 脚本运行时还需要下载 NLTK 数据吗？

**不需要**。新版脚本已完全移除对 NLTK `wordnet`、`averaged_perceptron_tagger` 等在线数据的依赖，所有词形还原都是纯离线的规则引擎。只要安装了 `numpy`、`scipy`、`scikit-learn` 即可直接运行。

---

## 五、文件总览

| 文件名 | 格式 | 主要用途 |
|--------|------|----------|
| `processed_docs.txt` | 文本 | 人工阅读预处理后的摘要 |
| `count_matrix.txt` | 文本 | 人工阅读词频（按重要性排序） |
| `tfidf_matrix.txt` | 文本 | 人工阅读 TF-IDF 权重（按重要性排序） |
| `count_matrix_nonzero.csv` | CSV | Excel 分析词频分布 |
| `tfidf_matrix_nonzero.csv` | CSV | Excel 分析 TF-IDF 分布 |
| `vocabulary.json` | JSON | 查看完整词表 |
| `matrix_info.json` | JSON | 查看矩阵统计信息 |
| `count_matrix.npz` | 二进制 | Python 程序读取词频矩阵 |
| `tfidf_matrix.npz` | 二进制 | Python 程序读取 TF-IDF 矩阵 |
