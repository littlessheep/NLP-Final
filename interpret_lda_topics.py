import csv
import os
import re
from pathlib import Path


K = 15
LDA_DIR = Path("output") / f"lda_k{K}"
OUT_DIR = LDA_DIR / "topic_interpretation"


TOPIC_META = {
    1: {
        "name_zh": "技术支持的在线与协作学习设计",
        "name_en": "Technology-Enhanced Online and Collaborative Learning Design",
        "explanation": "该主题主要关注在线学习、游戏化学习、协作学习和技术支持的课程设计。高概率词包括 learning、student、design、online、teaching、technology、system 和 course。代表文档多讨论如何通过在线讨论、游戏化系统、智能学习环境或数字工具改善学生学习体验，因此将该主题命名为“技术支持的在线与协作学习设计”。",
    },
    2: {
        "name_zh": "STEM与工程科学教育",
        "name_en": "STEM and Engineering Science Education",
        "explanation": "该主题集中在科学、工程、STEM 课程和学生职业兴趣培养上。高概率词包括 science、engineering、stem、project、technology、mathematics、major 和 career。代表文档涉及工程课程设计、STEM outreach camp、微电子或生物识别等工程科技课程，因此将该主题命名为“STEM与工程科学教育”。",
    },
    3: {
        "name_zh": "教师教育、课程设计与专业发展",
        "name_en": "Teacher Education, Curriculum Design, and Professional Development",
        "explanation": "该主题主要讨论教师、教学实践、课程设计、评价和专业发展。高概率词包括 teacher、teaching、program、practice、evaluation、curriculum、professional 和 school。代表文档关注教师评价决策、教学监督、UDL 课程设计和教师技术整合能力，因此将该主题命名为“教师教育、课程设计与专业发展”。",
    },
    4: {
        "name_zh": "化学与实验室科学教学",
        "name_en": "Chemistry and Laboratory Science Instruction",
        "explanation": "该主题围绕化学、实验室课程、实验设计和科学概念学习展开。高概率词包括 chemistry、laboratory、experiment、concept、scientific、reaction、biology 和 chemical。代表文档多为有机化学实验、微流控实验、光谱分析和生物化学实验课程，因此将该主题命名为“化学与实验室科学教学”。",
    },
    5: {
        "name_zh": "在线学习中的自我调节、动机与参与",
        "name_en": "Self-Regulation, Motivation, and Engagement in Online Learning",
        "explanation": "该主题强调学生在在线学习环境中的自我调节、学习动机、学业情绪、感知和参与。高概率词包括 self、online、motivation、academic、efficacy、perceive、relationship 和 engagement。代表文档多使用结构方程模型或路径模型分析在线学习中的心理因素，因此将该主题命名为“在线学习中的自我调节、动机与参与”。",
    },
    6: {
        "name_zh": "学生成绩、测试与学习效果评估",
        "name_en": "Student Achievement, Testing, and Learning Outcome Evaluation",
        "explanation": "该主题主要关注学生表现、测试成绩、课程效果、年级差异和学习结果评估。高概率词包括 test、performance、score、effect、year、school、grade、class 和 difference。代表文档通常比较不同学生群体或教学干预后的成绩变化，因此将该主题命名为“学生成绩、测试与学习效果评估”。",
    },
    7: {
        "name_zh": "医学、护理与临床健康教育",
        "name_en": "Medical, Nursing, and Clinical Health Education",
        "explanation": "该主题集中在医学教育、临床训练、患者照护、护理、药学和健康专业课程上。高概率词包括 medical、clinical、health、patient、care、nursing、training、pharmacy 和 medicine。代表文档涉及医学生、护理学生或健康专业学生的临床能力和课程培训，因此将该主题命名为“医学、护理与临床健康教育”。",
    },
    8: {
        "name_zh": "学业路径、职业发展与高等教育机构",
        "name_en": "Academic Pathways, Career Development, and Higher Education Institutions",
        "explanation": "该主题关注学生的学业发展、专业选择、职业路径、学位获得、社区学院和高等教育机构因素。高概率词包括 academic、program、career、institution、degree、community、college 和 major。代表文档多讨论学生在学校或学院中的学习经历、留存、转学和职业结果，因此将该主题命名为“学业路径、职业发展与高等教育机构”。",
    },
    9: {
        "name_zh": "英语语言、写作与读写能力",
        "name_en": "English Language, Writing, and Literacy Development",
        "explanation": "该主题主要涉及英语学习、写作、阅读、词汇、文本理解和外语能力发展。高概率词包括 language、english、write、reading、chinese、literacy、vocabulary、efl 和 comprehension。代表文档多关注 EFL 学习者、英语写作任务和阅读理解能力，因此将该主题命名为“英语语言、写作与读写能力”。",
    },
    10: {
        "name_zh": "学生健康、性别与社会心理因素",
        "name_en": "Student Health, Gender, and Psychosocial Factors",
        "explanation": "该主题聚焦学生健康、性别、家庭、压力、心理健康和社会因素。高概率词包括 child、school、health、social、gender、woman、female、stress、mental 和 family。代表文档多讨论儿童、女性或学生群体的健康与社会心理问题，因此将该主题命名为“学生健康、性别与社会心理因素”。",
    },
    11: {
        "name_zh": "批判性思维、问题解决与身份发展",
        "name_en": "Critical Thinking, Problem Solving, and Identity Development",
        "explanation": "该主题强调问题解决、知识建构、批判性思维、身份认同、理论理解和领导力发展。高概率词包括 problem、identity、knowledge、process、think、critical、solving、theory 和 leadership。代表文档通常关注学生如何形成专业身份、理解复杂概念或发展高阶思维能力，因此将该主题命名为“批判性思维、问题解决与身份发展”。",
    },
    12: {
        "name_zh": "同行反馈、学术出版与文献评审",
        "name_en": "Peer Feedback, Academic Publishing, and Literature Review",
        "explanation": "该主题主要关注同行反馈、论文评审、期刊发表、文献检索、博士培养和学术写作支持。高概率词包括 feedback、peer、review、journal、publication、publish、literature、author 和 phd。代表文档涉及同行评阅、教师反馈、文献综述和研究生学术发表，因此将该主题命名为“同行反馈、学术出版与文献评审”。",
    },
    13: {
        "name_zh": "测量模型、量表验证与研究方法",
        "name_en": "Measurement Models, Scale Validation, and Research Methods",
        "explanation": "该主题集中在模型、测量工具、测试项目、因素分析、效度、信度和数据分析方法上。高概率词包括 model、item、test、factor、measure、scale、validity、instrument 和 reliability。代表文档多为量表开发、测验验证或统计模型应用研究，因此将该主题命名为“测量模型、量表验证与研究方法”。",
    },
    14: {
        "name_zh": "住院医师、外科与医学培训评价",
        "name_en": "Residency, Surgery, and Medical Training Assessment",
        "explanation": "该主题是医学教育中更具体的住院医师和外科培训方向。高概率词包括 resident、medical、program、training、surgery、residency、surgical、test、score 和 director。代表文档多涉及住院医师项目、外科能力、培训评价和考试成绩，因此将该主题命名为“住院医师、外科与医学培训评价”。",
    },
    15: {
        "name_zh": "国际学生、中国语境与跨文化高等教育",
        "name_en": "International Students, Chinese Contexts, and Cross-Cultural Higher Education",
        "explanation": "该主题关注国际学生、中国语境、文化适应、全球化、政策与高等教育发展。高概率词包括 international、chinese、academic、cultural、china、policy、country、global、institution 和 development。代表文档多讨论中国或国际学生的学习经历、跨文化挑战和教育政策，因此将该主题命名为“国际学生、中国语境与跨文化高等教育”。",
    },
}


def load_topic_words():
    rows = {}
    with open(LDA_DIR / f"lda_k{K}_topic_words.csv", "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            topic = int(row["topic"])
            rows.setdefault(topic, []).append(row["word"])
    return rows


def load_prevalence():
    prevalence = {}
    with open(LDA_DIR / f"lda_k{K}_topic_prevalence.csv", "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prevalence[int(row["topic"])] = float(row["mean_document_proportion"])
    return prevalence


def load_representative_docs():
    text = (LDA_DIR / f"lda_k{K}_representative_docs.md").read_text(encoding="utf-8-sig")
    docs = {}
    for topic in range(1, K + 1):
        match = re.search(rf"## Topic {topic}\n\n(.*?)(?=\n## Topic {topic + 1}\n\n|\Z)", text, re.S)
        entries = re.findall(
            r"Rank (\d+): Document (\d+), probability ([0-9.]+)",
            match.group(1) if match else "",
        )
        docs[topic] = [f"doc {doc_id} ({float(prob):.3f})" for _, doc_id, prob in entries[:5]]
    return docs


def write_outputs(topic_words, prevalence, representative_docs):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for topic in range(1, K + 1):
        meta = TOPIC_META[topic]
        top_words = topic_words[topic][:10]
        rows.append({
            "topic": topic,
            "topic_name_zh": meta["name_zh"],
            "topic_name_en": meta["name_en"],
            "mean_document_proportion": prevalence.get(topic, 0.0),
            "top_words": ", ".join(top_words),
            "representative_docs": "; ".join(representative_docs.get(topic, [])),
            "interpretation_zh": meta["explanation"],
        })

    with open(OUT_DIR / "topic_interpretation_table.csv", "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "topic",
            "topic_name_zh",
            "topic_name_en",
            "mean_document_proportion",
            "top_words",
            "representative_docs",
            "interpretation_zh",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with open(OUT_DIR / "topic_interpretation_report.md", "w", encoding="utf-8-sig") as f:
        f.write("# LDA Topic Interpretation / LDA 主题解释\n\n")
        f.write("最终 LDA 模型选择 K=15。由于本项目使用 Python LDA 而不是 R STM，因此此处提供的是 Top words / high-probability words，不包含 STM 特有的 FREX words。\n\n")
        f.write("## Summary Table / 汇总表\n\n")
        f.write("| Topic | 主题名称 | Topic Name | Proportion | Top Words | Representative Docs |\n")
        f.write("|---:|---|---|---:|---|---|\n")
        for row in rows:
            f.write(
                f"| {row['topic']} | {row['topic_name_zh']} | {row['topic_name_en']} | "
                f"{row['mean_document_proportion']:.4f} | {row['top_words']} | {row['representative_docs']} |\n"
            )

        f.write("\n## Topic Explanations / 主题解释\n\n")
        for row in rows:
            f.write(f"### Topic {row['topic']}: {row['topic_name_zh']}\n\n")
            f.write(f"**English label:** {row['topic_name_en']}\n\n")
            f.write(f"**Top words:** {row['top_words']}\n\n")
            f.write(f"**Representative documents:** {row['representative_docs']}\n\n")
            f.write(row["interpretation_zh"] + "\n\n")


def main():
    topic_words = load_topic_words()
    prevalence = load_prevalence()
    representative_docs = load_representative_docs()
    write_outputs(topic_words, prevalence, representative_docs)
    print(f"Topic interpretation files saved to {OUT_DIR}")


if __name__ == "__main__":
    main()
