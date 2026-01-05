"""Worldview synthesis from extracted and clustered data."""

from datetime import datetime
from pathlib import Path

from wve.models import ClusterResult, Extraction, Worldview, WorldviewPoint
from wve.quotes import QuoteCollection, extract_quotes_from_dir


def check_ollama(host: str = "http://localhost:11434") -> bool:
    """Check if Ollama is available and running."""
    try:
        import ollama

        client = ollama.Client(host=host)
        client.list()
        return True
    except Exception:
        return False


def ollama_generate(
    prompt: str,
    model: str = "llama3",
    host: str = "http://localhost:11434",
) -> dict:
    """Generate response from Ollama and parse as JSON."""
    import json

    import ollama

    client = ollama.Client(host=host)
    response = client.generate(model=model, prompt=prompt, format="json")

    try:
        return json.loads(response["response"])
    except (json.JSONDecodeError, KeyError):
        return {}


def synthesize_quick(
    clusters: ClusterResult,
    extraction: Extraction | None = None,
    subject: str = "",
    n_points: int = 3,
) -> Worldview:
    """Quick synthesis using cluster labels only (no LLM).

    Args:
        clusters: Clustered terms
        extraction: Optional extraction data for additional context
        subject: Name of the person being analyzed
        n_points: Number of worldview points to generate

    Returns:
        Worldview with synthesized points
    """
    points: list[WorldviewPoint] = []

    # Sort clusters by coherence * member count (impact score)
    sorted_clusters = sorted(
        clusters.clusters,
        key=lambda c: c.coherence * len(c.members),
        reverse=True,
    )

    for cluster in sorted_clusters[:n_points]:
        # Generate point from cluster label and top terms
        point_text = cluster.label.replace(" / ", " and ")
        if len(cluster.centroid_terms) > 2:
            point_text = f"Focus on {cluster.centroid_terms[0]}, {cluster.centroid_terms[1]}, and related concepts"

        evidence = [m.term for m in cluster.members[:5]]

        points.append(
            WorldviewPoint(
                point=point_text,
                confidence=cluster.coherence,
                evidence=evidence,
                sources=[],
            )
        )

    return Worldview(
        subject=subject,
        points=points,
        method="quick",
        depth="quick",
        source_videos=[],
    )


def synthesize_medium(
    clusters: ClusterResult,
    extraction: Extraction,
    subject: str = "",
    n_points: int = 5,
) -> Worldview:
    """Medium synthesis using clusters + extraction data (no LLM).

    Args:
        clusters: Clustered terms
        extraction: Extraction results
        subject: Name of the person being analyzed
        n_points: Number of worldview points

    Returns:
        Worldview with enhanced points
    """
    points: list[WorldviewPoint] = []

    # Build keyword lookup for scoring
    keyword_scores = {kw.term.lower(): kw.score for kw in extraction.keywords}
    tfidf_scores = {tf.term.lower(): tf.score for tf in extraction.tfidf}

    sorted_clusters = sorted(
        clusters.clusters,
        key=lambda c: c.coherence * len(c.members),
        reverse=True,
    )

    for cluster in sorted_clusters[:n_points]:
        # Enhance label with TF-IDF context
        top_terms = cluster.centroid_terms[:3]

        # Find related phrases
        related_phrases = []
        for phrase in extraction.phrases[:20]:
            phrase_lower = phrase.phrase.lower()
            if any(t.lower() in phrase_lower for t in top_terms):
                related_phrases.append(phrase.phrase)
                if len(related_phrases) >= 2:
                    break

        # Build point description
        if related_phrases:
            point_text = f"{top_terms[0].title()}: {related_phrases[0]}"
        else:
            point_text = " and ".join(t.title() for t in top_terms[:2])

        # Gather evidence
        evidence = [m.term for m in cluster.members[:5]]
        evidence.extend(related_phrases[:2])

        # Calculate enhanced confidence
        avg_tfidf = sum(tfidf_scores.get(t.lower(), 0) for t in top_terms) / len(top_terms)
        confidence = (cluster.coherence + min(avg_tfidf, 1.0)) / 2

        points.append(
            WorldviewPoint(
                point=point_text,
                elaboration=f"Related concepts: {', '.join(top_terms)}",
                confidence=min(confidence, 1.0),
                evidence=evidence,
                sources=extraction.source_transcripts[:3],
            )
        )

    return Worldview(
        subject=subject,
        points=points,
        method="medium",
        depth="medium",
        source_videos=extraction.source_transcripts,
    )


def synthesize_deep(
    clusters: ClusterResult,
    extraction: Extraction,
    subject: str = "",
    n_points: int = 5,
    model: str = "llama3",
    ollama_host: str = "http://localhost:11434",
) -> Worldview:
    """Deep synthesis using Ollama LLM.

    Args:
        clusters: Clustered terms
        extraction: Extraction results
        subject: Name of the person being analyzed
        n_points: Number of worldview points
        model: Ollama model name
        ollama_host: Ollama API endpoint

    Returns:
        Worldview with LLM-synthesized points
    """
    try:
        import ollama
    except ImportError:
        raise RuntimeError("Deep synthesis requires ollama package. Install with: pip install ollama")

    # Build context for LLM
    cluster_summary = "\n".join(
        f"- {c.label}: {', '.join(m.term for m in c.members[:5])}"
        for c in clusters.clusters[:10]
    )

    top_tfidf = ", ".join(t.term for t in extraction.tfidf[:20])
    top_phrases = ", ".join(p.phrase for p in extraction.phrases[:15])
    entities = []
    for label, ents in list(extraction.entities.items())[:5]:
        entities.append(f"{label}: {', '.join(e.text for e in ents[:5])}")
    entities_summary = "\n".join(entities) if entities else "None extracted"

    prompt = f"""You are analyzing transcripts from video appearances of {subject} to extract their DISTINCTIVE worldview.

## Extracted Themes
{cluster_summary}

## Key Terms (by TF-IDF)
{top_tfidf}

## Frequent Phrases
{top_phrases}

## Named Entities Mentioned
{entities_summary}

---

Your task: Identify {n_points} beliefs or positions that make {subject}'s worldview DISTINCTIVE.

CRITICAL REQUIREMENTS:
- Focus on what {subject} believes that MOST PEOPLE DON'T
- Identify CONTRARIAN or UNCONVENTIONAL positions
- Be SPECIFIC: use proper nouns, specific claims, named concepts, concrete examples
- AVOID platitudes like "X is important", "Y matters", "believes in Z"
- Each point should be something a reader would find surprising or thought-provoking

For each point:
1. State a specific, distinctive belief (not a generic observation)
2. Elaborate with concrete details or named concepts they reference
3. List specific evidence (exact terms, phrases, entities from the data)
4. Confidence score (0.0-1.0) - higher if multiple sources support this distinctive view

BAD EXAMPLE: "Believes education is important" (generic, everyone believes this)
GOOD EXAMPLE: "Argues that credentialism has corrupted education, preferring apprenticeship models like those of Renaissance Florence" (specific, contrarian, named reference)

Format as JSON:
{{
  "worldview_points": [
    {{
      "point": "...",
      "elaboration": "...",
      "confidence": 0.0,
      "supporting_evidence": ["...", "..."]
    }}
  ]
}}"""

    data = ollama_generate(prompt, model=model, host=ollama_host)
    llm_points = data.get("worldview_points", [])

    if not llm_points:
        # Fall back to medium synthesis if LLM fails
        return synthesize_medium(clusters, extraction, subject, n_points)

    points = [
        WorldviewPoint(
            point=p.get("point", ""),
            elaboration=p.get("elaboration"),
            confidence=float(p.get("confidence", 0.5)),
            evidence=p.get("supporting_evidence", []),
            sources=extraction.source_transcripts[:3],
        )
        for p in llm_points[:n_points]
    ]

    return Worldview(
        subject=subject,
        points=points,
        method="ollama_synthesis",
        depth="deep",
        source_videos=extraction.source_transcripts,
    )


def synthesize(
    clusters: ClusterResult,
    extraction: Extraction | None = None,
    subject: str = "",
    depth: str = "medium",
    n_points: int = 5,
    model: str = "llama3",
) -> Worldview:
    """Synthesize worldview at specified depth.

    Args:
        clusters: Clustered terms
        extraction: Extraction results (required for medium/deep)
        subject: Name of person being analyzed
        depth: "quick", "medium", or "deep"
        n_points: Number of worldview points
        model: Ollama model for deep synthesis

    Returns:
        Synthesized worldview
    """
    if depth == "quick":
        return synthesize_quick(clusters, extraction, subject, n_points)
    elif depth == "medium":
        if extraction is None:
            raise ValueError("Medium synthesis requires extraction data")
        return synthesize_medium(clusters, extraction, subject, n_points)
    elif depth == "deep":
        if extraction is None:
            raise ValueError("Deep synthesis requires extraction data")
        return synthesize_deep(clusters, extraction, subject, n_points, model)
    else:
        raise ValueError(f"Unknown depth: {depth}")


def save_worldview(worldview: Worldview, output_path: str) -> None:
    """Save worldview to JSON."""
    with open(output_path, "w") as f:
        f.write(worldview.model_dump_json(indent=2))


# === Quote-Grounded Synthesis (v0.2) ===


QUOTE_GROUNDED_PROMPT = """You are analyzing transcripts from {subject} to extract their DISTINCTIVE worldview.

## Notable Quotes (verbatim from transcripts)
{quotes_section}

---

Your task: Identify {n_points} beliefs or positions that make {subject}'s worldview DISTINCTIVE.

CRITICAL REQUIREMENTS:
- Every point MUST be supported by at least 2 actual quotes from above
- Focus on what {subject} believes that MOST PEOPLE DON'T
- Be SPECIFIC: use the exact language and concepts from their quotes
- AVOID generic platitudes - if you can't ground it in quotes, don't include it

For each point:
1. State the distinctive belief in your own words
2. Provide 2-3 EXACT QUOTES (verbatim) that support this belief
3. Explain what makes this view contrarian or distinctive
4. Confidence based on how strongly the quotes support this interpretation

Format as JSON:
{{
  "worldview_points": [
    {{
      "point": "...",
      "supporting_quotes": ["exact quote 1", "exact quote 2"],
      "what_makes_it_distinctive": "...",
      "confidence": 0.0
    }}
  ]
}}"""


def synthesize_grounded(
    transcript_dir: Path | str,
    subject: str,
    n_points: int = 5,
    model: str = "llama3",
    ollama_host: str = "http://localhost:11434",
) -> dict:
    """Quote-grounded synthesis using actual quotes from transcripts.
    
    This is the v0.2 approach: every worldview point is backed by verbatim quotes.
    
    Args:
        transcript_dir: Directory containing transcript .txt files
        subject: Name of the person being analyzed
        n_points: Number of worldview points
        model: Ollama model name
        ollama_host: Ollama API endpoint
        
    Returns:
        Dict with worldview points, each backed by exact quotes
    """
    transcript_path = Path(transcript_dir)
    
    # Extract quotes first
    collection = extract_quotes_from_dir(transcript_path, max_quotes=100, min_score=0.25)
    
    if not collection.quotes:
        return {
            "subject": subject,
            "worldview_points": [],
            "error": "No notable quotes found in transcripts",
        }
    
    # Build quotes section for prompt
    quotes_section = "\n".join(
        f'- "{q.text}" (from {q.source_id})'
        for q in collection.quotes[:50]  # Limit for context window
    )
    
    prompt = QUOTE_GROUNDED_PROMPT.format(
        subject=subject,
        quotes_section=quotes_section,
        n_points=n_points,
    )
    
    try:
        data = ollama_generate(prompt, model=model, host=ollama_host)
        points = data.get("worldview_points", [])
    except Exception as e:
        # Return quotes without synthesis if LLM fails
        return {
            "subject": subject,
            "worldview_points": [],
            "quotes": [q.model_dump() for q in collection.quotes[:30]],
            "error": f"LLM synthesis failed: {e}",
            "source_count": collection.source_count,
        }
    
    return {
        "subject": subject,
        "worldview_points": points,
        "source_count": collection.source_count,
        "total_quotes_analyzed": len(collection.quotes),
    }
