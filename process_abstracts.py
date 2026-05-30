import sys
import csv
import os
import string
import json

# 修复 Windows 终端 UTF-8 输出
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

# 引入 wordfreq 用于词典检查和连词错误检测
# 需要先安装: pip install wordfreq
from wordfreq import zipf_frequency, top_n_list

# 预加载常用英文词表（用于检测连词错误，如 conclusionslower -> conclusions + lower）
_COMMON_WORDS = frozenset(top_n_list('en', n=50000))


def is_compound_error(token):
    """
    检查 token 是否由两个常见英文词拼接而成（连词错误）。
    例如: mydata -> my + data, conclusionslower -> conclusions + lower
    """
    n = len(token)
    # 尝试拆分为 2 个词
    for i in range(3, n - 3):
        left = token[:i]
        right = token[i:]
        if left in _COMMON_WORDS and right in _COMMON_WORDS:
            return True
    return False


def dictionary_filter(tokens):
    """
    对照正规英文词表过滤异常 token。
    使用 wordfreq 的 zipf_frequency 和启发式规则。
    """
    result = []
    for token in tokens:
        freq = zipf_frequency(token, 'en')

        # 1. 连续 3+ 个相同字母（如 aaaaaaa, ccc, eee）→ 过滤
        if __import__('re').search(r'(.)\1\1', token):
            continue

        # 2. 完全无元音(含y) 且 在任何语料库中都不存在 → 过滤
        # 常见无元音缩写如 pdf, phd, gdp, http 等频率通常 > 3.0，不会被误杀
        if not __import__('re').search(r'[aeiouy]', token) and freq == 0:
            continue

        # 3. 频率为 0（在任何语料库中都不存在）且长度 > 12 且可拆分为两个常见词 → 过滤
        # 这能捕获大量 clean_abstracts.py 未能清理的连词错误
        # 如: conclusionslower, backgroundacademic, mydata 等
        # 注意：会误杀少量合法前缀合成词（如 antioppressive），但比例很低
        if freq == 0 and len(token) > 12 and is_compound_error(token):
            continue

        result.append(token)
    return result

# ===================== 配置 =====================
INPUT_CSV = 'abstracts_cleaned.csv'
STOPWORDS_FILE = 'stopwords.txt'
OUTPUT_DIR = './output'

# ===================== 步骤1: 空格分词 =====================
def whitespace_tokenize(text):
    """
    按空格分词：去掉首尾引号和空白，将标点替换为空格，按空白分割。
    结果全部转为小写。
    """
    text = text.strip().strip('"')
    # 把所有标点替换为空格（保留单词完整性，不拆词）
    for p in string.punctuation:
        text = text.replace(p, ' ')
    # 按空白分割并过滤空字符串
    tokens = [t for t in text.lower().split() if t]
    return tokens


# ===================== 步骤2: 停用词过滤 =====================
def load_stopwords(path):
    """读取停用词表，返回小写集合。"""
    stopwords = set()
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip().lower()
            if word:
                stopwords.add(word)
    return stopwords


# ===================== 步骤3: 轻量级词形还原 + 近义词消除 =====================

# --- 不规则复数映射 ---
_IRREGULAR_PLURAL = {
    'curricula': 'curriculum',
    'phenomena': 'phenomenon',
    'analyses': 'analysis',
    'theses': 'thesis',
    'hypotheses': 'hypothesis',
    'children': 'child',
    'men': 'man',
    'women': 'woman',
    'feet': 'foot',
    'teeth': 'tooth',
    'mice': 'mouse',
    'people': 'people',
}

# --- -ing 结尾的黑名单（这些词不是动词的现在分词） ---
_ING_BLACKLIST = frozenset({
    'thing', 'things', 'something', 'nothing', 'anything', 'everything',
    'string', 'strings', 'bring', 'brings', 'bringing',
    'sing', 'sings', 'singing', 'wing', 'wings', 'winging',
    'king', 'kings', 'ring', 'rings', 'ringing',
    'spring', 'springs', 'springing',
    'during', 'morning', 'evening', 'ceiling', 'feeling', 'meaning',
    'training', 'learning', 'teaching', 'meeting', 'setting',
    'building', 'beginning', 'willing', 'funding', 'finding', 'fishing',
    'painting', 'housing', 'shopping', 'bearing', 'warning',
    'according', 'regarding', 'depending', 'concerning', 'following',
    'including',
})

# --- -ed 结尾的黑名单（这些词不是动词的过去式/过去分词） ---
_ED_BLACKLIST = frozenset({
    'bed', 'red', 'seed', 'feed', 'need', 'weed', 'deed', 'reed',
    'shed', 'bled', 'fled', 'bred', 'led', 'fed', 'wed', 'sped',
    'speed', 'succeed', 'proceed', 'exceed', 'precede', 'concede',
    'recede', 'secede', 'accede', 'impede', 'intercede',
    'advanced', 'based', 'related', 'located', 'involved', 'limited',
    'detailed', 'skilled', 'talented', 'gifted', 'educated',
    'dedicated', 'committed', 'connected', 'associated',
})

# --- 以 -s 结尾但不应去 s 的常见词 ---
_S_BLACKLIST = frozenset({
    'this', 'thus', 'plus', 'minus', 'virus', 'focus', 'campus',
    'status', 'crisis', 'basis', 'oasis', 'axis', 'testis',
    'bus', 'gas', 'mass', 'class', 'glass', 'grass', 'pass',
    'cross', 'loss', 'boss', 'toss', 'press', 'stress', 'dress',
    'address', 'access', 'success', 'process', 'progress',
    'distress', 'surplus', 'corpus', 'genus', 'cactus', 'fungus',
    'alumnus', 'stimulus', 'terminus', 'prospectus', 'apparatus',
    'hiatus', 'impetus', 'nexus', 'plexus', 'fetus',
})


def lemmatize_light(token):
    """
    轻量级词形还原，纯离线，不依赖任何外部数据。
    处理最常见的名词复数和动词变形，保留完整英文单词。
    """
    # 1. 不规则复数
    if token in _IRREGULAR_PLURAL:
        return _IRREGULAR_PLURAL[token]

    # 2. -ies -> -y  (abilities -> ability, studies -> study, tries -> try)
    if token.endswith('ies') and len(token) > 4:
        return token[:-3] + 'y'

    # 3. -ves -> -f/-fe  (lives -> life, shelves -> shelf, wolves -> wolf)
    if token.endswith('ves') and len(token) > 4:
        if token.endswith('lives'):
            return token[:-4] + 'ife'
        if token.endswith('wives'):
            return token[:-4] + 'ife'
        if token.endswith('shelves'):
            return token[:-4] + 'elf'
        if token.endswith('selves'):
            return token[:-4] + 'elf'
        if token.endswith('leaves'):
            return token[:-4] + 'eaf'
        if token.endswith('halves'):
            return token[:-4] + 'alf'
        return token[:-3] + 'f'

    # 4. -es -> 去掉 es  (taxes -> tax, buses -> bus, boxes -> box, churches -> church)
    if token.endswith('es') and len(token) > 3:
        if token.endswith(('sses', 'shes', 'ches', 'xes', 'zes', 'oes', 'ges', 'ses')):
            return token[:-2]

    # 5. -s -> 去掉 s  (students -> student, but not: this, bus, class)
    if token.endswith('s') and len(token) > 3:
        if token in _S_BLACKLIST:
            return token
        # 双写 s 通常不是简单复数 (unless -sses which is handled above)
        if token.endswith('ss'):
            return token
        return token[:-1]

    # 6. -ying -> -ie  (dying -> die, lying -> lie, tying -> tie)
    if token.endswith('ying') and len(token) > 5:
        return token[:-4] + 'ie'

    # 7. -ing -> 去掉 ing  (participating -> participate, making -> make)
    if token.endswith('ing') and len(token) > 5:
        if token in _ING_BLACKLIST:
            return token
        stem = token[:-3]
        # 双写辅音：stopping -> stop, sitting -> sit
        if len(stem) > 2 and stem[-1] == stem[-2] and stem[-1] not in 'aeiouy':
            return stem[:-1]
        # 辅音+元音+辅音，可能需要加 e：making -> make, taking -> take
        if len(stem) > 1 and stem[-1] not in 'aeiouywx' and stem[-2] in 'aeiou':
            return stem + 'e'
        # running -> run (stem = runn)
        if len(stem) > 1 and stem[-1] == 'n' and stem[-2] == 'n':
            return stem[:-1]
        return stem

    # 8. -ied -> -y  (tried -> try, carried -> carry, studied -> study)
    if token.endswith('ied') and len(token) > 4:
        return token[:-3] + 'y'

    # 9. -ed -> 去掉 ed  (participated -> participate, stopped -> stop, baked -> bake)
    if token.endswith('ed') and len(token) > 3:
        if token in _ED_BLACKLIST:
            return token
        stem = token[:-2]
        # 双写辅音：stopped -> stop
        if len(stem) > 2 and stem[-1] == stem[-2] and stem[-1] not in 'aeiouy':
            return stem[:-1]
        # 辅音+元音+辅音，可能需要加 e：baked -> bake, liked -> like
        if len(stem) > 1 and stem[-1] not in 'aeiouywx' and stem[-2] in 'aeiou':
            return stem + 'e'
        return stem

    return token


# 自定义近义词映射表（教育/学术领域常见近义词）
# 注意：此处使用【完整单词形式】，因为前面已用 lemmatize_light 做词形还原
SYNONYM_MAP = {
    # 学习者相关
    'pupil': 'student',
    'learner': 'student',
    'undergraduate': 'student',
    'graduate': 'student',
    'scholar': 'student',
    # 教师相关
    'instructor': 'teacher',
    'professor': 'teacher',
    'educator': 'teacher',
    'faculty': 'teacher',
    # 教学相关
    'programme': 'program',
    'curricula': 'curriculum',
    'instruction': 'teaching',
    'assessment': 'evaluation',
    'examination': 'test',
    'exam': 'test',
    # 能力相关
    'skill': 'ability',
    # 知识相关
    'knowledges': 'knowledge',
    # 技术相关
    'technological': 'technology',
    # 方法相关
    'methodology': 'method',
    # 其他常见学术近义词
    'outcome': 'result',
    'impact': 'effect',
    'utilize': 'use',
    # 兜底：防止还原未命中时的常见变体
    'utilizing': 'use',
    'utilized': 'use',
    'using': 'use',
    'used': 'use',
    'uses': 'use',
}


def synonym_normalize(tokens):
    """
    对一组 token 依次做轻量级词形还原和自定义近义词映射。
    纯离线，不依赖任何外部数据或网络。
    """
    result = []
    for token in tokens:
        lemma = lemmatize_light(token)
        # 应用自定义映射（若映射表中有，则替换；否则保留还原后的词）
        result.append(SYNONYM_MAP.get(lemma, lemma))
    return result


# ===================== 主流程 =====================
def main():
    # 1. 读取停用词
    stopwords = load_stopwords(STOPWORDS_FILE)
    print(f"停用词表加载完成，共 {len(stopwords)} 个词。")

    # 2. 读取 CSV 并依次执行三个预处理步骤
    processed_docs = []
    raw_count = 0

    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)  # 跳过表头
        except StopIteration:
            print("CSV 文件为空！")
            return

        for row in reader:
            if not row:
                continue
            raw_count += 1
            text = row[0]

            # 步骤1：空格分词
            tokens = whitespace_tokenize(text)

            # 步骤2：停用词过滤（同时过滤长度<=1的词、纯数字、含数字的词）
            tokens = [
                t for t in tokens
                if t not in stopwords
                and len(t) > 1
                and not t.isdigit()
                and not any(ch.isdigit() for ch in t)  # 过滤任何含数字的token
            ]

            # 步骤3：词形还原 + 近义词消除
            tokens = synonym_normalize(tokens)

            # 词形还原和近义词映射后可能重新产生停用词，例如 studies -> study。
            tokens = [t for t in tokens if t not in stopwords]

            # 步骤3b：对照正规英文词表过滤异常词
            tokens = dictionary_filter(tokens)

            # 再次过滤：还原后可能出现空字符串或单字符
            tokens = [t for t in tokens if len(t) > 1]

            # 重组为字符串（sklearn vectorizer 需要字符串输入）
            processed_docs.append(' '.join(tokens))

    print(f"共处理 {raw_count} 篇摘要。")

    # 保存预处理后的文本（方便复查）
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, 'processed_docs.txt'), 'w', encoding='utf-8') as f:
        for doc in processed_docs:
            f.write(doc + '\n')

    # ===================== 步骤4&5: 构建两个矩阵 =====================
    # 使用 sklearn 的 CountVectorizer 和 TfidfVectorizer
    # 因为已经预处理好了，所以 tokenizer 直接按空格 split，不再做额外转换

    # --- 矩阵A：词频矩阵 (Document-Term Count Matrix) ---
    count_vec = CountVectorizer(
        tokenizer=lambda x: x.split(),
        lowercase=False,       # 已经小写过
        token_pattern=None     # 禁用默认正则，完全使用自定义 tokenizer
    )
    count_matrix = count_vec.fit_transform(processed_docs)

    # --- 矩阵B：TF-IDF 矩阵 ---
    tfidf_vec = TfidfVectorizer(
        tokenizer=lambda x: x.split(),
        lowercase=False,
        token_pattern=None
    )
    tfidf_matrix = tfidf_vec.fit_transform(processed_docs)

    # ===================== 保存结果 =====================
    # 保存稀疏矩阵（npz 二进制格式，供程序读取）
    sparse.save_npz(os.path.join(OUTPUT_DIR, 'count_matrix.npz'), count_matrix)
    sparse.save_npz(os.path.join(OUTPUT_DIR, 'tfidf_matrix.npz'), tfidf_matrix)

    # 保存为易读的 txt 格式：每行一篇文档，格式为 "词:值 词:值 ..."
    def save_readable_txt(matrix, filepath, vocab_arr, is_int=True):
        """将稀疏矩阵保存为可读文本：每行一篇文档，只列出非零项。"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for i in range(matrix.shape[0]):
                row = matrix[i]
                cols = row.indices
                vals = row.data
                # 按值降序排列，让重要的词排在前面
                order = np.argsort(vals)[::-1]
                parts = []
                for idx in order:
                    term = vocab_arr[cols[idx]]
                    val = vals[idx]
                    if is_int:
                        parts.append(f"{term}:{int(val)}")
                    else:
                        parts.append(f"{term}:{val:.4f}")
                f.write(' '.join(parts) + '\n')

    # 同时保存一个"词汇-文档-值"的三列表格（CSV格式，方便用Excel打开分析特定词）
    def save_coo_csv(matrix, filepath, vocab_arr):
        """保存为非零元素的坐标列表 CSV：row, col, term, value"""
        coo = matrix.tocoo()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('doc_index,term_index,term,value\n')
            for i, j, v in zip(coo.row, coo.col, coo.data):
                f.write(f"{i},{j},{vocab_arr[j]},{v}\n")

    # 保存词汇表
    vocabulary = count_vec.get_feature_names_out().tolist()
    vocab_arr = np.array(vocabulary)
    
    save_readable_txt(count_matrix, os.path.join(OUTPUT_DIR, 'count_matrix.txt'), vocab_arr, is_int=True)
    save_readable_txt(tfidf_matrix, os.path.join(OUTPUT_DIR, 'tfidf_matrix.txt'), vocab_arr, is_int=False)
    save_coo_csv(count_matrix, os.path.join(OUTPUT_DIR, 'count_matrix_nonzero.csv'), vocab_arr)
    save_coo_csv(tfidf_matrix, os.path.join(OUTPUT_DIR, 'tfidf_matrix_nonzero.csv'), vocab_arr)

    with open(os.path.join(OUTPUT_DIR, 'vocabulary.json'), 'w', encoding='utf-8') as f:
        json.dump(vocabulary, f, ensure_ascii=False, indent=2)

    # 保存矩阵元信息
    info = {
        "文档数量 (行数)": count_matrix.shape[0],
        "词汇数量 (列数)": count_matrix.shape[1],
        "词频矩阵形状": list(count_matrix.shape),
        "TF-IDF矩阵形状": list(tfidf_matrix.shape),
        "词频矩阵非零元素数": int(count_matrix.nnz),
        "TF-IDF矩阵非零元素数": int(tfidf_matrix.nnz),
        "词频矩阵稀疏度": 1 - (count_matrix.nnz / (count_matrix.shape[0] * count_matrix.shape[1])),
        "TF-IDF矩阵稀疏度": 1 - (tfidf_matrix.nnz / (tfidf_matrix.shape[0] * tfidf_matrix.shape[1])),
    }
    with open(os.path.join(OUTPUT_DIR, 'matrix_info.json'), 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    # ===================== 打印说明性结果 =====================
    print("\n" + "="*60)
    print("处理完成！结果已保存到 './output/' 目录")
    print("="*60)
    print(f"文档数量 (矩阵行数): {info['文档数量 (行数)']}")
    print(f"词汇数量 (矩阵列数): {info['词汇数量 (列数)']}")
    print(f"词频矩阵非零元素: {info['词频矩阵非零元素数']}")
    print(f"TF-IDF矩阵非零元素: {info['TF-IDF矩阵非零元素数']}")
    print(f"词频矩阵稀疏度: {info['词频矩阵稀疏度']:.6f}")
    print(f"TF-IDF矩阵稀疏度: {info['TF-IDF矩阵稀疏度']:.6f}")


if __name__ == '__main__':
    main()
