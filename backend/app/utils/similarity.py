"""
TF-IDF based text similarity utilities.

Why TF-IDF instead of embeddings?
  - Runs locally on the Celery worker — no external API call or cost.
  - Processes 300 submissions in < 1 second on modest hardware.
  - Sufficient for flagging obvious copy-paste (> 80% match).
  - scikit-learn is already a project dependency.
"""
from typing import List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_similarity_scores(
    target: str,
    candidates: List[str],
) -> List[float]:
    """
    Returns cosine-similarity scores between `target` and each candidate,
    using TF-IDF vectors built on the joint corpus.

    Args:
        target:     The submission text to check.
        candidates: Other submission texts in the same assignment.

    Returns:
        A list of floats in [0, 1], one per candidate.
        Empty list if candidates is empty.
    """
    if not candidates:
        return []

    corpus = [target] + candidates
    vectorizer = TfidfVectorizer(
        strip_accents="unicode",
        analyzer="word",
        ngram_range=(1, 2),   # Unigrams + bigrams to catch phrase-level copying
        min_df=1,
        sublinear_tf=True,    # log(1 + tf) dampens very frequent terms
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Row 0 is target; rows 1..N are candidates
    scores = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1:]).flatten()
    return scores.tolist()


def find_highest_match(
    target: str,
    candidates: List[Tuple[str, str]],
    threshold: float = 0.80,
) -> Tuple[float, Optional[str]]:
    """
    Finds the most similar candidate above the plagiarism threshold.

    Args:
        target:     Text of the submission being checked.
        candidates: List of (submission_id, content) tuples.
        threshold:  Cosine similarity above which we flag plagiarism.

    Returns:
        (best_score, matching_submission_id) or (best_score, None) if no
        match exceeds the threshold.
    """
    if not candidates:
        return 0.0, None

    texts = [c[1] for c in candidates]
    scores = compute_similarity_scores(target, texts)

    best_score = max(scores) if scores else 0.0
    if best_score >= threshold:
        best_idx = scores.index(best_score)
        return best_score, candidates[best_idx][0]

    return best_score, None
