import csv
import json
import math
import os
import shutil

import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import LatentDirichletAllocation

from topic_modeling_lda import (
    get_topic_words,
    load_inputs,
    save_document_topics,
    save_summary,
    save_topic_prevalence,
    save_topic_word_plot,
    save_topic_words,
)


CANDIDATE_KS = [1, 2, 3, 4] + list(range(5, 51, 5))
MIN_FINAL_K = 5
OUTPUT_ROOT = "output"
SELECTION_DIR = os.path.join(OUTPUT_ROOT, "lda_k_selection")
TOP_N = 15
TOP_DOCS = 5
MAX_ITER_SELECTION = 30
MAX_ITER_FINAL = 50
SEED = 100


def safe_remove_lda_dirs(best_k=None):
    root = os.path.abspath(OUTPUT_ROOT)
    if not os.path.isdir(root):
        return

    for name in os.listdir(root):
        if not name.startswith("lda_k"):
            continue
        if name == "lda_k_selection":
            continue
        if best_k is not None and name == f"lda_k{best_k}":
            continue
        path = os.path.abspath(os.path.join(root, name))
        if os.path.isdir(path) and os.path.dirname(path) == root:
            shutil.rmtree(path)


def topic_diversity(model, top_n):
    top_words = []
    for weights in model.components_:
        top_indices = np.argsort(weights)[::-1][:top_n]
        top_words.extend(top_indices.tolist())
    if not top_words:
        return 0
    return len(set(top_words)) / len(top_words)


def topic_exclusivity(model, top_n):
    topic_word = model.components_ / model.components_.sum(axis=1, keepdims=True)
    word_total = topic_word.sum(axis=0, keepdims=True)
    exclusivity = topic_word / np.maximum(word_total, 1e-12)

    scores = []
    for topic_idx, weights in enumerate(model.components_):
        top_indices = np.argsort(weights)[::-1][:top_n]
        scores.extend(exclusivity[topic_idx, top_indices].tolist())
    return float(np.mean(scores)) if scores else 0


def umass_coherence(model, binary_matrix, doc_freq, top_n):
    scores = []
    topic_count = model.components_.shape[0]

    for topic_idx in range(topic_count):
        top_indices = np.argsort(model.components_[topic_idx])[::-1][:top_n]
        pair_scores = []
        for m in range(1, len(top_indices)):
            word_m = top_indices[m]
            docs_m = binary_matrix[:, word_m]
            for l in range(0, m):
                word_l = top_indices[l]
                docs_l = binary_matrix[:, word_l]
                cooccur = docs_m.multiply(docs_l).sum()
                denom = doc_freq[word_l]
                pair_scores.append(math.log((cooccur + 1) / max(denom, 1)))
        if pair_scores:
            scores.append(float(np.mean(pair_scores)))

    return float(np.mean(scores)) if scores else 0


def npmi_coherence(model, binary_matrix, doc_freq, top_n):
    scores = []
    doc_count = binary_matrix.shape[0]
    eps = 1e-12

    for topic_idx in range(model.components_.shape[0]):
        top_indices = np.argsort(model.components_[topic_idx])[::-1][:top_n]
        pair_scores = []
        for m in range(1, len(top_indices)):
            word_m = top_indices[m]
            docs_m = binary_matrix[:, word_m]
            p_m = doc_freq[word_m] / doc_count
            for l in range(0, m):
                word_l = top_indices[l]
                docs_l = binary_matrix[:, word_l]
                p_l = doc_freq[word_l] / doc_count
                p_ml = docs_m.multiply(docs_l).sum() / doc_count
                if p_ml <= 0:
                    pair_scores.append(-1.0)
                    continue
                pmi = math.log((p_ml + eps) / max(p_m * p_l, eps))
                npmi = pmi / (-math.log(p_ml + eps))
                pair_scores.append(npmi)
        if pair_scores:
            scores.append(float(np.mean(pair_scores)))

    return float(np.mean(scores)) if scores else 0


def topic_separation(model):
    topic_word = model.components_ / model.components_.sum(axis=1, keepdims=True)
    if topic_word.shape[0] < 2:
        return 0.0

    distances = []
    for i in range(topic_word.shape[0]):
        for j in range(i + 1, topic_word.shape[0]):
            p = topic_word[i]
            q = topic_word[j]
            m = 0.5 * (p + q)
            js = 0.5 * np.sum(p * np.log(p / m)) + 0.5 * np.sum(q * np.log(q / m))
            distances.append(math.sqrt(max(js, 0.0)))

    return float(np.mean(distances)) if distances else 0.0


def minmax(values, reverse=False):
    arr = np.array(values, dtype=float)
    if np.allclose(arr.max(), arr.min()):
        scaled = np.ones_like(arr)
    else:
        scaled = (arr - arr.min()) / (arr.max() - arr.min())
    if reverse:
        scaled = 1 - scaled
    return scaled


def choose_best(results):
    eligible = [row for row in results if row["k"] >= MIN_FINAL_K]

    perplexity_scaled = minmax([row["perplexity"] for row in eligible], reverse=True)
    npmi_scaled = minmax([row["coherence_npmi"] for row in eligible])
    exclusivity_scaled = minmax([row["exclusivity"] for row in eligible])
    diversity_scaled = minmax([row["topic_diversity"] for row in eligible])
    separation_scaled = minmax([row["topic_separation"] for row in eligible])

    for i, row in enumerate(eligible):
        row["score"] = float(
            0.35 * npmi_scaled[i]
            + 0.25 * exclusivity_scaled[i]
            + 0.20 * separation_scaled[i]
            + 0.10 * diversity_scaled[i]
            + 0.10 * perplexity_scaled[i]
        )

    for row in results:
        if row["k"] < MIN_FINAL_K:
            row["score"] = None

    return max(eligible, key=lambda row: row["score"])


def save_selection_outputs(results, best):
    os.makedirs(SELECTION_DIR, exist_ok=True)

    csv_path = os.path.join(SELECTION_DIR, "lda_k_selection_metrics.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "k",
            "status",
            "perplexity",
            "coherence_umass",
            "coherence_npmi",
            "exclusivity",
            "topic_diversity",
            "topic_separation",
            "mean_max_topic_probability",
            "score",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow({key: row[key] for key in fieldnames})

    with open(os.path.join(SELECTION_DIR, "best_k.json"), "w", encoding="utf-8-sig") as f:
        json.dump(best, f, indent=2, ensure_ascii=False)

    with open(os.path.join(SELECTION_DIR, "best_k.md"), "w", encoding="utf-8-sig") as f:
        f.write("# LDA K Selection Result\n\n")
        f.write(f"Best K: **{best['k']}**\n\n")
        f.write("K=1, K=2, K=3, and K=4 are kept as coarse-reference models only. They are useful for checking whether the corpus has broad splits, but they are not eligible for the final choice because the project needs several interpretable topics rather than one or two overly broad groups.\n\n")
        f.write("For eligible models (K >= 5), the final K is selected by a composite score:\n\n")
        f.write(
            "`0.35 * NPMI coherence + 0.25 * exclusivity + 0.20 * topic separation + 0.10 * topic diversity + 0.10 * inverse perplexity`\n\n"
        )
        f.write("Topic diversity is not expected to increase monotonically with K. It measures the proportion of unique words among all topic top words, so it can go up or down depending on how much the top-word lists overlap.\n\n")
        f.write("| K | Status | Perplexity | UMass | NPMI | Exclusivity | Diversity | Separation | Mean Max Topic Prob. | Score |\n")
        f.write("|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for row in results:
            score_text = "" if row["score"] is None else f"{row['score']:.4f}"
            f.write(
                f"| {row['k']} | {row['status']} | {row['perplexity']:.4f} | {row['coherence_umass']:.4f} | "
                f"{row['coherence_npmi']:.4f} | {row['exclusivity']:.4f} | {row['topic_diversity']:.4f} | "
                f"{row['topic_separation']:.4f} | {row['mean_max_topic_probability']:.4f} | {score_text} |\n"
            )

    plot_metric(results, "perplexity", "Perplexity", "lda_k_perplexity.png", lower_is_better=True)
    plot_metric(results, "coherence_umass", "UMass Coherence", "lda_k_coherence.png")
    plot_metric(results, "coherence_npmi", "NPMI Coherence", "lda_k_npmi_coherence.png")
    plot_metric(results, "exclusivity", "Exclusivity", "lda_k_exclusivity.png")
    plot_metric(results, "topic_diversity", "Topic Diversity", "lda_k_topic_diversity.png")
    plot_metric(results, "topic_separation", "Topic Separation", "lda_k_topic_separation.png")
    plot_metric(results, "score", "Composite Score", "lda_k_composite_score.png")


def plot_metric(results, key, title, filename, lower_is_better=False):
    ks = [row["k"] for row in results]
    values = [np.nan if row[key] is None else row[key] for row in results]

    plt.figure(figsize=(9, 5))
    plt.plot(ks, values, marker="o", color="#365F91")
    for k, value in zip(ks, values):
        if np.isnan(value):
            continue
        label = f"{value:.2f}" if abs(value) >= 10 else f"{value:.3f}"
        plt.text(k, value, label, ha="center", va="bottom", fontsize=8)
    plt.xlabel("Number of Topics (K)")
    suffix = "Lower is better" if lower_is_better else "Higher is better"
    plt.ylabel(f"{title} ({suffix})")
    plt.title(f"LDA K Selection: {title}")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(os.path.join(SELECTION_DIR, filename), dpi=200)
    plt.close()


def save_best_model_outputs(model, doc_topic, matrix, vocabulary, docs, best_k):
    output_dir = os.path.join(OUTPUT_ROOT, f"lda_k{best_k}")
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    topic_rows = get_topic_words(model, vocabulary, TOP_N)
    save_topic_words(topic_rows, output_dir, best_k, TOP_N)
    save_topic_word_plot(topic_rows, output_dir, best_k, TOP_N)
    save_document_topics(doc_topic, docs, output_dir, best_k, TOP_DOCS)
    save_topic_prevalence(doc_topic, output_dir, best_k)
    save_summary(model, matrix, doc_topic, output_dir, best_k, TOP_N)


def train_lda(matrix, k, max_iter):
    model = LatentDirichletAllocation(
        n_components=k,
        max_iter=max_iter,
        learning_method="batch",
        random_state=SEED,
        evaluate_every=0,
        n_jobs=-1,
    )
    doc_topic = model.fit_transform(matrix)
    return model, doc_topic


def main():
    safe_remove_lda_dirs()
    os.makedirs(SELECTION_DIR, exist_ok=True)

    matrix, vocabulary, docs = load_inputs()
    binary_matrix = matrix.copy()
    binary_matrix.data = np.ones_like(binary_matrix.data)
    doc_freq = np.asarray(binary_matrix.sum(axis=0)).ravel()

    results = []
    trained = {}

    for k in CANDIDATE_KS:
        print(f"Training LDA K={k}...")
        model, doc_topic = train_lda(matrix, k, MAX_ITER_SELECTION)
        result = {
            "k": k,
            "status": "eligible" if k >= MIN_FINAL_K else "coarse_reference",
            "perplexity": float(model.perplexity(matrix)),
            "coherence_umass": umass_coherence(model, binary_matrix, doc_freq, TOP_N),
            "coherence_npmi": npmi_coherence(model, binary_matrix, doc_freq, TOP_N),
            "exclusivity": topic_exclusivity(model, TOP_N),
            "topic_diversity": topic_diversity(model, TOP_N),
            "topic_separation": topic_separation(model),
            "mean_max_topic_probability": float(np.max(doc_topic, axis=1).mean()),
        }
        results.append(result)
        trained[k] = (model, doc_topic)
        print(
            f"K={k}: perplexity={result['perplexity']:.2f}, "
            f"npmi={result['coherence_npmi']:.4f}, "
            f"exclusivity={result['exclusivity']:.4f}, "
            f"diversity={result['topic_diversity']:.4f}, "
            f"separation={result['topic_separation']:.4f}"
        )

    best = choose_best(results)
    save_selection_outputs(results, best)

    best_k = best["k"]
    print(f"Best K by composite score: {best_k}")
    print(f"Retraining final LDA K={best_k} with max_iter={MAX_ITER_FINAL}...")
    final_model, final_doc_topic = train_lda(matrix, best_k, MAX_ITER_FINAL)
    save_best_model_outputs(final_model, final_doc_topic, matrix, vocabulary, docs, best_k)

    safe_remove_lda_dirs(best_k=best_k)
    print(f"Final best model outputs saved to output/lda_k{best_k}")
    print(f"K selection metrics saved to {SELECTION_DIR}")


if __name__ == "__main__":
    main()
