import csv
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform


K = 15
LDA_DIR = Path("output") / f"lda_k{K}"
OUT_DIR = LDA_DIR / "topic_visualizations"

TOPIC_WORDS = LDA_DIR / f"lda_k{K}_topic_words.csv"
DOC_TOPIC = LDA_DIR / f"lda_k{K}_doc_topic_distribution.csv"
DOMINANT_TOPICS = LDA_DIR / f"lda_k{K}_dominant_topics.csv"
PREVALENCE = LDA_DIR / f"lda_k{K}_topic_prevalence.csv"


TOPIC_LABELS = {
    1: "Online learning design",
    2: "STEM engineering",
    3: "Teacher development",
    4: "Lab science",
    5: "Self-regulation",
    6: "Achievement testing",
    7: "Clinical health",
    8: "Academic pathways",
    9: "Language literacy",
    10: "Health gender society",
    11: "Critical thinking",
    12: "Peer review",
    13: "Measurement methods",
    14: "Residency surgery",
    15: "International education",
}


def ensure_output_dir():
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def topic_tick_labels():
    return [f"T{i}\n{TOPIC_LABELS[i]}" for i in range(1, K + 1)]


def load_doc_topic():
    df = pd.read_csv(DOC_TOPIC, encoding="utf-8-sig")
    topic_cols = [f"topic_{i}" for i in range(1, K + 1)]
    return df, topic_cols


def save_top_words_facets(top_n=10):
    words = pd.read_csv(TOPIC_WORDS, encoding="utf-8-sig")
    words = words[words["rank"] <= top_n].copy()

    fig, axes = plt.subplots(5, 3, figsize=(16, 22))
    axes = axes.ravel()

    for topic in range(1, K + 1):
        ax = axes[topic - 1]
        data = words[words["topic"] == topic].sort_values("probability")
        bars = ax.barh(data["word"], data["probability"], color="#4E79A7")
        ax.set_title(f"Topic {topic}: {TOPIC_LABELS[topic]}", fontsize=11)
        ax.set_xlabel("Probability")
        max_value = data["probability"].max()
        for bar, value in zip(bars, data["probability"]):
            ax.text(
                bar.get_width() + max_value * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.3f}",
                va="center",
                fontsize=7,
            )
        ax.set_xlim(0, max_value * 1.25)

    plt.tight_layout()
    plt.savefig(OUT_DIR / "topic_top_words_facets.png", dpi=220)
    plt.close()


def save_topic_correlation_heatmap(doc_topic, topic_cols):
    corr = doc_topic[topic_cols].corr()
    corr.to_csv(OUT_DIR / "topic_correlation_matrix.csv", encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(13, 11))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(np.arange(K))
    ax.set_yticks(np.arange(K))
    ax.set_xticklabels(topic_tick_labels(), rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(topic_tick_labels(), fontsize=8)

    for i in range(K):
        for j in range(K):
            value = corr.values[i, j]
            color = "white" if abs(value) > 0.55 else "black"
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=7, color=color)

    ax.set_title("Topic Correlation Heatmap")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Pearson correlation")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "topic_correlation_heatmap.png", dpi=220)
    plt.close()

    return corr


def save_topic_dendrogram(corr):
    distance = 1 - corr.values
    np.fill_diagonal(distance, 0)
    distance = np.clip(distance, 0, None)
    condensed = squareform(distance, checks=False)
    linked = linkage(condensed, method="average")

    plt.figure(figsize=(13, 7))
    dendrogram(
        linked,
        labels=topic_tick_labels(),
        leaf_rotation=45,
        leaf_font_size=8,
        color_threshold=None,
    )
    plt.title("Topic Clustering Dendrogram")
    plt.ylabel("Distance: 1 - correlation")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "topic_clustering_dendrogram.png", dpi=220)
    plt.close()


def save_document_topic_heatmap(doc_topic, topic_cols, sample_size=500):
    plot_df = doc_topic.copy()
    plot_df["dominant_topic"] = plot_df[topic_cols].idxmax(axis=1).str.replace("topic_", "").astype(int)
    plot_df["dominant_probability"] = plot_df[topic_cols].max(axis=1)
    plot_df = plot_df.sort_values(["dominant_topic", "dominant_probability"], ascending=[True, False])
    sample = plot_df.head(min(sample_size, len(plot_df)))

    matrix = sample[topic_cols].to_numpy()
    fig, ax = plt.subplots(figsize=(13, 8))
    im = ax.imshow(matrix, aspect="auto", cmap="YlGnBu", vmin=0, vmax=matrix.max())
    ax.set_xticks(np.arange(K))
    ax.set_xticklabels(topic_tick_labels(), rotation=45, ha="right", fontsize=8)
    ax.set_ylabel(f"Documents, sorted by dominant topic (first {len(sample)})")
    ax.set_title("Document-Topic Distribution Heatmap")
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02, label="Topic proportion")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "document_topic_heatmap_sample.png", dpi=220)
    plt.close()


def save_dominant_topic_distribution():
    dom = pd.read_csv(DOMINANT_TOPICS, encoding="utf-8-sig")
    counts = dom["dominant_topic"].value_counts().sort_index()

    with open(OUT_DIR / "dominant_topic_counts.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["topic", "document_count"])
        for topic in range(1, K + 1):
            writer.writerow([topic, int(counts.get(topic, 0))])

    labels = [f"T{i}" for i in range(1, K + 1)]
    values = [counts.get(i, 0) for i in range(1, K + 1)]
    plt.figure(figsize=(11, 5))
    bars = plt.bar(labels, values, color="#59A14F")
    plt.xlabel("Dominant Topic")
    plt.ylabel("Number of Documents")
    plt.title("Dominant Topic Distribution Across Documents")
    max_value = max(values) if values else 0
    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            value + max_value * 0.01,
            f"{int(value):,}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    plt.ylim(0, max_value * 1.18 if max_value else 1)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "dominant_topic_distribution.png", dpi=220)
    plt.close()


def save_topic_prevalence_plot():
    prevalence = pd.read_csv(PREVALENCE, encoding="utf-8-sig")
    labels = [f"T{int(topic)}" for topic in prevalence["topic"]]
    values = prevalence["mean_document_proportion"].to_numpy()

    plt.figure(figsize=(11, 5))
    bars = plt.bar(labels, values, color="#F28E2B")
    plt.xlabel("Topic")
    plt.ylabel("Mean Topic Proportion")
    plt.title("Average Topic Prevalence")
    max_value = max(values) if len(values) else 0
    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            value + max_value * 0.01,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    plt.ylim(0, max_value * 1.20 if max_value else 1)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "topic_prevalence_bar.png", dpi=220)
    plt.close()


def save_trend_note():
    note = (
        "# Topic Trend Analysis\n\n"
        "No topic trend plot was generated because the current dataset only provides abstract text. "
        "There is no reliable year, publication date, or time variable in `abstracts.csv`. "
        "If a year column is added later, topic proportions from "
        f"`output/lda_k{K}/lda_k{K}_doc_topic_distribution.csv` can be aggregated by year to produce trend plots.\n"
    )
    (OUT_DIR / "trend_analysis_note.md").write_text(note, encoding="utf-8-sig")


def save_visualization_index():
    index = f"""# Topic Visualization Outputs

Final model: LDA, K={K}

Generated files:

| File | Description |
|---|---|
| `topic_top_words_facets.png` | Top words for each topic |
| `topic_correlation_heatmap.png` | Pearson correlation heatmap among topic proportions |
| `topic_correlation_matrix.csv` | Numeric topic correlation matrix |
| `topic_clustering_dendrogram.png` | Hierarchical clustering of topics based on 1 - correlation |
| `document_topic_heatmap_sample.png` | Document-topic distribution heatmap for a sorted sample of documents |
| `dominant_topic_distribution.png` | Number of documents dominated by each topic |
| `dominant_topic_counts.csv` | Numeric dominant-topic counts |
| `topic_prevalence_bar.png` | Average topic prevalence across all documents |
| `trend_analysis_note.md` | Explanation for why no trend plot is generated |
"""
    (OUT_DIR / "README.md").write_text(index, encoding="utf-8-sig")


def main():
    ensure_output_dir()
    doc_topic, topic_cols = load_doc_topic()

    save_top_words_facets(top_n=10)
    corr = save_topic_correlation_heatmap(doc_topic, topic_cols)
    save_topic_dendrogram(corr)
    save_document_topic_heatmap(doc_topic, topic_cols, sample_size=500)
    save_dominant_topic_distribution()
    save_topic_prevalence_plot()
    save_trend_note()
    save_visualization_index()

    print(f"Topic visualizations saved to {OUT_DIR}")


if __name__ == "__main__":
    main()
