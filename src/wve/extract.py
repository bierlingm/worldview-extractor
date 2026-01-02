"""Theme and keyword extraction from transcripts."""

import re
from collections import Counter
from pathlib import Path

from wve.models import (
    CoOccurrence,
    ExtractedEntity,
    ExtractedKeyword,
    ExtractedPhrase,
    Extraction,
    TfidfTerm,
)


def extract_keywords_yake(
    texts: list[str],
    source_ids: list[str],
    top_n: int = 50,
    language: str = "en",
    max_ngram: int = 3,
) -> list[ExtractedKeyword]:
    """Extract keywords using YAKE (unsupervised keyword extraction).

    Args:
        texts: List of transcript texts
        source_ids: Corresponding source identifiers
        top_n: Number of keywords to return
        language: Language code
        max_ngram: Maximum n-gram size

    Returns:
        List of extracted keywords with scores
    """
    import yake

    kw_extractor = yake.KeywordExtractor(
        lan=language,
        n=max_ngram,
        dedupLim=0.7,
        top=top_n * 2,  # Extract more, then aggregate
        features=None,
    )

    # Aggregate keywords across all texts
    keyword_scores: dict[str, list[float]] = {}
    keyword_sources: dict[str, set[str]] = {}

    for text, source_id in zip(texts, source_ids):
        keywords = kw_extractor.extract_keywords(text)
        for kw, score in keywords:
            kw_lower = kw.lower()
            if kw_lower not in keyword_scores:
                keyword_scores[kw_lower] = []
                keyword_sources[kw_lower] = set()
            keyword_scores[kw_lower].append(score)
            keyword_sources[kw_lower].add(source_id)

    # Compute average score and create results
    results = []
    for term, scores in keyword_scores.items():
        avg_score = sum(scores) / len(scores)
        results.append(
            ExtractedKeyword(
                term=term,
                score=avg_score,
                frequency=len(scores),
                sources=list(keyword_sources[term]),
            )
        )

    # YAKE: lower score = more relevant
    results.sort(key=lambda x: x.score)
    return results[:top_n]


def extract_entities_spacy(
    texts: list[str],
    source_ids: list[str],
    model: str = "en_core_web_sm",
) -> dict[str, list[ExtractedEntity]]:
    """Extract named entities using spaCy NER.

    Args:
        texts: List of transcript texts
        source_ids: Corresponding source identifiers
        model: spaCy model name

    Returns:
        Dictionary mapping entity types to lists of entities
    """
    import spacy

    try:
        nlp = spacy.load(model)
    except OSError:
        raise RuntimeError(f"spaCy model '{model}' not found. Run: python -m spacy download {model}")

    entity_counts: dict[str, dict[str, int]] = {}
    entity_sources: dict[str, dict[str, set[str]]] = {}

    for text, source_id in zip(texts, source_ids):
        doc = nlp(text)
        for ent in doc.ents:
            label = ent.label_
            text_norm = ent.text.strip()
            if not text_norm:
                continue

            if label not in entity_counts:
                entity_counts[label] = {}
                entity_sources[label] = {}

            if text_norm not in entity_counts[label]:
                entity_counts[label][text_norm] = 0
                entity_sources[label][text_norm] = set()

            entity_counts[label][text_norm] += 1
            entity_sources[label][text_norm].add(source_id)

    results: dict[str, list[ExtractedEntity]] = {}
    for label, counts in entity_counts.items():
        entities = [
            ExtractedEntity(
                text=text,
                label=label,
                frequency=count,
                sources=list(entity_sources[label][text]),
            )
            for text, count in counts.items()
        ]
        entities.sort(key=lambda x: x.frequency, reverse=True)
        results[label] = entities

    return results


def extract_tfidf(
    texts: list[str],
    top_n: int = 50,
    max_features: int = 1000,
) -> list[TfidfTerm]:
    """Extract top TF-IDF terms across the corpus.

    Args:
        texts: List of transcript texts
        top_n: Number of top terms to return
        max_features: Maximum vocabulary size

    Returns:
        List of terms with TF-IDF scores
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    if not texts:
        return []

    # For single document, use simpler settings
    if len(texts) == 1:
        vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words="english",
            ngram_range=(1, 2),
        )
    else:
        vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
        )

    tfidf_matrix = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()

    # Aggregate scores across documents
    scores = tfidf_matrix.sum(axis=0).A1
    term_scores = list(zip(feature_names, scores))
    term_scores.sort(key=lambda x: x[1], reverse=True)

    return [TfidfTerm(term=term, score=float(score)) for term, score in term_scores[:top_n]]


def extract_phrases(
    texts: list[str],
    source_ids: list[str],
    n_range: tuple[int, int] = (2, 4),
    top_n: int = 50,
) -> list[ExtractedPhrase]:
    """Extract frequent n-gram phrases.

    Args:
        texts: List of transcript texts
        source_ids: Corresponding source identifiers
        n_range: (min_n, max_n) for n-gram sizes
        top_n: Number of phrases to return

    Returns:
        List of frequent phrases
    """
    phrase_counts: Counter[str] = Counter()
    phrase_sources: dict[str, set[str]] = {}

    # Simple tokenization
    def tokenize(text: str) -> list[str]:
        return re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())

    for text, source_id in zip(texts, source_ids):
        tokens = tokenize(text)
        for n in range(n_range[0], n_range[1] + 1):
            for i in range(len(tokens) - n + 1):
                phrase = " ".join(tokens[i : i + n])
                phrase_counts[phrase] += 1
                if phrase not in phrase_sources:
                    phrase_sources[phrase] = set()
                phrase_sources[phrase].add(source_id)

    results = [
        ExtractedPhrase(
            phrase=phrase,
            count=count,
            sources=list(phrase_sources[phrase]),
        )
        for phrase, count in phrase_counts.most_common(top_n * 2)
        if count > 1  # Only phrases appearing more than once
    ]

    return results[:top_n]


def extract_cooccurrences(
    texts: list[str],
    window_size: int = 5,
    top_n: int = 50,
) -> list[CoOccurrence]:
    """Extract co-occurring term pairs using sliding window.

    Args:
        texts: List of transcript texts
        window_size: Size of sliding window
        top_n: Number of pairs to return

    Returns:
        List of co-occurring term pairs
    """
    pair_counts: Counter[tuple[str, str]] = Counter()

    def tokenize(text: str) -> list[str]:
        return re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())

    # Common stopwords to filter
    stopwords = {
        "the", "and", "that", "this", "with", "for", "are", "was", "were",
        "been", "have", "has", "had", "will", "would", "could", "should",
        "can", "may", "might", "must", "shall", "into", "from", "about",
        "what", "which", "who", "whom", "when", "where", "why", "how",
        "all", "each", "every", "both", "few", "more", "most", "other",
        "some", "such", "than", "too", "very", "just", "also", "now",
        "only", "then", "there", "here", "these", "those", "their", "your",
        "its", "his", "her", "our", "they", "you", "she", "him", "them",
    }

    for text in texts:
        tokens = [t for t in tokenize(text) if t not in stopwords]
        for i in range(len(tokens) - window_size + 1):
            window = tokens[i : i + window_size]
            for j, t1 in enumerate(window):
                for t2 in window[j + 1 :]:
                    if t1 != t2:
                        pair = tuple(sorted([t1, t2]))
                        pair_counts[pair] += 1

    results = [
        CoOccurrence(pair=pair, count=count)
        for pair, count in pair_counts.most_common(top_n)
    ]

    return results


def extract_all(
    texts: list[str],
    source_ids: list[str] | None = None,
    top_n: int = 50,
    skip_ner: bool = False,
) -> Extraction:
    """Run all extraction methods and combine results.

    Args:
        texts: List of transcript texts
        source_ids: Optional source identifiers (defaults to indices)
        top_n: Number of items per category
        skip_ner: Skip NER if spaCy model unavailable

    Returns:
        Combined extraction results
    """
    if source_ids is None:
        source_ids = [str(i) for i in range(len(texts))]

    # Try NER, skip gracefully if model missing
    entities: dict[str, list[ExtractedEntity]] = {}
    if not skip_ner:
        try:
            entities = extract_entities_spacy(texts, source_ids)
        except RuntimeError:
            pass  # spaCy model not available

    return Extraction(
        keywords=extract_keywords_yake(texts, source_ids, top_n=top_n),
        entities=entities,
        phrases=extract_phrases(texts, source_ids, top_n=top_n),
        tfidf=extract_tfidf(texts, top_n=top_n),
        co_occurrences=extract_cooccurrences(texts, top_n=top_n),
        source_transcripts=source_ids,
    )


def load_transcripts(input_path: str | Path) -> tuple[list[str], list[str]]:
    """Load transcripts from a file or directory.

    Args:
        input_path: Path to transcript file, directory, or manifest.json

    Returns:
        Tuple of (texts, source_ids)
    """
    path = Path(input_path)

    if path.is_file() and path.suffix == ".json":
        # Manifest file
        import json

        with open(path) as f:
            manifest = json.load(f)
        texts = []
        source_ids = []
        for video_id, transcript_path in manifest.get("transcripts", {}).items():
            tp = Path(transcript_path)
            if tp.exists():
                texts.append(tp.read_text())
                source_ids.append(video_id)
        return texts, source_ids

    elif path.is_file():
        # Single transcript
        return [path.read_text()], [path.stem]

    elif path.is_dir():
        # Directory of transcripts
        texts = []
        source_ids = []
        for f in sorted(path.glob("*.txt")):
            texts.append(f.read_text())
            source_ids.append(f.stem)
        return texts, source_ids

    raise ValueError(f"Invalid input path: {input_path}")


def save_extraction(extraction: Extraction, output_path: str) -> None:
    """Save extraction results to JSON."""
    with open(output_path, "w") as f:
        f.write(extraction.model_dump_json(indent=2))
