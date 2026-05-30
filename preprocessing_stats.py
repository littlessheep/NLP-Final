import csv
import json
import os
from collections import Counter
from statistics import mean, median

import matplotlib.pyplot as plt


PROCESSED_DOCS = os.path.join("output", "processed_docs.txt")
COUNT_MATRIX_TXT = os.path.join("output", "count_matrix.txt")
VOCABULARY_JSON = os.path.join("output", "vocabulary.json")
ABSTRACTS_CLEANED = "abstracts_cleaned.csv"
OUTPUT_DIR = os.path.join("output", "preprocessing_stats")


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_processed_docs():
    with open(PROCESSED_DOCS, "r", encoding="utf-8") as f:
        return [line.strip() for line in f]


def load_vocabulary_size():
    with open(VOCABULARY_JSON, "r", encoding="utf-8") as f:
        return len(json.load(f))


def parse_count_matrix():
    total_counts = Counter()
    nonzero_count = 0

    with open(COUNT_MATRIX_TXT, "r", encoding="utf-8") as f:
        for line in f:
            for item in line.strip().split():
                if ":" not in item:
                    continue
                term, value = item.rsplit(":", 1)
                try:
                    count = int(value)
                except ValueError:
                    continue
                total_counts[term] += count
                nonzero_count += 1

    return total_counts, nonzero_count


def save_summary(docs, vocab_size, nonzero_count):
    doc_lengths = [len(doc.split()) for doc in docs]
    doc_count = len(docs)
    matrix_cells = doc_count * vocab_size
    sparsity = 1 - (nonzero_count / matrix_cells) if matrix_cells else 0

    summary_rows = [
        ("document_count", "摘要数量", doc_count),
        ("vocabulary_size", "词汇总数", vocab_size),
        ("document_term_matrix_shape", "文档-词矩阵形状", f"{doc_count} x {vocab_size}"),
        ("nonzero_elements", "非零元素数量", nonzero_count),
        ("sparsity", "稀疏度", sparsity),
        ("min_doc_length", "最短文档长度", min(doc_lengths) if doc_lengths else 0),
        ("max_doc_length", "最长文档长度", max(doc_lengths) if doc_lengths else 0),
        ("mean_doc_length", "平均文档长度", mean(doc_lengths) if doc_lengths else 0),
        ("median_doc_length", "文档长度中位数", median(doc_lengths) if doc_lengths else 0),
    ]
    summary = {english: value for english, _, value in summary_rows}

    with open(os.path.join(OUTPUT_DIR, "summary.json"), "w", encoding="utf-8-sig") as f:
        json.dump(
            [
                {"metric_en": english, "metric_zh": chinese, "value": value}
                for english, chinese, value in summary_rows
            ],
            f,
            indent=2,
            ensure_ascii=False,
        )

    with open(os.path.join(OUTPUT_DIR, "summary.csv"), "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric_en", "metric_zh", "value"])
        for english, chinese, value in summary_rows:
            writer.writerow([english, chinese, value])

    with open(os.path.join(OUTPUT_DIR, "summary.md"), "w", encoding="utf-8-sig") as f:
        f.write("# Preprocessing Statistics / 预处理统计\n\n")
        f.write("| Metric | 指标 | Value / 数值 |\n")
        f.write("|---|---|---:|\n")
        for english, chinese, value in summary_rows:
            f.write(f"| {english} | {chinese} | {value} |\n")

    return summary, doc_lengths


def save_top_words(total_counts, top_n=30):
    top_words = total_counts.most_common(top_n)

    with open(os.path.join(OUTPUT_DIR, "top_words.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "word", "count"])
        for rank, (word, count) in enumerate(top_words, start=1):
            writer.writerow([rank, word, count])

    words = [word for word, _ in reversed(top_words)]
    counts = [count for _, count in reversed(top_words)]

    plt.figure(figsize=(10, 8))
    bars = plt.barh(words, counts, color="#3662A3")
    plt.xlabel("Total Count")
    plt.ylabel("Word")
    plt.title(f"Top {top_n} Words After Preprocessing")
    max_count = max(counts) if counts else 0
    for bar, count in zip(bars, counts):
        plt.text(
            bar.get_width() + max_count * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{count:,}",
            va="center",
            fontsize=8,
        )
    plt.xlim(0, max_count * 1.18 if max_count else 1)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "top_words_bar.png"), dpi=200)
    plt.close()


def save_doc_length_distribution(doc_lengths):
    with open(os.path.join(OUTPUT_DIR, "doc_lengths.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["doc_index", "processed_word_count"])
        for idx, length in enumerate(doc_lengths):
            writer.writerow([idx, length])

    plt.figure(figsize=(10, 6))
    counts, bins, patches = plt.hist(doc_lengths, bins=50, color="#4C8C6B", edgecolor="white")
    plt.xlabel("Processed Word Count")
    plt.ylabel("Number of Documents")
    plt.title("Distribution of Processed Document Lengths")
    max_count = max(counts) if len(counts) else 0
    for count, patch in zip(counts, patches):
        if count == 0:
            continue
        plt.text(
            patch.get_x() + patch.get_width() / 2,
            count + max_count * 0.01,
            f"{int(count):,}",
            ha="center",
            va="bottom",
            fontsize=6,
        )
    plt.ylim(0, max_count * 1.18 if max_count else 1)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "doc_length_distribution.png"), dpi=200)
    plt.close()


def save_before_after_examples(docs, sample_size=10):
    examples = []

    with open(ABSTRACTS_CLEANED, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for idx, row in enumerate(reader):
            if idx >= sample_size or idx >= len(docs):
                break
            original = row[0] if row else ""
            processed = docs[idx]
            examples.append((idx, original, processed))

    with open(os.path.join(OUTPUT_DIR, "before_after_examples.csv"), "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["doc_index", "cleaned_abstract", "processed_text"])
        writer.writerows(examples)

    with open(os.path.join(OUTPUT_DIR, "before_after_examples.md"), "w", encoding="utf-8") as f:
        f.write("# Before and After Preprocessing Examples\n\n")
        for idx, original, processed in examples:
            f.write(f"## Document {idx}\n\n")
            f.write("**Cleaned abstract sample**\n\n")
            f.write(original[:700].replace("\n", " ") + "\n\n")
            f.write("**Processed text sample**\n\n")
            f.write(processed[:700].replace("\n", " ") + "\n\n")


def main():
    ensure_output_dir()

    docs = load_processed_docs()
    vocab_size = load_vocabulary_size()
    total_counts, nonzero_count = parse_count_matrix()

    summary, doc_lengths = save_summary(docs, vocab_size, nonzero_count)
    save_top_words(total_counts, top_n=30)
    save_doc_length_distribution(doc_lengths)
    save_before_after_examples(docs, sample_size=10)

    print("Preprocessing statistics generated.")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Documents: {summary['document_count']}")
    print(f"Vocabulary size: {summary['vocabulary_size']}")
    print(f"Nonzero elements: {summary['nonzero_elements']}")
    print(f"Sparsity: {summary['sparsity']:.6f}")


if __name__ == "__main__":
    main()
