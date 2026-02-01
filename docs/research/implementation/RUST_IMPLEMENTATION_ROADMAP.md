# Rust NLP Implementation Roadmap

## Quick Reference: What to Implement Next

### MVP Phase (Current + 2-3 weeks)

**Goal:** Replace Python NLP pipeline with Rust equivalent

#### 1. Add NER for Quote Attribution

```toml
[dependencies]
rust-bert = "0.23"
```

**Implementation (src/extraction/ner.rs):**
```rust
use rust_bert::pipelines::ner::NERModel;

pub fn extract_speakers(text: &str) -> Result<Vec<String>> {
    let model = NERModel::new(Default::default())?;
    let entities = model.predict(&[text]);

    Ok(entities
        .iter()
        .filter(|e| e.label == "PER")  // Person entities
        .map(|e| e.word.clone())
        .collect())
}
```

**Test:** Extract speakers from 100 random sentences, verify 80%+ accuracy

---

#### 2. Add Quote Detection

**Implementation (src/extraction/quotes.rs):**
```rust
use regex::Regex;

pub struct Quote {
    pub text: String,
    pub speaker: Option<String>,
    pub confidence: f32,
    pub source_context: String,
}

pub fn extract_quotes(text: &str) -> Result<Vec<Quote>> {
    // Pattern 1: "quoted text"
    let quote_regex = Regex::new(r#""([^"]+)""#)?;

    // Pattern 2: 'quoted text' (less common)
    let single_quote = Regex::new(r"'([^']+)'")?;

    // Pattern 3: em-dash quotes
    let em_dash = Regex::new(r"—\s*(.+?)\s*—")?;

    let mut quotes = vec![];

    for (pattern, weight) in &[(quote_regex, 0.95), (single_quote, 0.7), (em_dash, 0.6)] {
        for cap in pattern.captures_iter(text) {
            let quote_text = cap.get(1).unwrap().as_str();

            // Score by length (longer = more likely real quote)
            let length_score = (quote_text.len() as f32).min(200.0) / 200.0;
            let confidence = weight * length_score;

            quotes.push(Quote {
                text: quote_text.to_string(),
                speaker: None,  // Will be filled by NER
                confidence,
                source_context: text.to_string(),
            });
        }
    }

    Ok(quotes)
}
```

**Test:** Extract 50+ quotes from sample transcripts

---

#### 3. Add K-Means Clustering for Themes

```toml
[dependencies]
linfa = "0.7"
linfa-clustering = "0.7"
ndarray = "0.16"
```

**Implementation (src/analysis/clustering.rs):**
```rust
use linfa::prelude::*;
use linfa_clustering::KMeans;
use ndarray::Array2;

pub struct Theme {
    pub id: String,
    pub name: String,
    pub member_count: usize,
    pub centroid: Vec<f32>,
}

pub fn cluster_embeddings(
    embeddings: Vec<Vec<f32>>,
    n_clusters: usize,
) -> Result<(Vec<usize>, Vec<Theme>)> {
    // Convert to ndarray
    let data = Array2::from_shape_vec(
        (embeddings.len(), embeddings[0].len()),
        embeddings.iter().flatten().copied().collect(),
    )?;

    let dataset = DatasetBase::from(data);

    // Fit K-means
    let model = KMeans::params(n_clusters)
        .max_n_iterations(100)
        .fit(&dataset)?;

    let labels = model.predict(&dataset);
    let centroids = model.centroids().to_owned();

    // Convert to Theme structs
    let themes: Vec<Theme> = (0..n_clusters)
        .map(|i| {
            let members = labels.iter().filter(|&&l| l == i).count();
            Theme {
                id: format!("theme-{}", i),
                name: format!("Theme {}", i),  // Will be named by LLM later
                member_count: members,
                centroid: centroids.row(i).to_vec(),
            }
        })
        .collect();

    Ok((labels.to_vec(), themes))
}
```

**Test:** Cluster 1000 random embeddings into 10 themes

---

#### 4. Optimize Embedding Batching

**Current (blocking):**
```rust
pub fn embed_texts(texts: &[&str]) -> Result<Vec<Vec<f32>>> {
    let embedder = get_embedder()?;
    let embeddings = embedder.embed(texts.to_vec(), None)?;
    Ok(embeddings)
}
```

**Improved (async batching):**
```rust
use tokio::task;

pub async fn embed_texts_batched(
    texts: Vec<String>,
    batch_size: usize,
) -> Result<Vec<Vec<f32>>> {
    let mut handles = vec![];

    for chunk in texts.chunks(batch_size) {
        let chunk = chunk.to_vec();
        let handle = task::spawn_blocking(move || {
            embed_texts(&chunk)
        });
        handles.push(handle);
    }

    let mut all_embeddings = vec![];
    for handle in handles {
        let batch = handle.await??;
        all_embeddings.extend(batch);
    }
    Ok(all_embeddings)
}
```

**Benchmark:** Embed 10k texts, compare single-threaded vs batched

---

#### 5. Add LRU Cache for Embeddings

**Implementation (src/embeddings.rs):**
```rust
use lru::LruCache;
use std::sync::Mutex;
use std::num::NonZeroUsize;

lazy_static::lazy_static! {
    static ref EMBEDDING_CACHE: Mutex<LruCache<String, Vec<f32>>> =
        Mutex::new(LruCache::new(
            NonZeroUsize::new(10_000).unwrap()
        ));
}

pub fn embed_text_cached(text: &str) -> Result<Vec<f32>> {
    let mut cache = EMBEDDING_CACHE.lock().unwrap();

    if let Some(cached) = cache.get(text) {
        return Ok(cached.clone());
    }

    let embedding = embed_text(text)?;
    cache.put(text.to_string(), embedding.clone());

    Ok(embedding)
}

#[test]
fn test_cache_hit_rate() {
    // Embed same text 100 times
    // First should be slow, rest should be instant
}
```

**Expected speedup:** 30% for typical workloads

---

### Phase 2 (Weeks 3-4): Advanced Analysis

#### 6. Add Dependency Parsing (Optional)

**Decision tree:**
```
Does your analysis need syntactic relationships?
├─ No → Skip dependency parsing
├─ Yes, only for ~5% of texts → Use Python FFI (PyO3)
└─ Yes, heavily used → Implement custom pattern rules
```

**If using Python FFI:**
```toml
[dependencies]
pyo3 = { version = "0.21", features = ["auto_initialize"] }
```

**Don't implement in pure Rust** (too complex for marginal benefit)

---

#### 7. Add HDBSCAN for Noise-Aware Clustering

```toml
[dependencies]
petal-clustering = "*"
```

**Implementation:**
```rust
use petal_clustering::HierarchicalDensityBasedSpatialClustering;
use ndarray::Array2;

pub fn cluster_hdbscan(
    embeddings: Vec<Vec<f32>>,
    min_cluster_size: usize,
) -> Result<Vec<i32>> {
    let data = Array2::from_shape_vec(
        (embeddings.len(), embeddings[0].len()),
        embeddings.iter().flatten().copied().collect(),
    )?;

    let mut hdbscan = HierarchicalDensityBasedSpatialClustering::new(min_cluster_size);
    let labels = hdbscan.fit_predict(&data);

    // labels: Vec<i32> where -1 = noise, 0..n = cluster ID
    Ok(labels)
}
```

**When to use:** You have "theme noise" (passages that don't fit any theme)

---

#### 8. Add Full-Text Search for Quote Discovery

```toml
[dependencies]
tantivy = "0.21"
```

**Implementation:**
```rust
use tantivy::Index;
use tantivy::schema::*;

pub fn build_quote_index(quotes: Vec<Quote>) -> Result<Index> {
    let mut schema_builder = Schema::builder();
    schema_builder.add_text_field("text", TEXT | STORED);
    schema_builder.add_text_field("speaker", STRING | STORED);
    schema_builder.add_u64_field("doc_id", STORED);

    let schema = schema_builder.build();
    let index = Index::create_in_ram(schema);

    let mut writer = index.writer(50_000_000)?;
    for quote in quotes {
        let doc = doc!(
            "text" => quote.text,
            "speaker" => quote.speaker.unwrap_or_default(),
        );
        writer.add_document(doc)?;
    }
    writer.commit()?;

    Ok(index)
}
```

**Use:** `wve ask "What does X think about Y?"` searches quotes directly

---

### Phase 3 (Weeks 5-6): Scaling

#### 9. Add Qdrant Vector Database (If Scaling)

**Only when:**
- You have >100k vectors
- You need <100ms similarity search
- You want distributed storage

**Skip for MVP** (SQLite is sufficient for 20k vectors)

---

### Testing Strategy

#### Unit Tests (Per Phase)

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_quote_extraction() {
        let text = r#"As Steve Jobs said, "Innovation distinguishes between a leader and a follower.""#;
        let quotes = extract_quotes(text).unwrap();
        assert_eq!(quotes.len(), 1);
        assert!(quotes[0].text.contains("Innovation"));
    }

    #[test]
    fn test_speaker_extraction() {
        let quotes = extract_speakers("Steve Jobs was an innovator.").unwrap();
        assert!(quotes.iter().any(|s| s.contains("Jobs")));
    }

    #[test]
    fn test_clustering_quality() {
        let embeddings = generate_separated_clusters(100, 5);
        let (labels, themes) = cluster_embeddings(embeddings, 5).unwrap();
        assert_eq!(themes.len(), 5);
        // All points in cluster 0 should have label 0
        assert!(labels.iter().take(20).all(|&l| l == 0));
    }

    #[test]
    fn test_caching_speedup() {
        let text = "This is a test sentence.";
        let start = Instant::now();
        let emb1 = embed_text_cached(text).unwrap();
        let time1 = start.elapsed();

        let start = Instant::now();
        let emb2 = embed_text_cached(text).unwrap();
        let time2 = start.elapsed();

        // Second call should be 100x+ faster
        assert!(time2 < Duration::from_millis(1));
        assert!(time1 > time2 * 10);
        assert_eq!(emb1, emb2);
    }
}
```

#### Integration Tests

```bash
# tests/integration_test.rs
#[test]
fn test_full_extraction_pipeline() {
    let transcripts = vec!["sample1.txt", "sample2.txt"];

    // Load transcripts
    let texts: Vec<_> = transcripts
        .iter()
        .flat_map(|path| load_chunks(path))
        .collect();

    // Extract quotes
    let quotes: Vec<_> = texts
        .iter()
        .flat_map(|text| extract_quotes(text).unwrap_or_default())
        .collect();

    assert!(quotes.len() > 10);

    // Embed
    let embeddings = embed_texts_batched(texts, 64).await.unwrap();
    assert_eq!(embeddings.len(), texts.len());

    // Cluster
    let (labels, themes) = cluster_embeddings(embeddings, 5).unwrap();
    assert_eq!(labels.len(), texts.len());
    assert!(themes.len() <= 5);
}
```

---

## Performance Targets

### Latency (1000 videos = 20k texts)

| Phase | Current (Py) | Target (Rust) | Method |
|-------|--------------|---------------|--------|
| Download transcripts | 30 min | 30 min | Parallel yt-dlp |
| Tokenization | 15s | 5s | Add tokenizers crate |
| Embedding | 8s | 2s | Batched fastembed + async |
| Quote extraction | 5s | 3s | Add NER |
| Clustering | 2s | 1s | Add linfa |
| **Total CPU** | **30s** | **11s** | **2.7x faster** |

### Memory (all at once)

| Component | Size |
|-----------|------|
| fastembed model | 22MB |
| 20k embeddings | 30MB |
| NER model (rust-bert) | ~400MB |
| Clustering state | ~2MB |
| SQLite DB | ~100MB |
| **Total** | ~550MB |

**Recommendation:** Process in batches (1-2 videos at a time) to keep memory <300MB

---

## File Structure (After Implementation)

```
wve-rs/src/
├── main.rs
├── lib.rs
├── cli.rs
├── embeddings.rs          (ENHANCED: add caching)
├── nlp/
│   ├── mod.rs
│   ├── tokenization.rs    (NEW)
│   ├── ner.rs             (NEW: rust-bert NER)
│   ├── quotes.rs          (NEW: quote detection)
│   └── stopwords.rs       (NEW: static list)
├── analysis/
│   ├── mod.rs
│   ├── clustering.rs      (NEW: K-means, HDBSCAN)
│   └── themes.rs          (NEW: theme naming + scoring)
├── storage/
│   ├── mod.rs
│   ├── db.rs              (ENHANCED: quote storage)
│   ├── embeddings.rs      (NEW: vector storage)
│   └── json_store.rs
├── synthesis/
│   ├── mod.rs
│   ├── markdown.rs
│   └── movement.rs
└── [existing modules]
```

---

## Dependency Additions (Summary)

### Cargo.toml Changes

```diff
[dependencies]
  # Current
  fastembed = "4"
  clap = { version = "4", features = ["derive"] }
  serde = { version = "1", features = ["derive"] }
  serde_json = "1"
  tokio = { version = "1", features = ["full"] }
  sqlx = { version = "0.32", features = ["bundled"] }

+ # Phase 1: NLP & Clustering (MVP)
+ tokenizers = "0.14"
+ rust-bert = "0.23"
+ regex = "1.10"
+ linfa = "0.7"
+ linfa-clustering = "0.7"
+ ndarray = "0.16"
+ lru = "0.12"
+ lazy_static = "1.4"
+
+ # Phase 2: Advanced (Optional)
+ petal-clustering = "*"              # HDBSCAN
+ tantivy = "0.21"                    # Full-text search
+ whatlang = "0.16"                   # Language detection
+
+ # Phase 3: Scaling (Optional)
+ qdrant-client = { version = "1.8", optional = true }
+
[features]
default = []
vector-db = ["qdrant-client"]
```

---

## Success Criteria

### MVP Phase
- [ ] NER extraction: 80%+ speaker accuracy on 100-sentence sample
- [ ] Quote detection: Find 50+ quotes from sample transcript
- [ ] Clustering: K-means groups similar themes (silhouette score > 0.4)
- [ ] Caching: 30%+ speedup on repeated embeddings
- [ ] Latency: Full 20k-text pipeline in <15 seconds

### Phase 2
- [ ] HDBSCAN clustering works with noise handling
- [ ] Full-text search finds quotes in <100ms
- [ ] No Python dependencies in NLP pipeline

### Phase 3
- [ ] Qdrant integration (optional)
- [ ] 1M+ vectors supported

---

## Risk Mitigation

### Risk: rust-bert NER accuracy < spaCy

**Mitigation:**
1. Compare on test set (100 sentences)
2. If accuracy <80%, keep Python NER for now
3. Fine-tune rust-bert model on domain-specific data

### Risk: Clustering doesn't match human judgment

**Mitigation:**
1. Start with K-means (simple, reproducible)
2. Let user manually verify clusters
3. Adjust n_clusters based on feedback
4. Store original groupings for comparison

### Risk: Memory explosion at scale

**Mitigation:**
1. Process in batches (1-2 videos at a time)
2. Clear embedding cache between batches
3. Use quantized embeddings if needed (75% size reduction)

---

## Timeline Estimate

| Phase | Duration | Effort | Risk |
|-------|----------|--------|------|
| 1. NER + Quote extraction | 1 week | 40hrs | Low |
| 2. Clustering + Caching | 1 week | 40hrs | Low |
| 3. Testing + Optimization | 1 week | 40hrs | Low |
| 4. HDBSCAN + Full-text search | 1 week | 40hrs | Medium |
| **Total** | **4 weeks** | **160hrs** | **Low-Medium** |

---

## References

- [Rust-BERT Examples](https://github.com/guillaume-be/rust-bert/tree/master/examples)
- [Linfa K-Means](https://docs.rs/linfa-clustering/latest/linfa_clustering/struct.KMeans.html)
- [FastEmbed Batching](https://github.com/Anush008/fastembed-rs#batching)
- [SQLx Bulk Insert](https://github.com/launchbadge/sqlx/blob/main/examples/sqlite/examples/dynamic_query.rs)
- [Tokio Spawn Blocking](https://tokio.rs/tokio/tutorial/select#spawn_blocking)

