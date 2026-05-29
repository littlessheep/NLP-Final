import csv
import re

# ==================== 配置 ====================

# 1. 全大写段落标题 — 全局安全替换
ALL_CAPS_TITLES = [
    'INTRODUCTION', 'BACKGROUND', 'OBJECTIVE', 'OBJECTIVES',
    'PURPOSE', 'AIM', 'AIMS', 'CONTEXT', 'DESIGN', 'SETTING',
    'PARTICIPANTS', 'PHENOMENON', 'METHOD', 'METHODS',
    'MATERIALS', 'RESULT', 'RESULTS', 'FINDING', 'FINDINGS',
    'DISCUSSION', 'CONCLUSION', 'CONCLUSIONS', 'SUMMARY',
    'ORIGINALITY', 'VALUE', 'IMPLICATIONS',
    'EXPERIMENTAL', 'METHODOLOGY',
]

# 2. 明确的段落标题词 — 匹配后跟 : - / 的情况（不区分大小写，不匹配句点）
CLEAR_TITLE_WORDS = [
    'introduction', 'background', 'objective', 'objectives',
    'purpose', 'aim', 'aims', 'context', 'design', 'setting',
    'participants', 'phenomenon', 'method', 'methods',
    'materials', 'result', 'results', 'finding', 'findings',
    'discussion', 'conclusion', 'conclusions', 'summary',
    'value', 'description'
]

# 3. 较常见但可能是标题的词 — 仅匹配首字母大写后跟 : - /
RISKY_TITLE_WORDS = [
    'Originality', 'Implications',
    'Experimental', 'Methodology',
]

# 4. 特定复合标题模式（不区分大小写）
COMPOSITE_PATTERNS = [
    r'\bMaterials\s+and\s+Methods\b\s*[:：\-/.]+\s*',
    r'\bDesign\s*/\s*methodology\s*/\s*approach\b\s*[:：\-/.]+\s*',
    r'\bImplications?\s+for\s+(?:research\s+and\s+)?practice\b\s*[:：\-/.]+\s*',
]

# 5. "X is to" 结构
IS_TO_PATTERNS = [
    r'\b(?:Objective|Objectives|Purpose|Aim|Aims)\s+is\s+to\s+',
]

# 6. 可能出现在行首且没有分隔符的标题词
LEADING_TITLES = [
    'Introduction', 'Background', 'Objective', 'Objectives',
    'Purpose', 'Aim', 'Aims', 'Context', 'Design', 'Setting',
    'Method', 'Methods', 'Result', 'Results',
    'Discussion', 'Conclusion', 'Conclusions', 'Summary',
]

# ==================== 清理函数 ====================

def clean_text(text):
    # 步骤1: 先去掉复合标题（避免被单步匹配拆分）
    for pattern in COMPOSITE_PATTERNS:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    # 步骤2: 去掉全大写标题（任何位置）
    for title in ALL_CAPS_TITLES:
        text = re.sub(r'\b' + title + r'\b\s*[:：.\-/,]*\s*', ' ', text)
    
    # 步骤3: 去掉明确标题词 + : - / （不区分大小写，不匹配句点）
    for word in CLEAR_TITLE_WORDS:
        text = re.sub(r'\b' + re.escape(word.title()) + r'\b\s*[:：\-/]+\s*', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'\b' + re.escape(word) + r'\b\s*[:：\-/]+\s*', ' ', text, flags=re.IGNORECASE)
    
    # 步骤4: 去掉较常见词的标题用法（仅首字母大写 + : - /）
    for word in RISKY_TITLE_WORDS:
        text = re.sub(r'\b' + re.escape(word) + r'\b\s*[:：\-/]+\s*', ' ', text)
    
    # 步骤5: 去掉 "X is to" 类结构
    for pattern in IS_TO_PATTERNS:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    # 步骤6: 处理没有分隔符的标题词（如 "Background Family..." 或 "Results Students..."）
    # 仅当出现在行首或句号/分号后，且后面跟大写单词或 "To " 时匹配
    # 避免误伤 "Results from..." 等正文
    for word in LEADING_TITLES:
        text = re.sub(r'(^|[.;]\s+)' + re.escape(word) + r'(\s+)(?=(?-i:[A-Z]|To\s+))', r'\1', text, flags=re.IGNORECASE)
    
    # 步骤6b: 处理标题和正文之间完全没有空格的情况（如 "ConclusionsMore"）
    # 仅当出现在行首或句号/分号后，且后面直接跟大写单词或 "To" 时匹配
    for word in LEADING_TITLES:
        text = re.sub(r'(^|[.;]\s+)' + re.escape(word) + r'(?=(?-i:[A-Z]|To\s+))', r'\1', text, flags=re.IGNORECASE)
    
    # 步骤7: 清理多余空格
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

# ==================== 主程序 ====================

def main():
    input_file = 'abstracts.csv'
    output_file = 'abstracts_cleaned.csv'
    
    print(f"Reading from {input_file}...")
    
    cleaned_rows = []
    changed_examples = []
    unchanged_count = 0
    
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        cleaned_rows.append(header)
        
        for i, row in enumerate(reader):
            if not row:
                continue
            original = row[0] if row else ''
            cleaned = clean_text(original)
            
            if original != cleaned:
                if len(changed_examples) < 15:
                    changed_examples.append({
                        'row': i + 2,
                        'original_start': original[:150].replace('\n', ' '),
                        'cleaned_start': cleaned[:150].replace('\n', ' ')
                    })
            else:
                unchanged_count += 1
            
            cleaned_rows.append([cleaned])
    
    total = len(cleaned_rows) - 1
    changed = total - unchanged_count
    
    print(f"Total rows processed: {total}")
    print(f"Rows changed: {changed}")
    print(f"Rows unchanged: {unchanged_count}")
    
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(cleaned_rows)
    
    print(f"\nSaved cleaned abstracts to {output_file}")

if __name__ == '__main__':
    main()
