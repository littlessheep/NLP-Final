import argparse
import csv
import json
import os

import matplotlib.pyplot as plt
import numpy as np
from scipy import sparse
from sklearn.decomposition import LatentDirichletAllocation


COUNT_MATRIX = os.path.join("output", "count_matrix.npz")
VOCABULARY_JSON = os.path.join("output", "vocabulary.json")
PROCESSED_DOCS = os.path.join("output", "processed_docs.txt")


def load_inputs():
    count_matrix = sparse.load_npz(COUNT_MATRIX)
    with open(VOCABULARY_JSON, "r", encoding="utf-8") as f:
        vocabulary = np.array(json.load(f))
    with open(PROCESSED_DOCS, "r", encoding="utf-8") as f:
        docs = [line.strip() for line in f]
    return count_matrix, vocabulary, docs


def get_topic_words(model, vocabulary, top_n):
    topic_rows = []
    for topic_idx, topic_weights in enumerate(model.components_):
        top_indices = np.argsort(topic_weights)[::-1][:top_n]
        total_weight = topic_weights.sum()
        for rank, term_idx in enumerate(top_indices, start=1):
            weight = topic_weights[term_idx]
            probability = weight / total_weight if total_weight else 0
            topic_rows.append(
                {
                    "topic": topic_idx + 1,
                    "rank": rank,
                    "word": vocabulary[term_idx],
                    "weight": weight,
                    "probability": probability,
                }
            )
    return topic_rows


def save_topic_words(topic_rows, output_dir, k, top_n):
    csv_path = os.path.join(output_dir, f"lda_k{k}_topic_words.csv")
    md_path = os.path.join(output_dir, f"lda_k{k}_topic_words.md")

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["topic", "rank", "word", "weight", "probability"],
        )
        writer.writeheader()
        writer.writerows(topic_rows)

    by_topic = {}
    for row in topic_rows:
        by_topic.setdefault(row["topic"], []).append(row)

    with open(md_path, "w", encoding="utf-8-sig") as f:
        f.write(f"# LDA Topic Words, K={k}\n\n")
        for topic in range(1, k + 1):
            rows = by_topic.get(topic, [])
            words = ", ".join(row["word"] for row in rows)
            f.write(f"## Topic {topic}\n\n")
            f.write(f"Top {top_n} words: {words}\n\n")
            f.write("| Rank | Word | Probability |\n")
            f.write("|---:|---|---:|\n")
            for row in rows:
                f.write(f"| {row['rank']} | {row['word']} | {row['probability']:.6f} |\n")
            f.write("\n")


def save_topic_word_plot(topic_rows, output_dir, k, top_n):
    by_topic = {}
    for row in topic_rows:
        by_topic.setdefault(row["topic"], []).append(row)

    fig, axes = plt.subplots(k, 1, figsize=(10, max(2.2 * k, 8)))
    if k == 1:
        axes = [axes]

    for topic, ax in zip(range(1, k + 1), axes):
        rows = by_topic.get(topic, [])[:top_n]
        words = [row["word"] for row in reversed(rows)]
        probs = [row["probability"] for row in reversed(rows)]
        bars = ax.barh(words, probs, color="#5B7DB1")
        ax.set_title(f"Topic {topic}")
        ax.set_xlabel("Word Probability")
        max_prob = max(probs) if probs else 0
        for bar, prob in zip(bars, probs):
            ax.text(
                bar.get_width() + max_prob * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{prob:.4f}",
                va="center",
                fontsize=8,
            )
        ax.set_xlim(0, max_prob * 1.22 if max_prob else 1)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"lda_k{k}_topic_words.png"), dpi=200)
    plt.close()


def save_document_topics(doc_topic, docs, output_dir, k, top_doc_n):
    doc_topic_path = os.path.join(output_dir, f"lda_k{k}_doc_topic_distribution.csv")
    dominant_path = os.path.join(output_dir, f"lda_k{k}_dominant_topics.csv")
    representatives_path = os.path.join(output_dir, f"lda_k{k}_representative_docs.md")

    topic_columns = [f"topic_{i}" for i in range(1, k + 1)]
    with open(doc_topic_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["doc_index"] + topic_columns)
        for idx, row in enumerate(doc_topic):
            writer.writerow([idx] + [f"{value:.8f}" for value in row])

    dominant_topics = np.argmax(doc_topic, axis=1) + 1
    dominant_probs = np.max(doc_topic, axis=1)
    with open(dominant_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["doc_index", "dominant_topic", "dominant_topic_probability"])
        for idx, (topic, prob) in enumerate(zip(dominant_topics, dominant_probs)):
            writer.writerow([idx, topic, f"{prob:.8f}"])

    with open(representatives_path, "w", encoding="utf-8-sig") as f:
        f.write(f"# Representative Documents, LDA K={k}\n\n")
        for topic in range(1, k + 1):
            scores = doc_topic[:, topic - 1]
            top_indices = np.argsort(scores)[::-1][:top_doc_n]
            f.write(f"## Topic {topic}\n\n")
            for rank, doc_idx in enumerate(top_indices, start=1):
                sample = docs[doc_idx][:700]
                f.write(
                    f"### Rank {rank}: Document {doc_idx}, probability {scores[doc_idx]:.6f}\n\n"
                )
                f.write(sample + "\n\n")


def save_topic_prevalence(doc_topic, output_dir, k):
    prevalence = doc_topic.mean(axis=0)
    csv_path = os.path.join(output_dir, f"lda_k{k}_topic_prevalence.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["topic", "mean_document_proportion"])
        for topic, value in enumerate(prevalence, start=1):
            writer.writerow([topic, f"{value:.8f}"])

    plt.figure(figsize=(9, 5))
    topics = [f"Topic {i}" for i in range(1, k + 1)]
    bars = plt.bar(topics, prevalence, color="#4C8C6B")
    plt.xlabel("Topic")
    plt.ylabel("Mean Document Proportion")
    plt.title(f"LDA Topic Prevalence, K={k}")
    max_value = max(prevalence) if len(prevalence) else 0
    for bar, value in zip(bars, prevalence):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            value + max_value * 0.01,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    plt.ylim(0, max_value * 1.18 if max_value else 1)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"lda_k{k}_topic_prevalence.png"), dpi=200)
    plt.close()


def save_summary(model, matrix, doc_topic, output_dir, k, top_n):
    summary = {
        "model": "LatentDirichletAllocation",
        "k": k,
        "top_words_per_topic": top_n,
        "document_count": int(matrix.shape[0]),
        "vocabulary_size": int(matrix.shape[1]),
        "max_iter": int(model.max_iter),
        "learning_method": model.learning_method,
        "random_state": model.random_state,
        "perplexity": float(model.perplexity(matrix)),
        "mean_max_topic_probability": float(np.max(doc_topic, axis=1).mean()),
    }

    with open(os.path.join(output_dir, f"lda_k{k}_summary.json"), "w", encoding="utf-8-sig") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(os.path.join(output_dir, f"lda_k{k}_summary.md"), "w", encoding="utf-8-sig") as f:
        f.write(f"# LDA Model Summary, K={k}\n\n")
        f.write("| Metric | Value |\n")
        f.write("|---|---:|\n")
        for key, value in summary.items():
            f.write(f"| {key} | {value} |\n")


def main():
    parser = argparse.ArgumentParser(description="Train an LDA topic model on the count matrix.")
    parser.add_argument("--k", type=int, default=10, help="Number of topics.")
    parser.add_argument("--top-n", type=int, default=15, help="Top words to export for each topic.")
    parser.add_argument("--top-docs", type=int, default=5, help="Representative documents per topic.")
    parser.add_argument("--max-iter", type=int, default=50, help="Maximum LDA iterations.")
    parser.add_argument("--seed", type=int, default=100, help="Random seed.")
    args = parser.parse_args()

    output_dir = os.path.join("output", f"lda_k{args.k}")
    os.makedirs(output_dir, exist_ok=True)

    count_matrix, vocabulary, docs = load_inputs()
    model = LatentDirichletAllocation(
        n_components=args.k,
        max_iter=args.max_iter,
        learning_method="batch",
        random_state=args.seed,
        evaluate_every=0,
        n_jobs=-1,
    )

    doc_topic = model.fit_transform(count_matrix)
    topic_rows = get_topic_words(model, vocabulary, args.top_n)

    save_topic_words(topic_rows, output_dir, args.k, args.top_n)
    save_topic_word_plot(topic_rows, output_dir, args.k, args.top_n)
    save_document_topics(doc_topic, docs, output_dir, args.k, args.top_docs)
    save_topic_prevalence(doc_topic, output_dir, args.k)
    save_summary(model, count_matrix, doc_topic, output_dir, args.k, args.top_n)

    print(f"LDA topic model finished. K={args.k}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
