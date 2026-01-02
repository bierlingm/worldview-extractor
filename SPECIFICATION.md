# Worldview Extractor — Complete Specification

**Version:** 0.1.0  
**Status:** Draft  
**Created:** 2026-01-02

---

## 1. Executive Summary

Worldview Extractor (`wve`) is a CLI tool that synthesizes a person's intellectual worldview from their public video appearances. It prioritizes local computation over paid inference, using code-based NLP for theme extraction and optional local LLM (Ollama) for synthesis.

**Core principle:** Maximize signal extraction through algorithmic means; use inference only for final synthesis when depth requires it.

---

## 2. Problem Statement

### 2.1 The Need

When encountering a new thinker, researcher, or public intellectual, understanding their worldview requires:
- Finding their video appearances across platforms
- Watching hours of content
- Mentally synthesizing recurring themes and beliefs

This is time-intensive and doesn't scale.

### 2.2 Existing Solutions Gap

Current tools (tldw, ytscript, etc.) focus on single-video summarization. None provide:
- **Person-centric discovery** across multiple videos/channels
- **Cross-video theme aggregation**
- **Configurable depth** from quick keyword scan to deep synthesis
- **Local-first inference** without mandatory API costs

---

## 3. Design Philosophy

### 3.1 Compute Hierarchy

```
Level 0: Pure code (regex, frequency analysis)     — free, instant
Level 1: Local NLP (keyword extraction, NER)       — free, seconds
Level 2: Local embeddings (clustering, similarity) — free, minutes
Level 3: Local LLM (Ollama synthesis)              — free, minutes
Level 4: Droid interaction (Claude via Factory)    — paid, on-demand
```

**Rule:** Never escalate to a higher level unless the lower level is insufficient for the requested depth.

### 3.2 Data Flow

```
[Search Query] → [Video Discovery] → [Transcript Download] → [Preprocessing]
                                                                    ↓
[Structured Output] ← [Synthesis (optional)] ← [Theme Extraction] ←─┘
```

### 3.3 Output Philosophy

The tool produces **structured intermediate artifacts** at each stage. The user (or Droid) can:
- Stop at any stage and use the artifacts
- Resume from cached artifacts
- Choose synthesis depth post-extraction

---

## 4. Functional Requirements

### 4.1 Commands

#### 4.1.1 `wve search <person> [options]`

Discover videos featuring a person.

**Inputs:**
- `<person>`: Name or search term (required)
- `--max-results N`: Maximum videos to find (default: 10)
- `--channel URL`: Limit to specific channel
- `--min-duration M`: Minimum video length in minutes (default: 5)
- `--max-duration M`: Maximum video length in minutes (default: 180)
- `--output FILE`: Save results to JSON file

**Outputs:**
- JSON array of video metadata: `{id, title, channel, duration, url, published}`

**Implementation:**
- Uses `yt-dlp "ytsearch{N}:{query}"` with `--dump-json`
- No API key required

#### 4.1.2 `wve transcripts <input> [options]`

Download and preprocess transcripts.

**Inputs:**
- `<input>`: Video URL, video ID, or JSON file from `wve search`
- `--lang CODE`: Preferred language (default: en)
- `--fallback-whisper`: Use Whisper if no captions (requires confirmation)
- `--output-dir DIR`: Directory for transcript files (default: ./transcripts)

**Outputs:**
- One `.txt` file per video (cleaned, deduplicated)
- `manifest.json`: Metadata linking transcripts to sources

**Implementation:**
- Uses `yt-dlp --write-auto-sub --skip-download`
- VTT → plaintext conversion with deduplication
- Whisper fallback via `whisper` CLI (local model)

#### 4.1.3 `wve extract <input> [options]`

Extract themes, keywords, and entities from transcripts.

**Inputs:**
- `<input>`: Transcript file, directory, or manifest.json
- `--method METHOD`: Extraction method (default: all)
  - `keywords`: YAKE/RAKE keyword extraction
  - `entities`: spaCy NER (people, orgs, concepts)
  - `phrases`: N-gram frequency analysis
  - `tfidf`: TF-IDF across corpus
  - `all`: Run all methods
- `--top N`: Number of items per category (default: 50)
- `--output FILE`: Output JSON file

**Outputs:**
```json
{
  "keywords": [{"term": "...", "score": 0.0, "frequency": 0, "sources": [...]}],
  "entities": {"PERSON": [...], "ORG": [...], "CONCEPT": [...]},
  "phrases": [{"phrase": "...", "count": 0, "sources": [...]}],
  "tfidf": [{"term": "...", "score": 0.0}],
  "co_occurrences": [{"pair": ["a", "b"], "count": 0}]
}
```

**Implementation:**
- YAKE: `yake` library (unsupervised, no training)
- NER: `spacy` with `en_core_web_sm` model
- TF-IDF: `scikit-learn` TfidfVectorizer
- Co-occurrence: sliding window analysis

#### 4.1.4 `wve cluster <input> [options]`

Cluster extracted themes into conceptual groups.

**Inputs:**
- `<input>`: Extraction JSON from `wve extract`
- `--model MODEL`: Embedding model (default: all-MiniLM-L6-v2)
- `--n-clusters N`: Number of clusters (default: auto via silhouette)
- `--output FILE`: Output JSON file

**Outputs:**
```json
{
  "clusters": [
    {
      "id": 0,
      "label": "inferred label",
      "centroid_terms": ["term1", "term2"],
      "members": [{"term": "...", "distance": 0.0}],
      "coherence": 0.0
    }
  ],
  "unclustered": [...],
  "silhouette_score": 0.0
}
```

**Implementation:**
- Embeddings: `sentence-transformers` (local model, ~90MB)
- Clustering: K-means with silhouette-based k selection, or HDBSCAN
- Label inference: Most central terms + frequency weighting

#### 4.1.5 `wve synthesize <input> [options]`

Synthesize worldview points from extracted/clustered data.

**Inputs:**
- `<input>`: Cluster JSON or extraction JSON
- `--depth LEVEL`: Synthesis depth
  - `quick`: 3-point summary, keyword-based (no LLM)
  - `medium`: 5-point summary, cluster labels + top terms (no LLM)
  - `deep`: N-point synthesis via Ollama (requires local LLM)
- `--points N`: Number of worldview points (default: 5)
- `--model MODEL`: Ollama model for deep synthesis (default: llama3)
- `--output FILE`: Output JSON/Markdown file

**Outputs:**

Quick/Medium (no LLM):
```json
{
  "worldview_points": [
    {
      "point": "Civilizations vs Nation-States",
      "confidence": 0.85,
      "evidence": ["term1", "term2", "phrase1"],
      "sources": ["video1.txt:L123", "video2.txt:L456"]
    }
  ],
  "method": "cluster_labels",
  "depth": "medium"
}
```

Deep (with Ollama):
```json
{
  "worldview_points": [
    {
      "point": "Civilizations are self-healing mesh networks...",
      "elaboration": "...",
      "confidence": 0.9,
      "supporting_quotes": ["...", "..."],
      "sources": [...]
    }
  ],
  "method": "ollama_synthesis",
  "model": "llama3",
  "depth": "deep"
}
```

**Implementation:**
- Quick: Top N cluster labels ranked by member count × coherence
- Medium: Cluster labels + top TF-IDF terms + key phrases merged
- Deep: Ollama prompt with extracted data as context

#### 4.1.6 `wve pipeline <person> [options]`

End-to-end pipeline combining all stages.

**Inputs:**
- `<person>`: Name or search term
- `--depth LEVEL`: Target depth (quick/medium/deep)
- `--max-videos N`: Video limit (default: 10)
- `--output-dir DIR`: Working directory
- `--cache`: Use cached intermediates if available

**Outputs:**
- All intermediate artifacts in `output-dir/`
- Final `worldview.json` and `worldview.md`

#### 4.1.7 `wve inspect <artifact>`

Human-readable inspection of any artifact.

**Inputs:**
- `<artifact>`: Any JSON artifact from previous stages

**Outputs:**
- Formatted, colorized terminal output
- Summary statistics

---

### 4.2 Configuration

#### 4.2.1 Config File: `~/.config/wve/config.toml`

```toml
[search]
default_max_results = 10
min_duration_minutes = 5
max_duration_minutes = 180

[transcripts]
preferred_language = "en"
whisper_model = "base"
auto_whisper_fallback = false

[extract]
default_top_n = 50
spacy_model = "en_core_web_sm"

[cluster]
embedding_model = "all-MiniLM-L6-v2"
min_cluster_size = 3

[synthesize]
default_depth = "medium"
default_points = 5
ollama_model = "llama3"
ollama_host = "http://localhost:11434"

[cache]
enabled = true
directory = "~/.cache/wve"
ttl_days = 30
```

#### 4.2.2 Environment Variables

- `WVE_OLLAMA_HOST`: Override Ollama endpoint
- `WVE_CACHE_DIR`: Override cache directory
- `WVE_DEBUG`: Enable debug logging

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Operation | Target | Notes |
|-----------|--------|-------|
| Search (10 videos) | < 5s | Network-bound |
| Transcript download (per video) | < 10s | Network-bound |
| Extraction (10 transcripts) | < 30s | CPU-bound |
| Clustering | < 60s | First run downloads model (~90MB) |
| Synthesis (quick/medium) | < 5s | Pure computation |
| Synthesis (deep) | < 120s | Ollama inference |

### 5.2 Resource Constraints

- **Memory:** < 2GB peak (embedding model is largest consumer)
- **Disk:** 
  - Base install: ~50MB
  - With spaCy model: ~100MB
  - With embedding model: ~200MB
  - Whisper base model: ~150MB (optional)
- **Network:** Only for video search and transcript download

### 5.3 Reliability

- **Graceful degradation:** If optional dependencies missing, skip those features
- **Resumable:** Pipeline can resume from any cached intermediate
- **Idempotent:** Re-running with same inputs produces same outputs

### 5.4 Portability

- **Python:** 3.10+
- **Platforms:** macOS, Linux (Windows untested but should work)
- **Dependencies:** Minimize; prefer stdlib where possible

---

## 6. Technical Architecture

### 6.1 Module Structure

```
worldview-extractor/
├── src/
│   └── wve/
│       ├── __init__.py
│       ├── cli.py              # Click CLI entrypoint
│       ├── search.py           # Video discovery via yt-dlp
│       ├── transcripts.py      # Download and preprocess
│       ├── extract.py          # Theme/keyword extraction
│       ├── cluster.py          # Embedding and clustering
│       ├── synthesize.py       # Worldview synthesis
│       ├── pipeline.py         # End-to-end orchestration
│       ├── cache.py            # Artifact caching
│       ├── models.py           # Pydantic data models
│       └── utils.py            # Shared utilities
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── test_search.py
│   ├── test_transcripts.py
│   ├── test_extract.py
│   ├── test_cluster.py
│   ├── test_synthesize.py
│   ├── test_pipeline.py
│   └── fixtures/               # Test data
│       ├── sample_transcript.txt
│       ├── sample_extraction.json
│       └── sample_clusters.json
├── pyproject.toml
├── README.md
├── SPECIFICATION.md
└── AGENTS.md
```

### 6.2 Data Models (Pydantic)

```python
class VideoMetadata(BaseModel):
    id: str
    title: str
    channel: str
    channel_id: str
    duration_seconds: int
    url: str
    published: datetime
    
class TranscriptManifest(BaseModel):
    created_at: datetime
    videos: list[VideoMetadata]
    transcripts: dict[str, Path]  # video_id -> file path
    
class ExtractedKeyword(BaseModel):
    term: str
    score: float
    frequency: int
    sources: list[str]  # video_ids
    
class ExtractedEntity(BaseModel):
    text: str
    label: str  # PERSON, ORG, etc.
    frequency: int
    sources: list[str]
    
class Extraction(BaseModel):
    keywords: list[ExtractedKeyword]
    entities: dict[str, list[ExtractedEntity]]
    phrases: list[dict]
    tfidf: list[dict]
    co_occurrences: list[dict]
    
class Cluster(BaseModel):
    id: int
    label: str
    centroid_terms: list[str]
    members: list[dict]
    coherence: float
    
class ClusterResult(BaseModel):
    clusters: list[Cluster]
    unclustered: list[str]
    silhouette_score: float
    
class WorldviewPoint(BaseModel):
    point: str
    elaboration: Optional[str]
    confidence: float
    evidence: list[str]
    sources: list[str]
    
class Worldview(BaseModel):
    subject: str
    points: list[WorldviewPoint]
    method: str
    depth: str
    generated_at: datetime
    source_videos: list[str]
```

### 6.3 Dependencies

**Core (required):**
```
click>=8.0           # CLI framework
pydantic>=2.0        # Data validation
yt-dlp>=2024.0       # Video/transcript download (external)
```

**NLP (required for extract):**
```
yake>=0.4            # Keyword extraction (no model download)
spacy>=3.5           # NER (requires model download)
scikit-learn>=1.0    # TF-IDF
```

**Embeddings (required for cluster):**
```
sentence-transformers>=2.2  # Local embeddings
numpy>=1.24
```

**Optional:**
```
hdbscan>=0.8         # Alternative clustering
ollama>=0.1          # Python client for Ollama
rich>=13.0           # Pretty terminal output
```

### 6.4 Caching Strategy

**Cache key:** SHA256 of (input content + parameters)

**Cached artifacts:**
- Search results: `~/.cache/wve/search/{hash}.json`
- Transcripts: `~/.cache/wve/transcripts/{video_id}.txt`
- Extractions: `~/.cache/wve/extract/{hash}.json`
- Clusters: `~/.cache/wve/cluster/{hash}.json`

**Cache invalidation:**
- TTL-based (default 30 days)
- Manual: `wve cache clear [--older-than DAYS]`

---

## 7. Synthesis Prompts

### 7.1 Deep Synthesis Prompt (Ollama)

```
You are analyzing transcripts from video appearances of {subject} to extract their core worldview.

## Extracted Themes
{cluster_summary}

## Key Terms (by TF-IDF)
{top_tfidf_terms}

## Frequent Phrases
{top_phrases}

## Named Entities Mentioned
{entities_summary}

## Sample Quotes
{representative_quotes}

---

Based on this evidence, identify the {n_points} most fundamental aspects of {subject}'s worldview.

For each point:
1. State the core belief/position concisely (1-2 sentences)
2. Provide a brief elaboration (2-3 sentences)
3. List supporting evidence from the extracted data
4. Assign a confidence score (0.0-1.0) based on how strongly the evidence supports this point

Format as JSON:
{
  "worldview_points": [
    {
      "point": "...",
      "elaboration": "...",
      "confidence": 0.0,
      "supporting_evidence": ["...", "..."]
    }
  ]
}
```

### 7.2 Quick Synthesis (Code-based)

Algorithm:
1. Rank clusters by (member_count × coherence)
2. Take top N clusters
3. For each cluster, generate point from:
   - Label (if coherent)
   - Top 3 centroid terms
   - Most frequent phrase containing centroid terms
4. Confidence = cluster coherence score

### 7.3 Medium Synthesis (Code-based)

Algorithm:
1. Start with quick synthesis output
2. Enhance each point with:
   - Top TF-IDF terms from that cluster's source documents
   - Named entities co-occurring with cluster terms
   - Direct quotes containing cluster centroid terms
3. Re-rank by evidence density
4. Confidence = (cluster_coherence + evidence_density) / 2

---

## 8. Error Handling

### 8.1 Error Categories

| Category | Behavior | User Message |
|----------|----------|--------------|
| Network (transient) | Retry 3x with backoff | "Network error, retrying..." |
| Network (permanent) | Fail with cache suggestion | "Video unavailable. Use --cache to skip." |
| No transcripts | Offer Whisper fallback | "No captions. Use --fallback-whisper?" |
| Missing dependency | Skip feature, warn | "spaCy not installed, skipping NER." |
| Ollama unavailable | Fall back to medium depth | "Ollama not running, using medium depth." |
| Invalid input | Fail fast with help | "Expected JSON file, got: {path}" |

### 8.2 Logging

- **Default:** Errors and warnings to stderr
- **--verbose:** Info-level progress
- **--debug:** Full debug trace
- **--quiet:** Errors only

---

## 9. Testing Strategy

### 9.1 Test Categories

#### Unit Tests
- Each module tested in isolation
- Mock external dependencies (yt-dlp, Ollama)
- Focus on data transformation correctness

#### Integration Tests
- End-to-end pipeline with fixture data
- Verify artifact format compliance
- Test caching behavior

#### Robustness Tests ("Noise Tests")
- Malformed transcripts (encoding issues, truncation)
- Missing/partial data
- Timeout simulation
- Empty results handling

#### Quality Tests
- Known-answer tests with curated transcripts
- Extraction precision/recall against manual labels
- Cluster coherence thresholds
- Synthesis sanity checks (hallucination detection)

### 9.2 Test Fixtures

**Fixture 1: Burlingame Sample**
- 2 transcripts from research phase
- Manual extraction labels (ground truth)
- Expected worldview points

**Fixture 2: Synthetic Corpus**
- Generated transcripts with known themes
- Varying noise levels (typos, repetition, tangents)
- Known cluster structure

**Fixture 3: Edge Cases**
- Empty transcript
- Single-word transcript
- Non-English content
- Extremely long transcript (stress test)

### 9.3 Quality Metrics

**Extraction:**
- Keyword precision: % of extracted keywords that are relevant
- Keyword recall: % of known themes captured
- Entity accuracy: % of entities correctly typed

**Clustering:**
- Silhouette score > 0.3 (acceptable)
- Silhouette score > 0.5 (good)
- No singleton clusters (except outliers)

**Synthesis:**
- Coverage: % of source clusters represented in output
- Groundedness: % of claims traceable to evidence
- Coherence: Human-eval or LLM-as-judge score

---

## 10. Future Extensions (Out of Scope for v0.1)

1. **Multi-platform support:** Podcast RSS, Spotify, conference talks
2. **Comparative analysis:** Compare worldviews of multiple people
3. **Temporal analysis:** Track worldview evolution over time
4. **Citation generation:** Academic-style citations for claims
5. **Interactive mode:** TUI for exploring extractions
6. **Export formats:** PDF report, slide deck, mind map

---

## 11. Glossary

| Term | Definition |
|------|------------|
| Worldview | Coherent set of beliefs, values, and frameworks through which a person interprets reality |
| Extraction | Process of identifying salient terms, entities, and phrases from text |
| Clustering | Grouping related concepts based on semantic similarity |
| Synthesis | Combining extracted/clustered data into coherent worldview points |
| Depth | Level of computational sophistication (quick/medium/deep) |
| Artifact | Intermediate or final output file (JSON/Markdown) |

---

## 12. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-01-02 | Initial specification |
