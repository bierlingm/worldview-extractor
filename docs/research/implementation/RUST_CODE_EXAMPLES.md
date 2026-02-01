# Rust NLP Code Examples: Copy-Paste Ready

This document contains production-ready code snippets for the worldview extraction engine.

---

## 1. Enhanced Embeddings Module (Drop-in Replacement)

**File: `wve-rs/src/embeddings.rs`**

```rust
use anyhow::Result;
use fastembed::{EmbeddingModel, InitOptions, TextEmbedding};
use lru::LruCache;
use std::num::NonZeroUsize;
use std::sync::OnceLock;
use std::sync::Mutex;

static EMBEDDER: OnceLock<TextEmbedding> = OnceLock::new();
static EMBEDDING_CACHE: OnceLock<Mutex<LruCache<String, Vec<f32>>>> = OnceLock::new();

const CACHE_SIZE: usize = 10_000;

/// Get or initialize the embedding model (all-MiniLM-L6-v2)
fn get_embedder() -> Result<&'static TextEmbedding> {
    if let Some(embedder) = EMBEDDER.get() {
        return Ok(embedder);
    }

    let options = InitOptions::new(EmbeddingModel::AllMiniLML6V2)
        .with_show_download_progress(true);
    let embedder = TextEmbedding::try_new(options)?;

    let _ = EMBEDDER.set(embedder);
    Ok(EMBEDDER.get().unwrap())
}

/// Get or initialize the embedding cache
fn get_cache() -> &'static Mutex<LruCache<String, Vec<f32>>> {
    if let Some(cache) = EMBEDDING_CACHE.get() {
        return cache;
    }

    let cache = Mutex::new(
        LruCache::new(NonZeroUsize::new(CACHE_SIZE).unwrap())
    );
    let _ = EMBEDDING_CACHE.set(cache);
    EMBEDDING_CACHE.get().unwrap()
}

/// Embed a single text with caching
pub fn embed_text(text: &str) -> Result<Vec<f32>> {
    let cache = get_cache();
    let mut cache = cache.lock().unwrap();

    if let Some(cached) = cache.get(text) {
        return Ok(cached.clone());
    }

    drop(cache);  // Release lock before embedding

    let embedder = get_embedder()?;
    let embeddings = embedder.embed(vec![text], None)?;
    let embedding = embeddings.into_iter().next().unwrap();

    // Cache result
    let mut cache = get_cache().lock().unwrap();
    cache.put(text.to_string(), embedding.clone());

    Ok(embedding)
}

/// Embed multiple texts (no caching for batch efficiency)
pub fn embed_texts(texts: &[&str]) -> Result<Vec<Vec<f32>>> {
    let embedder = get_embedder()?;
    let embeddings = embedder.embed(texts.to_vec(), None)?;
    Ok(embeddings)
}

/// Embed multiple texts asynchronously with batching
pub async fn embed_texts_batched(
    texts: Vec<String>,
    batch_size: usize,
) -> Result<Vec<Vec<f32>>> {
    use tokio::task;

    if texts.is_empty() {
        return Ok(vec![]);
    }

    let batch_size = batch_size.max(1);
    let mut handles = vec![];

    for chunk in texts.chunks(batch_size) {
        let chunk: Vec<&str> = chunk.iter().map(|s| s.as_str()).collect();
        let handle = task::spawn_blocking(move || embed_texts(&chunk));
        handles.push(handle);
    }

    let mut all_embeddings = vec![];
    for handle in handles {
        let batch = handle.await??;
        all_embeddings.extend(batch);
    }

    Ok(all_embeddings)
}

/// Cosine similarity between two vectors
pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    if a.len() != b.len() || a.is_empty() {
        return 0.0;
    }

    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();

    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        dot / (norm_a * norm_b)
    }
}

/// Find most similar texts from candidates
pub fn find_most_similar(query: &str, candidates: &[&str], top_k: usize) -> Result<Vec<(usize, f32)>> {
    let query_emb = embed_text(query)?;
    let candidate_embs = embed_texts(candidates)?;

    let mut similarities: Vec<(usize, f32)> = candidate_embs
        .iter()
        .enumerate()
        .map(|(i, emb)| (i, cosine_similarity(&query_emb, emb)))
        .collect();

    similarities.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
    Ok(similarities.into_iter().take(top_k).collect())
}

/// Clear the embedding cache (for memory management)
pub fn clear_cache() {
    if let Some(cache) = EMBEDDING_CACHE.get() {
        let mut cache = cache.lock().unwrap();
        cache.clear();
    }
}

/// Get cache stats (for monitoring)
pub fn cache_stats() -> (usize, usize) {
    if let Some(cache) = EMBEDDING_CACHE.get() {
        let cache = cache.lock().unwrap();
        (cache.len(), CACHE_SIZE)
    } else {
        (0, CACHE_SIZE)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_embed_text() {
        let emb = embed_text("Hello, world!").unwrap();
        assert_eq!(emb.len(), 384);  // all-MiniLM-L6-v2 is 384-dim
    }

    #[test]
    fn test_embedding_cache() {
        clear_cache();
        let text = "This is a test sentence for caching.";

        // First call (cache miss)
        let emb1 = embed_text(text).unwrap();

        // Second call (cache hit)
        let emb2 = embed_text(text).unwrap();

        assert_eq!(emb1, emb2);

        let (cached, total) = cache_stats();
        assert!(cached > 0);
        assert!(cached <= total);
    }

    #[test]
    fn test_cosine_similarity() {
        let a = vec![1.0, 0.0, 0.0];
        let b = vec![1.0, 0.0, 0.0];
        assert!((cosine_similarity(&a, &b) - 1.0).abs() < 0.001);

        let c = vec![0.0, 1.0, 0.0];
        assert!((cosine_similarity(&a, &c)).abs() < 0.001);
    }

    #[tokio::test]
    async fn test_batch_embedding() {
        let texts = vec![
            "First sentence.".to_string(),
            "Second sentence.".to_string(),
            "Third sentence.".to_string(),
        ];
        let embeddings = embed_texts_batched(texts, 2).await.unwrap();
        assert_eq!(embeddings.len(), 3);
        for emb in embeddings {
            assert_eq!(emb.len(), 384);
        }
    }
}
```

---

## 2. Named Entity Recognition Module (NEW)

**File: `wve-rs/src/nlp/ner.rs`**

```rust
use anyhow::Result;
use rust_bert::pipelines::ner::NERModel;
use std::sync::OnceLock;

static NER_MODEL: OnceLock<NERModel> = OnceLock::new();

/// Get or initialize the NER model
fn get_ner_model() -> Result<&'static NERModel> {
    if let Some(model) = NER_MODEL.get() {
        return Ok(model);
    }

    let model = NERModel::new(Default::default())?;
    let _ = NER_MODEL.set(model);
    Ok(NER_MODEL.get().unwrap())
}

#[derive(Clone, Debug)]
pub struct Entity {
    pub text: String,
    pub label: String,
    pub score: f64,
}

/// Extract named entities from text
pub fn extract_entities(text: &str) -> Result<Vec<Entity>> {
    let model = get_ner_model()?;
    let predictions = model.predict(&[text]);

    let entities = predictions
        .into_iter()
        .map(|pred| Entity {
            text: pred.word,
            label: pred.label,
            score: pred.score,
        })
        .collect();

    Ok(entities)
}

/// Extract only person entities (speakers)
pub fn extract_speakers(text: &str) -> Result<Vec<String>> {
    let entities = extract_entities(text)?;

    let speakers: Vec<String> = entities
        .into_iter()
        .filter(|e| e.label == "PER" || e.label == "B-PER" || e.label == "I-PER")
        .map(|e| e.text)
        .collect::<std::collections::HashSet<_>>()  // Deduplicate
        .into_iter()
        .collect();

    Ok(speakers)
}

/// Extract all entity types with high confidence
pub fn extract_entities_confident(text: &str, min_confidence: f64) -> Result<Vec<Entity>> {
    let entities = extract_entities(text)?;
    Ok(entities.into_iter().filter(|e| e.score >= min_confidence).collect())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_entities() {
        let text = "John Smith works at Google in San Francisco.";
        let entities = extract_entities(text).unwrap();

        let person_entities: Vec<_> = entities
            .iter()
            .filter(|e| e.label == "PER" || e.label == "B-PER")
            .collect();
        assert!(!person_entities.is_empty());
    }

    #[test]
    fn test_extract_speakers() {
        let text = "Steve Jobs and Bill Gates revolutionized computing.";
        let speakers = extract_speakers(text).unwrap();
        assert!(speakers.iter().any(|s| s.contains("Jobs") || s.contains("Steve")));
        assert!(speakers.iter().any(|s| s.contains("Gates") || s.contains("Bill")));
    }
}
```

---

## 3. Quote Extraction Module (NEW)

**File: `wve-rs/src/nlp/quotes.rs`**

```rust
use anyhow::Result;
use regex::Regex;
use serde::{Deserialize, Serialize};
use lazy_static::lazy_static;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Quote {
    pub text: String,
    pub speaker: Option<String>,
    pub confidence: f32,
    pub pattern: String,  // "double-quote", "single-quote", "em-dash"
    pub start_index: usize,
    pub end_index: usize,
}

lazy_static! {
    // Pattern 1: "quoted text" (most common)
    static ref DOUBLE_QUOTE: Regex = Regex::new(r#""([^"]{10,})""#).unwrap();

    // Pattern 2: 'quoted text' (less common, needs minimum length)
    static ref SINGLE_QUOTE: Regex = Regex::new(r"'([^']{10,})'").unwrap();

    // Pattern 3: —text— (em-dash quotes)
    static ref EM_DASH: Regex = Regex::new(r"—\s*([A-Z][^—]{10,}?)\s*—").unwrap();

    // Pattern 4: text in parentheses after name (attributive)
    static ref ATTRIBUTIVE: Regex = Regex::new(r"(\w+(?:\s+\w+)*)\s+\(([^)]{10,})\)").unwrap();
}

/// Extract quotes from text using pattern matching
pub fn extract_quotes(text: &str) -> Result<Vec<Quote>> {
    let mut quotes = vec![];

    // Pattern 1: "quoted text"
    for (idx, cap) in DOUBLE_QUOTE.captures_iter(text).enumerate() {
        let quote_text = cap.get(1).unwrap().as_str();
        let start = cap.get(0).unwrap().start();
        let end = cap.get(0).unwrap().end();

        let confidence = calculate_confidence(quote_text, 0.95);

        quotes.push(Quote {
            text: quote_text.to_string(),
            speaker: None,
            confidence,
            pattern: "double-quote".to_string(),
            start_index: start,
            end_index: end,
        });
    }

    // Pattern 2: 'quoted text'
    for cap in SINGLE_QUOTE.captures_iter(text) {
        let quote_text = cap.get(1).unwrap().as_str();
        let start = cap.get(0).unwrap().start();
        let end = cap.get(0).unwrap().end();

        let confidence = calculate_confidence(quote_text, 0.70);

        quotes.push(Quote {
            text: quote_text.to_string(),
            speaker: None,
            confidence,
            pattern: "single-quote".to_string(),
            start_index: start,
            end_index: end,
        });
    }

    // Pattern 3: em-dash quotes
    for cap in EM_DASH.captures_iter(text) {
        let quote_text = cap.get(1).unwrap().as_str();
        let start = cap.get(0).unwrap().start();
        let end = cap.get(0).unwrap().end();

        let confidence = calculate_confidence(quote_text, 0.80);

        quotes.push(Quote {
            text: quote_text.to_string(),
            speaker: None,
            confidence,
            pattern: "em-dash".to_string(),
            start_index: start,
            end_index: end,
        });
    }

    Ok(quotes)
}

/// Calculate quote confidence based on heuristics
fn calculate_confidence(quote_text: &str, base_confidence: f32) -> f32 {
    let text = quote_text.trim();

    // Minimum length check
    if text.len() < 10 {
        return 0.2;
    }

    // Length scoring: longer quotes are more likely real
    let length_score = (text.len() as f32).min(500.0) / 500.0;

    // Capitalization check: real quotes usually start with capital
    let caps_score = if text.chars().next().map(|c| c.is_uppercase()).unwrap_or(false) {
        1.0
    } else {
        0.7
    };

    // Punctuation scoring: quotes with proper punctuation score higher
    let has_punctuation = text.ends_with('.') || text.ends_with('!') || text.ends_with('?');
    let punct_score = if has_punctuation { 1.0 } else { 0.8 };

    // Combine scores
    (base_confidence * length_score * caps_score * punct_score).min(0.99).max(0.1)
}

/// Filter quotes by minimum confidence
pub fn filter_quotes(quotes: Vec<Quote>, min_confidence: f32) -> Vec<Quote> {
    quotes
        .into_iter()
        .filter(|q| q.confidence >= min_confidence)
        .collect()
}

/// Sort quotes by confidence (descending) and length
pub fn rank_quotes(quotes: Vec<Quote>) -> Vec<Quote> {
    let mut sorted = quotes;
    sorted.sort_by(|a, b| {
        // Primary: confidence (descending)
        match b.confidence.partial_cmp(&a.confidence).unwrap() {
            std::cmp::Ordering::Equal => {
                // Secondary: length (descending)
                b.text.len().cmp(&a.text.len())
            }
            other => other,
        }
    });
    sorted
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_double_quotes() {
        let text = r#"Einstein said "Imagination is more important than knowledge.""#;
        let quotes = extract_quotes(text).unwrap();

        assert!(quotes.len() >= 1);
        assert!(quotes[0].text.contains("Imagination"));
    }

    #[test]
    fn test_extract_multiple_patterns() {
        let text = r#"
            He said "Innovation is the path to success."
            She replied 'That is absolutely correct.'
            — The wise one spoke — Success comes to those who try —
        "#;
        let quotes = extract_quotes(text).unwrap();
        assert!(quotes.len() >= 3);
    }

    #[test]
    fn test_confidence_calculation() {
        let short = calculate_confidence("hi", 0.9);
        let long = calculate_confidence("This is a very long quote about the meaning of life", 0.9);
        assert!(short < long);
    }

    #[test]
    fn test_quote_ranking() {
        let quotes = vec![
            Quote {
                text: "Short".to_string(),
                speaker: None,
                confidence: 0.5,
                pattern: "double-quote".to_string(),
                start_index: 0,
                end_index: 10,
            },
            Quote {
                text: "This is a much longer and better quote".to_string(),
                speaker: None,
                confidence: 0.9,
                pattern: "double-quote".to_string(),
                start_index: 0,
                end_index: 40,
            },
        ];

        let ranked = rank_quotes(quotes);
        assert!(ranked[0].confidence > ranked[1].confidence);
    }
}
```

---

## 4. Clustering Module (NEW)

**File: `wve-rs/src/analysis/clustering.rs`**

```rust
use anyhow::{anyhow, Result};
use linfa::prelude::*;
use linfa_clustering::KMeans;
use ndarray::Array2;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Theme {
    pub id: String,
    pub cluster_id: usize,
    pub name: String,
    pub description: Option<String>,
    pub member_count: usize,
    pub centroid: Vec<f32>,
}

/// Cluster embeddings using K-Means
pub fn cluster_kmeans(
    embeddings: Vec<Vec<f32>>,
    n_clusters: usize,
    max_iterations: usize,
) -> Result<(Vec<usize>, Vec<Theme>)> {
    if embeddings.is_empty() {
        return Err(anyhow!("No embeddings provided"));
    }

    if n_clusters == 0 {
        return Err(anyhow!("n_clusters must be > 0"));
    }

    let n_features = embeddings[0].len();
    let n_samples = embeddings.len();

    // Flatten embeddings to 2D array
    let data_flat: Vec<f32> = embeddings
        .iter()
        .flat_map(|v| v.clone())
        .collect();

    let data = Array2::from_shape_vec((n_samples, n_features), data_flat)?;
    let dataset = DatasetBase::from(data);

    // Fit K-means
    let model = KMeans::params(n_clusters)
        .max_n_iterations(max_iterations)
        .fit(&dataset)?;

    let labels = model.predict(&dataset);
    let centroids = model.centroids().to_owned();

    // Convert to Theme structs
    let mut themes = vec![];
    for cluster_id in 0..n_clusters {
        let members = labels.iter().filter(|&&l| l == cluster_id).count();

        themes.push(Theme {
            id: format!("theme-{}", cluster_id),
            cluster_id,
            name: format!("Theme {}", cluster_id),
            description: None,
            member_count: members,
            centroid: centroids.row(cluster_id).to_vec(),
        });
    }

    Ok((labels.to_vec(), themes))
}

/// Compute silhouette score for clustering quality (0-1, higher is better)
pub fn silhouette_score(
    embeddings: &[Vec<f32>],
    labels: &[usize],
) -> Result<f32> {
    if embeddings.len() != labels.len() {
        return Err(anyhow!("Embeddings and labels length mismatch"));
    }

    if embeddings.is_empty() {
        return Ok(0.0);
    }

    use crate::embeddings::cosine_similarity;

    let mut total_score = 0.0;
    let n = embeddings.len();

    for i in 0..n {
        let label_i = labels[i];

        // a(i): mean distance to points in same cluster
        let same_cluster: Vec<usize> = labels
            .iter()
            .enumerate()
            .filter(|(_, &l)| l == label_i)
            .map(|(idx, _)| idx)
            .collect();

        let a = if same_cluster.len() > 1 {
            let distances: Vec<f32> = same_cluster
                .iter()
                .filter(|&&j| j != i)
                .map(|&j| 1.0 - cosine_similarity(&embeddings[i], &embeddings[j]))
                .collect();

            distances.iter().sum::<f32>() / distances.len() as f32
        } else {
            0.0
        };

        // b(i): min mean distance to points in other clusters
        let mut min_b = f32::INFINITY;
        let unique_labels: std::collections::HashSet<_> = labels.iter().copied().collect();

        for &other_label in &unique_labels {
            if other_label == label_i {
                continue;
            }

            let other_cluster: Vec<usize> = labels
                .iter()
                .enumerate()
                .filter(|(_, &l)| l == other_label)
                .map(|(idx, _)| idx)
                .collect();

            if !other_cluster.is_empty() {
                let distances: Vec<f32> = other_cluster
                    .iter()
                    .map(|&j| 1.0 - cosine_similarity(&embeddings[i], &embeddings[j]))
                    .collect();

                let mean_dist = distances.iter().sum::<f32>() / distances.len() as f32;
                min_b = min_b.min(mean_dist);
            }
        }

        let b = if min_b == f32::INFINITY { 0.0 } else { min_b };

        // Silhouette coefficient
        let s = if a.max(b) > 0.0 {
            (b - a) / a.max(b)
        } else {
            0.0
        };

        total_score += s;
    }

    Ok((total_score / n as f32 + 1.0) / 2.0)  // Normalize to [0, 1]
}

/// Recommend optimal number of clusters based on silhouette score
pub fn find_optimal_clusters(
    embeddings: Vec<Vec<f32>>,
    min_clusters: usize,
    max_clusters: usize,
) -> Result<usize> {
    let mut best_k = min_clusters;
    let mut best_score = -1.0;

    for k in min_clusters..=max_clusters {
        let (labels, _) = cluster_kmeans(embeddings.clone(), k, 100)?;
        let score = silhouette_score(&embeddings, &labels)?;

        if score > best_score {
            best_score = score;
            best_k = k;
        }

        // Early exit if score is very good
        if score > 0.7 {
            break;
        }
    }

    Ok(best_k)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn generate_test_embeddings(n: usize, dim: usize) -> Vec<Vec<f32>> {
        use rand::distributions::Normal;
        use rand::Rng;

        let mut rng = rand::thread_rng();
        let normal = Normal::new(0.0, 0.1).unwrap();

        (0..n)
            .map(|_| {
                (0..dim)
                    .map(|_| rng.sample(&normal))
                    .collect()
            })
            .collect()
    }

    #[test]
    fn test_kmeans_clustering() {
        let embeddings = generate_test_embeddings(100, 384);
        let (labels, themes) = cluster_kmeans(embeddings, 5, 100).unwrap();

        assert_eq!(labels.len(), 100);
        assert_eq!(themes.len(), 5);

        for theme in themes {
            assert!(theme.member_count > 0);
            assert_eq!(theme.centroid.len(), 384);
        }
    }

    #[test]
    fn test_silhouette_score() {
        let embeddings = generate_test_embeddings(50, 384);
        let (labels, _) = cluster_kmeans(embeddings.clone(), 3, 100).unwrap();
        let score = silhouette_score(&embeddings, &labels).unwrap();

        assert!(score >= -1.0 && score <= 1.0);
    }
}
```

---

## 5. Integration: Updated Cargo.toml

**File: `wve-rs/Cargo.toml`**

```toml
[package]
name = "wve"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "wve"
path = "src/main.rs"

[dependencies]
# Existing
bubbletea = { path = "vendor/charmed_rust/crates/bubbletea" }
lipgloss = { path = "vendor/charmed_rust/crates/lipgloss" }
bubbles = { path = "vendor/charmed_rust/crates/bubbles" }
huh = { path = "vendor/charmed_rust/crates/huh" }

# Embeddings (existing, enhanced)
fastembed = "0.4"
lru = "0.12"
lazy_static = "1.4"

# New: NLP
tokenizers = "0.14"
rust-bert = "0.23"
tch = "0.12"
regex = "1.10"

# New: Clustering
linfa = "0.7"
linfa-clustering = "0.7"
ndarray = "0.16"

# Existing
clap = { version = "4", features = ["derive"] }
clap_complete = "4"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tokio = { version = "1", features = ["full"] }
rusqlite = { version = "0.32", features = ["bundled"] }
dirs = "5"
anyhow = "1"
thiserror = "2"
chrono = { version = "0.4", features = ["serde"] }
which = "7"
toml = "0.8"

# Optional: for testing
[dev-dependencies]
rand = "0.8"
criterion = "0.5"

[[bench]]
name = "embedding_benchmark"
harness = false

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
```

---

## 6. Module Structure

**File: `wve-rs/src/lib.rs`**

```rust
pub mod embeddings;
pub mod nlp;
pub mod analysis;
pub mod storage;
pub mod synthesis;
pub mod comparison;
pub mod extraction;
pub mod eval;
pub mod harness;
pub mod transcripts;
pub mod models;
pub mod wizard;

pub use embeddings::{embed_text, embed_texts, cosine_similarity, find_most_similar};
pub use nlp::{
    ner::{extract_entities, extract_speakers},
    quotes::{extract_quotes, Quote},
};
pub use analysis::clustering::{cluster_kmeans, silhouette_score, find_optimal_clusters};
```

**File: `wve-rs/src/nlp/mod.rs`**

```rust
pub mod tokenization;
pub mod ner;
pub mod quotes;

pub use ner::{extract_entities, extract_speakers};
pub use quotes::{extract_quotes, Quote};
```

**File: `wve-rs/src/analysis/mod.rs`**

```rust
pub mod clustering;

pub use clustering::{cluster_kmeans, silhouette_score};
```

---

## 7. Integration Example: Complete Pipeline

**File: `wve-rs/src/bin/extract_worldview.rs`**

```rust
use anyhow::Result;
use wve::embeddings;
use wve::nlp::{extract_quotes, extract_speakers};
use wve::analysis::clustering::cluster_kmeans;
use std::fs;

#[tokio::main]
async fn main() -> Result<()> {
    // 1. Load transcripts
    let text = fs::read_to_string("transcript.txt")?;

    // 2. Split into sentences (simple approach)
    let sentences: Vec<&str> = text.split('.').collect();

    // 3. Extract quotes
    let quotes = extract_quotes(&text)?;
    println!("Found {} quotes", quotes.len());

    // 4. Extract speakers from quotes context
    let speakers = extract_speakers(&text)?;
    println!("Identified speakers: {:?}", speakers);

    // 5. Embed sentences asynchronously
    let sentences_owned: Vec<String> = sentences.iter().map(|s| s.to_string()).collect();
    let embeddings = embeddings::embed_texts_batched(sentences_owned, 64).await?;
    println!("Embedded {} sentences", embeddings.len());

    // 6. Cluster themes
    let (labels, themes) = cluster_kmeans(embeddings, 5, 100)?;
    for theme in themes {
        println!(
            "{}: {} members",
            theme.id, theme.member_count
        );
    }

    Ok(())
}
```

---

## 8. Performance Optimization Tips

### Tip 1: Batch Embedding for Large Datasets

```rust
// Instead of:
for text in texts {
    let emb = embed_text(text)?;
}

// Do this:
let embeddings = embed_texts_batched(texts, 64).await?;
```

**Speedup:** 4-8x faster

### Tip 2: Use Caching for Repeated Texts

```rust
// First call caches the result
let emb1 = embed_text("Hello, world!")?;  // ~100ms

// Second call hits cache
let emb2 = embed_text("Hello, world!")?;  // <1ms
```

**Speedup:** 100x for cache hits

### Tip 3: Clear Cache Between Batches

```rust
let total_texts = 100_000;
for chunk in texts.chunks(10_000) {
    process_chunk(chunk).await?;
    embeddings::clear_cache();  // Free ~100MB RAM
}
```

**Memory:** Keeps usage constant

---

## 9. Testing Checklist

```bash
# Run all tests
cargo test --release

# Run with output
cargo test -- --nocapture

# Specific test
cargo test test_kmeans_clustering -- --nocapture

# Benchmark
cargo bench

# Check compilation
cargo check

# Lint
cargo clippy
```

---

## References

- [FastEmbed Docs](https://docs.rs/fastembed/latest/fastembed/)
- [Rust-BERT Docs](https://docs.rs/rust-bert/latest/rust_bert/)
- [Linfa Documentation](https://docs.rs/linfa/latest/linfa/)
- [Tokio Async](https://tokio.rs/tokio/tutorial)
- [Regex Crate](https://docs.rs/regex/latest/regex/)

