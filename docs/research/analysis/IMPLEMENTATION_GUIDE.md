# Worldview Extraction: Implementation Guide for Weave

**Purpose:** Translate research frameworks into actionable Python/Rust code for weave
**Target Audience:** Developers implementing belief extraction features

---

## 1. QUICK DECISION MATRIX

### "Should I use X for worldview extraction?"

| Technique | Use Case | Cost | Quality | When to Pick |
|-----------|----------|------|---------|--------------|
| **Keyword extraction (YAKE)** | Quick theme discovery | Free | Medium | When you need instant results, large corpus |
| **spaCy NER** | Entity/concept identification | Free | Good | Standard baseline, person/org/location |
| **GliNER** | Custom entity types (values, principles) | Free | Good | Domain-specific concepts |
| **REBEL/Relik** | Belief triplets (subject-relation-object) | Free | Excellent | Core belief statements extraction |
| **Sentence-BERT + clustering** | Semantic grouping | Free | Excellent | Medium mode synthesis |
| **HDBSCAN** | Natural cluster discovery | Free | Excellent | Replacing fixed K-means |
| **LDA** | Topic modeling | Free | Medium | Quick scan of what matters |
| **Argument mining** | Why people believe things | Moderate | Excellent | Deep mode only |
| **LIWC** | Psychological profile | Paid (~$90) | Excellent | Detecting certainty/deception/drives |
| **Claude API** | Final synthesis + validation | Expensive | Excellent | Deep mode, high-value content |
| **Ollama (local LLM)** | Synthesis without cost | Free | Good | Medium/deep synthesis, privacy |
| **Neo4j** | Storing belief graphs | Free (CE) | Excellent | Comparative analysis, coherence checking |

---

## 2. EXTRACTION PIPELINE (UPDATED FOR BELIEF FOCUS)

### 2.1 Quick Mode Implementation

**Goal:** 30 seconds, identify top beliefs/interests

```python
# quick_extract.py
from yake import KeywordExtractor
import spacy
from collections import Counter

def quick_extract(transcript_text: str, top_n: int = 20) -> dict:
    """Quick mode: keywords + entities."""

    # 1. YAKE keyword extraction
    kw_extractor = KeywordExtractor(lan="en", n=3, top=top_n)
    keywords = kw_extractor.extract_keywords(transcript_text)

    # 2. spaCy NER
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(transcript_text)

    entities_by_type = {}
    for ent in doc.ents:
        ent_type = ent.label_
        if ent_type not in entities_by_type:
            entities_by_type[ent_type] = []
        entities_by_type[ent_type].append(ent.text)

    # 3. Simple TF-IDF approximation
    words = transcript_text.lower().split()
    word_freq = Counter(words)

    return {
        "keywords": [{"term": kw[0], "score": kw[1]} for kw in keywords],
        "entities": entities_by_type,
        "top_terms": [{"term": w, "freq": f} for w, f in word_freq.most_common(20)]
    }
```

**Output interpretation:**
- Keywords = Salient topics person cares about
- Entities = People/orgs that matter to them
- Frequency = What dominates their speech (raw importance)

---

### 2.2 Medium Mode Implementation

**Goal:** 2-3 minutes, semantic grouping + psychological profile

```python
# medium_extract.py
from sentence_transformers import SentenceTransformer
from hdbscan import HDBSCAN
import numpy as np
from quick_extract import quick_extract

def medium_extract(transcript_text: str, top_clusters: int = 8) -> dict:
    """Medium mode: semantic clustering + LIWC profiling."""

    # 1. Get quick extraction as baseline
    quick = quick_extract(transcript_text, top_n=100)
    keywords = [kw["term"] for kw in quick["keywords"]]

    # 2. Embed keywords semantically
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(keywords)

    # 3. Cluster with HDBSCAN
    clustering = HDBSCAN(min_cluster_size=3, gen_min_span_tree=True)
    labels = clustering.fit_predict(embeddings)

    # 4. Generate cluster labels (most central terms)
    clusters = {}
    for idx in set(labels):
        if idx == -1:  # Outliers
            continue
        cluster_terms = [keywords[i] for i, l in enumerate(labels) if l == idx]
        # Label from most central term
        label = cluster_terms[0] if cluster_terms else f"Cluster_{idx}"
        clusters[idx] = {
            "label": label,
            "terms": cluster_terms,
            "size": len(cluster_terms)
        }

    # 5. LIWC analysis (if available)
    liwc_profile = run_liwc(transcript_text) if has_liwc() else None

    return {
        "clusters": clusters,
        "outliers": [keywords[i] for i, l in enumerate(labels) if l == -1],
        "liwc_profile": liwc_profile,
        "suggested_worldview_points": [
            {
                "cluster": v["label"],
                "terms": v["terms"][:3],  # Top 3 in cluster
                "size": v["size"]
            }
            for k, v in sorted(clusters.items(),
                              key=lambda x: x[1]["size"],
                              reverse=True)[:top_clusters]
        ]
    }

def has_liwc() -> bool:
    """Check if LIWC is available (needs license)."""
    try:
        import liwc
        return True
    except ImportError:
        return False

def run_liwc(text: str) -> dict:
    """Run LIWC if available."""
    try:
        import liwc
        parse, _ = liwc.load_token_parser('LIWC2015_English.dic')
        tokens = text.split()
        categories = {}
        for token in tokens:
            for category in parse(token):
                categories[category] = categories.get(category, 0) + 1

        # Normalize by word count
        total = len(tokens)
        return {cat: (count/total)*100 for cat, count in categories.items()}
    except ImportError:
        return None
```

**Output interpretation:**
- Clusters = Semantic themes
- LIWC profile = Psychological signature:
  - High "certainty" (always, never) → Strong epistemological confidence
  - High "power" language → Values around agency/control
  - High "social" → Communal orientation vs. individualist
  - High "future" → Future-oriented vs. present-focused

---

### 2.3 Deep Mode Implementation

**Goal:** 2-5 minutes, full belief extraction with LLM synthesis

```python
# deep_extract.py
from medium_extract import medium_extract
from ollama import OllamaClient  # or Claude API
import json

def deep_extract(
    transcript_text: str,
    subject_name: str,
    use_ollama: bool = True
) -> dict:
    """Deep mode: semantic extraction + LLM synthesis."""

    # 1. Get medium mode output
    medium = medium_extract(transcript_text)

    # 2. Quote extraction (for grounding)
    quotes = extract_representative_quotes(transcript_text, medium["clusters"], n=2)

    # 3. Argument structure (if doing full argument mining)
    # (optional, expensive)

    # 4. LLM synthesis
    synthesis_prompt = build_synthesis_prompt(
        subject=subject_name,
        clusters=medium["clusters"],
        quotes=quotes,
        liwc=medium.get("liwc_profile")
    )

    if use_ollama:
        worldview_points = call_ollama(synthesis_prompt)
    else:
        worldview_points = call_claude(synthesis_prompt)

    return {
        "medium_analysis": medium,
        "quotes": quotes,
        "synthesis_prompt": synthesis_prompt,
        "worldview_points": worldview_points,
        "confidence": calculate_confidence(medium)
    }

def extract_representative_quotes(text: str, clusters: dict, n: int = 2) -> list:
    """Extract quotes representative of each cluster."""
    # Simple heuristic: find sentences containing cluster keywords
    sentences = text.split(". ")
    quotes_per_cluster = {}

    for cluster_id, cluster_info in clusters.items():
        top_term = cluster_info["terms"][0]
        # Find sentence with top_term, scoring by length (3-20 sentences)
        candidates = [
            s for s in sentences
            if top_term.lower() in s.lower() and 8 < len(s.split()) < 50
        ]
        quotes_per_cluster[cluster_id] = candidates[:n]

    return quotes_per_cluster

def build_synthesis_prompt(subject: str, clusters: dict, quotes: dict, liwc: dict = None) -> str:
    """Build LLM prompt for worldview synthesis."""

    cluster_summary = "\n".join([
        f"- {v['label']}: {', '.join(v['terms'][:3])}"
        for k, v in sorted(clusters.items(), key=lambda x: x[1]["size"], reverse=True)
    ])

    quotes_summary = "\n".join([
        f"On {k}: {q}"
        for k, quotes_list in quotes.items()
        for q in quotes_list
    ])

    liwc_summary = ""
    if liwc:
        high_categories = sorted(
            [(k, v) for k, v in liwc.items() if v > 5],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        liwc_summary = f"\nPsychological profile: {', '.join([f'{k}({v:.1f}%)' for k, v in high_categories])}"

    return f"""Analyze the worldview of {subject} based on their public statements.

EXTRACTED THEMES:
{cluster_summary}

REPRESENTATIVE QUOTES:
{quotes_summary}

{liwc_summary}

Identify the 5 most fundamental beliefs about reality, values, and how knowledge works.
For each belief:
1. State it concisely (1-2 sentences)
2. Explain its role in {subject}'s thinking
3. Ground it with evidence from above
4. Assign confidence 0-1 based on evidence strength

Output as JSON matching this schema:
{{
  "beliefs": [
    {{
      "statement": "...",
      "explanation": "...",
      "evidence": ["quote1", "quote2"],
      "confidence": 0.85
    }}
  ]
}}"""

def call_ollama(prompt: str, model: str = "llama3") -> list:
    """Call local Ollama instance."""
    import subprocess
    result = subprocess.run(
        ["ollama", "run", model, prompt],
        capture_output=True,
        text=True
    )
    output = result.stdout
    try:
        parsed = json.loads(output)
        return parsed.get("beliefs", [])
    except json.JSONDecodeError:
        return []  # Fallback to empty

def call_claude(prompt: str, api_key: str = None) -> list:
    """Call Claude API."""
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    output = response.content[0].text
    try:
        parsed = json.loads(output)
        return parsed.get("beliefs", [])
    except json.JSONDecodeError:
        return []

def calculate_confidence(medium: dict) -> float:
    """Estimate overall confidence based on evidence density."""
    num_clusters = len(medium["clusters"])
    avg_cluster_size = np.mean([c["size"] for c in medium["clusters"].values()])

    # More clusters + more dense clusters = higher confidence
    confidence = min(0.95, (num_clusters / 10) * (avg_cluster_size / 5))
    return confidence
```

---

## 3. CONTRARIAN & DISTINCTIVENESS SCORING

### 3.1 Contrarian Detection

```python
# contrarian_scoring.py
from typing import dict, list
import numpy as np
from sentence_transformers import SentenceTransformer

def score_contrarian_beliefs(
    subject_beliefs: dict,
    reference_group: list[dict],  # List of {name, beliefs}
    model = None
) -> dict:
    """
    Score how distinctive subject's beliefs are from reference group.

    Returns beliefs with distinctiveness scores.
    """

    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")

    subject_statements = subject_beliefs.get("statements", [])
    subject_embeddings = model.encode(subject_statements)

    # Compute centroid of reference group beliefs
    all_ref_beliefs = []
    for person in reference_group:
        all_ref_beliefs.extend(person.get("statements", []))

    if not all_ref_beliefs:
        return subject_beliefs  # No reference, can't score

    ref_embeddings = model.encode(all_ref_beliefs)
    ref_centroid = np.mean(ref_embeddings, axis=0)

    # Score each subject belief by distance from centroid
    contrarian_scores = []
    for i, subject_emb in enumerate(subject_embeddings):
        distance = np.linalg.norm(subject_emb - ref_centroid)

        # Normalize by reference group variance
        ref_distances = [np.linalg.norm(ref_emb - ref_centroid) for ref_emb in ref_embeddings]
        percentile = (distance > np.array(ref_distances)).sum() / len(ref_distances)

        contrarian_scores.append({
            "statement": subject_statements[i],
            "distinctiveness": float(percentile),  # 0-1, higher = more unique
            "is_contrarian": percentile > 0.75,  # Top 25% unique
            "distance_from_group": float(distance)
        })

    # Sort by distinctiveness
    contrarian_scores.sort(key=lambda x: x["distinctiveness"], reverse=True)

    return {
        **subject_beliefs,
        "contrarian_analysis": contrarian_scores,
        "contrarian_count": sum(1 for s in contrarian_scores if s["is_contrarian"]),
        "avg_distinctiveness": np.mean([s["distinctiveness"] for s in contrarian_scores])
    }
```

---

### 3.2 Consistency Checking

```python
# consistency_checking.py
from sentence_transformers import SentenceTransformer, util
import numpy as np

def check_belief_consistency(beliefs: list[dict], threshold: float = 0.7) -> dict:
    """
    Check for contradictions in extracted belief system.

    Returns:
    - Coherence score (0-1, how logically integrated)
    - Contradiction pairs (which beliefs conflict)
    - Gaps (beliefs that should connect but don't)
    """

    model = SentenceTransformer("all-MiniLM-L6-v2")

    statements = [b["statement"] for b in beliefs]
    embeddings = model.encode(statements)

    # Compute pairwise similarities
    similarity_matrix = util.pytorch_cos_sim(embeddings, embeddings)

    contradictions = []
    complementary = []

    for i in range(len(beliefs)):
        for j in range(i+1, len(beliefs)):
            sim = similarity_matrix[i][j].item()

            if sim > threshold:
                # Similar beliefs should support each other
                complementary.append({
                    "belief_1": statements[i],
                    "belief_2": statements[j],
                    "similarity": sim,
                    "type": "supporting"
                })
            elif sim < 0.3:
                # Check if they're potentially contradictory
                # (simple heuristic: very dissimilar could be conflicting)
                contradictions.append({
                    "belief_1": statements[i],
                    "belief_2": statements[j],
                    "similarity": sim,
                    "type": "potential_conflict"
                })

    # Coherence = average similarity (beliefs form connected web)
    coherence = float(np.mean(similarity_matrix))

    return {
        "coherence_score": coherence,
        "contradictions": contradictions,
        "supporting_pairs": complementary,
        "integration_level": "high" if coherence > 0.6 else "medium" if coherence > 0.4 else "low"
    }
```

---

## 4. TEMPORAL EVOLUTION TRACKING

```python
# temporal_analysis.py
from datetime import datetime
from sentence_transformers import SentenceTransformer
import numpy as np

def track_belief_evolution(
    timeline_beliefs: list[dict],
    # each item: {date, statement, source}
) -> dict:
    """
    Track how beliefs change over time.

    Returns:
    - Belief trajectory (semantic distance over time)
    - Inflection points (sudden shifts)
    - Drift direction (toward/away from reference group)
    """

    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Sort by date
    timeline = sorted(timeline_beliefs, key=lambda x: x["date"])

    if len(timeline) < 2:
        return {"message": "Need at least 2 time points"}

    # Embed each belief
    statements = [b["statement"] for b in timeline]
    embeddings = model.encode(statements)

    # Compute trajectory: distance between consecutive beliefs
    trajectory = []
    for i in range(1, len(embeddings)):
        distance = np.linalg.norm(embeddings[i] - embeddings[i-1])
        trajectory.append({
            "from_date": timeline[i-1]["date"],
            "to_date": timeline[i]["date"],
            "distance": float(distance),
            "from_statement": timeline[i-1]["statement"],
            "to_statement": timeline[i]["statement"]
        })

    # Identify inflection points (distances > mean + 1 std)
    distances = np.array([t["distance"] for t in trajectory])
    mean_distance = np.mean(distances)
    std_distance = np.std(distances)

    inflection_points = [
        t for t in trajectory
        if t["distance"] > mean_distance + std_distance
    ]

    # Overall trend
    first_half = np.mean(distances[:len(distances)//2]) if len(distances) > 1 else 0
    second_half = np.mean(distances[len(distances)//2:]) if len(distances) > 1 else 0

    return {
        "trajectory": trajectory,
        "inflection_points": inflection_points,
        "overall_volatility": float(np.mean(distances)),
        "trend": "increasing_change" if second_half > first_half else "decreasing_change",
        "stability": "high" if np.mean(distances) < 0.3 else "medium" if np.mean(distances) < 0.6 else "low"
    }
```

---

## 5. KNOWLEDGE GRAPH EXPORT (Neo4j)

```python
# neo4j_export.py
from neo4j import GraphDatabase
from typing import dict, list
import json

class BeliefGraphStore:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def store_worldview(self, subject: str, analysis: dict) -> None:
        """Store extracted worldview as knowledge graph."""

        with self.driver.session() as session:
            # Create subject node
            session.run(
                "CREATE (p:Person {name: $name})",
                name=subject
            )

            # Create belief nodes and relationships
            for point in analysis.get("worldview_points", []):
                # Create belief
                session.run(
                    """CREATE (b:Belief {
                        statement: $stmt,
                        confidence: $conf,
                        category: $cat
                    })""",
                    stmt=point["point"],
                    conf=point["confidence"],
                    cat=point.get("category", "unknown")
                )

                # Link to person
                session.run(
                    """MATCH (p:Person {name: $person})
                       MATCH (b:Belief {statement: $stmt})
                       CREATE (p)-[:HOLDS]->(b)""",
                    person=subject,
                    stmt=point["point"]
                )

            # Create contradiction relationships
            if "contradictions" in analysis:
                for pair in analysis["contradictions"]:
                    session.run(
                        """MATCH (b1:Belief {statement: $stmt1})
                           MATCH (b2:Belief {statement: $stmt2})
                           CREATE (b1)-[:CONTRADICTS {similarity: $sim}]->(b2)""",
                        stmt1=pair["belief_1"],
                        stmt2=pair["belief_2"],
                        sim=pair["similarity"]
                    )

            # Create support relationships
            if "supporting_pairs" in analysis:
                for pair in analysis["supporting_pairs"]:
                    session.run(
                        """MATCH (b1:Belief {statement: $stmt1})
                           MATCH (b2:Belief {statement: $stmt2})
                           CREATE (b1)-[:SUPPORTS {similarity: $sim}]->(b2)""",
                        stmt1=pair["belief_1"],
                        stmt2=pair["belief_2"],
                        sim=pair["similarity"]
                    )

    def comparative_analysis(self, person1: str, person2: str) -> dict:
        """Compare worldviews of two people."""

        with self.driver.session() as session:
            # Find shared beliefs
            shared = session.run(
                """MATCH (p1:Person {name: $p1})-[:HOLDS]->(b)<-[:HOLDS]-(p2:Person {name: $p2})
                   RETURN b.statement""",
                p1=person1,
                p2=person2
            )

            # Find contradictory beliefs
            contradictory = session.run(
                """MATCH (p1:Person {name: $p1})-[:HOLDS]->(b1:Belief)
                   MATCH (p2:Person {name: $p2})-[:HOLDS]->(b2:Belief)
                   WHERE (b1)-[:CONTRADICTS]-(b2)
                   RETURN b1.statement, b2.statement""",
                p1=person1,
                p2=person2
            )

            return {
                "shared_beliefs": [r[0] for r in shared],
                "contradictory_beliefs": [(r[0], r[1]) for r in contradictory]
            }

    def close(self):
        self.driver.close()

# Usage
if __name__ == "__main__":
    store = BeliefGraphStore("bolt://localhost:7687", "neo4j", "password")

    # Example worldview
    worldview = {
        "worldview_points": [
            {
                "point": "Wealth is earned through leverage",
                "confidence": 0.92,
                "category": "economics"
            }
        ],
        "contradictions": [],
        "supporting_pairs": []
    }

    store.store_worldview("Naval Ravikant", worldview)

    # Compare
    comparison = store.comparative_analysis("Naval Ravikant", "Tim Ferriss")
    print(comparison)

    store.close()
```

---

## 6. LIBRARY RECOMMENDATIONS

### Python Libraries

**Core:**
- `sentence-transformers` - Semantic embeddings (state of art)
- `hdbscan` - Clustering (better than K-means for belief extraction)
- `spacy` - NER baseline
- `gliner` - Custom entity extraction

**Optional (Recommended):**
- `relik` - Entity + relationship extraction (triplets)
- `liwc` - Psycholinguistic analysis (~$90 license)
- `neo4j` - Graph storage
- `ollama` - Local LLM (free)
- `anthropic` - Claude API (for deep synthesis)

**Installation:**
```bash
pip install sentence-transformers hdbscan spacy gliner neo4j anthropic
python -m spacy download en_core_web_sm
```

### Rust Integration

**Recommended approach:** Python does NLP, outputs JSON, Rust processes JSON

**Key crates:**
- `serde_json` - JSON handling
- `tokio` - Async runtime
- `pyo3` - Call Python from Rust (if embedding extraction)
- `uuid` - ID generation for beliefs
- `chrono` - Temporal tracking

---

## 7. TESTING STRATEGY

### Unit Tests

```python
# test_extraction.py
import pytest
from medium_extract import medium_extract
from contrarian_scoring import score_contrarian_beliefs

def test_medium_extract():
    sample_text = """
    I believe in wealth creation through leverage. Technology is the greatest leverage.
    Code and media are permissionless. You should read more than you listen.
    """

    result = medium_extract(sample_text)

    assert "clusters" in result
    assert len(result["clusters"]) > 0
    assert "suggested_worldview_points" in result

def test_contrarian_detection():
    subject = {
        "statements": [
            "AI is dangerous and should be regulated",
            "Climate change is overstated",
            "Social media is net positive"
        ]
    }

    reference = [
        {"statements": ["AI is beneficial", "Climate change is urgent"]},
        {"statements": ["AI is beneficial", "Climate change is urgent"]}
    ]

    result = score_contrarian_beliefs(subject, reference)

    # Subject's views are contrarian to reference
    assert result["avg_distinctiveness"] > 0.5
```

### Integration Tests

Test full pipeline with fixture data:

```python
# test_pipeline.py
def test_full_pipeline():
    """Test complete extraction on known content."""

    # Load fixture
    with open("fixtures/sample_transcript.txt") as f:
        text = f.read()

    # Run full pipeline
    from main import extract_worldview
    result = extract_worldview(text, "Test Person", depth="medium")

    # Verify output schema
    assert "worldview_points" in result
    for point in result["worldview_points"]:
        assert "statement" in point
        assert "confidence" in point
        assert isinstance(point["confidence"], float)
        assert 0 <= point["confidence"] <= 1
```

---

## 8. PERFORMANCE OPTIMIZATION

### Caching Strategy

```python
# caching.py
import hashlib
import json
from pathlib import Path

def cache_key(text: str, method: str) -> str:
    """Generate cache key from content hash."""
    return hashlib.sha256(f"{text}{method}".encode()).hexdigest()

def cached_extraction(text: str, depth: str = "medium"):
    """Wrapper that uses cache when available."""
    key = cache_key(text, depth)
    cache_dir = Path.home() / ".cache" / "weave"
    cache_file = cache_dir / f"{key}.json"

    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)

    # Run extraction
    if depth == "quick":
        from quick_extract import quick_extract
        result = quick_extract(text)
    elif depth == "medium":
        from medium_extract import medium_extract
        result = medium_extract(text)
    else:
        from deep_extract import deep_extract
        result = deep_extract(text, "Subject")

    # Cache result
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(result, f)

    return result
```

### Batch Processing

```python
# batch_processing.py
from multiprocessing import Pool
from medium_extract import medium_extract

def process_batch(transcripts: list[str]) -> list[dict]:
    """Process multiple transcripts in parallel."""

    with Pool(processes=4) as pool:
        results = pool.map(medium_extract, transcripts)

    return results
```

---

## 9. ERROR HANDLING

```python
# error_handling.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class ExtractionError:
    code: str
    message: str
    severity: str  # warning, error, critical
    recoverable: bool

def safe_extract(text: str, depth: str = "medium") -> tuple[dict, list[ExtractionError]]:
    """Extract with error tracking."""

    errors = []
    result = {}

    try:
        if not text or len(text) < 100:
            errors.append(ExtractionError(
                code="INPUT_TOO_SHORT",
                message="Input text < 100 words",
                severity="warning",
                recoverable=True
            ))

        if depth == "quick":
            result = quick_extract(text)
        elif depth == "medium":
            result = medium_extract(text)
        elif depth == "deep":
            result = deep_extract(text, "Unknown")

    except Exception as e:
        errors.append(ExtractionError(
            code="EXTRACTION_FAILED",
            message=str(e),
            severity="error",
            recoverable=False
        ))

    return result, errors
```

---

## 10. DEBUGGING CHECKLIST

- [ ] Check input text encoding (UTF-8)
- [ ] Verify spaCy model loaded (`python -m spacy download en_core_web_sm`)
- [ ] Check LIWC licensing if used
- [ ] Verify Neo4j connection (if using graph)
- [ ] Monitor memory on large transcripts (>100k words)
- [ ] Validate JSON output schema matches Pydantic models
- [ ] Test with fixture data before production
- [ ] Check temporal consistency if tracking evolution

---

**Version:** 1.0
**Last Updated:** February 2026
**Status:** Ready for Implementation
