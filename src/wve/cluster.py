"""Clustering of extracted themes using sentence embeddings."""

from datetime import datetime

import numpy as np

from wve.models import Cluster, ClusterMember, ClusterResult, Extraction


def get_embeddings(
    terms: list[str],
    model_name: str = "all-MiniLM-L6-v2",
) -> np.ndarray:
    """Generate embeddings for a list of terms.

    Args:
        terms: List of terms/phrases to embed
        model_name: Sentence-transformers model name

    Returns:
        NumPy array of embeddings (n_terms x embedding_dim)
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    embeddings = model.encode(terms, show_progress_bar=False)
    return np.array(embeddings)


def find_optimal_k(
    embeddings: np.ndarray,
    k_range: tuple[int, int] = (2, 10),
) -> int:
    """Find optimal number of clusters using silhouette score.

    Args:
        embeddings: Term embeddings
        k_range: (min_k, max_k) range to search

    Returns:
        Optimal k value
    """
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    n_samples = len(embeddings)
    max_k = min(k_range[1], n_samples - 1)
    min_k = max(k_range[0], 2)

    if max_k < min_k:
        return min_k

    best_k = min_k
    best_score = -1

    for k in range(min_k, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels)
        if score > best_score:
            best_score = score
            best_k = k

    return best_k


def cluster_terms(
    terms: list[str],
    n_clusters: int = 0,
    model_name: str = "all-MiniLM-L6-v2",
) -> ClusterResult:
    """Cluster terms into conceptual groups.

    Args:
        terms: List of terms/phrases to cluster
        n_clusters: Number of clusters (0 = auto-detect)
        model_name: Embedding model name

    Returns:
        ClusterResult with labeled clusters
    """
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    if len(terms) < 3:
        return ClusterResult(
            clusters=[],
            unclustered=terms,
            silhouette_score=0.0,
            embedding_model=model_name,
        )

    # Generate embeddings
    embeddings = get_embeddings(terms, model_name)

    # Determine k
    if n_clusters <= 0:
        n_clusters = find_optimal_k(embeddings)

    n_clusters = min(n_clusters, len(terms) - 1)

    # Perform clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)

    # Calculate silhouette score
    sil_score = silhouette_score(embeddings, labels) if len(set(labels)) > 1 else 0.0

    # Build clusters
    clusters: list[Cluster] = []
    for cluster_id in range(n_clusters):
        mask = labels == cluster_id
        cluster_indices = np.where(mask)[0]

        if len(cluster_indices) == 0:
            continue

        cluster_embeddings = embeddings[mask]
        centroid = kmeans.cluster_centers_[cluster_id]

        # Calculate distances to centroid
        distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)

        # Sort by distance (closest first)
        sorted_indices = np.argsort(distances)
        members = [
            ClusterMember(
                term=terms[cluster_indices[i]],
                distance=float(distances[i]),
            )
            for i in sorted_indices
        ]

        # Generate label from closest terms
        centroid_terms = [m.term for m in members[:3]]
        label = " / ".join(centroid_terms[:2]) if len(centroid_terms) >= 2 else centroid_terms[0]

        # Coherence: inverse of average distance
        coherence = 1.0 / (1.0 + float(np.mean(distances)))

        clusters.append(
            Cluster(
                id=cluster_id,
                label=label,
                centroid_terms=centroid_terms,
                members=members,
                coherence=coherence,
            )
        )

    # Sort clusters by coherence
    clusters.sort(key=lambda c: c.coherence, reverse=True)

    return ClusterResult(
        clusters=clusters,
        unclustered=[],
        silhouette_score=float(sil_score),
        embedding_model=model_name,
    )


def cluster_extraction(
    extraction: Extraction,
    n_clusters: int = 0,
    model_name: str = "all-MiniLM-L6-v2",
) -> ClusterResult:
    """Cluster terms from an Extraction result.

    Combines keywords, TF-IDF terms, and phrases for clustering.
    """
    terms: list[str] = []

    # Add keywords
    for kw in extraction.keywords:
        if kw.term not in terms:
            terms.append(kw.term)

    # Add TF-IDF terms
    for tf in extraction.tfidf:
        if tf.term not in terms:
            terms.append(tf.term)

    # Add phrases
    for ph in extraction.phrases:
        if ph.phrase not in terms:
            terms.append(ph.phrase)

    return cluster_terms(terms, n_clusters, model_name)


def save_clusters(clusters: ClusterResult, output_path: str) -> None:
    """Save cluster results to JSON."""
    with open(output_path, "w") as f:
        f.write(clusters.model_dump_json(indent=2))


def load_clusters(input_path: str) -> ClusterResult:
    """Load cluster results from JSON."""
    with open(input_path) as f:
        return ClusterResult.model_validate_json(f.read())
