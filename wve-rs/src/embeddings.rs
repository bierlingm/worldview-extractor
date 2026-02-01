use anyhow::Result;
use fastembed::{EmbeddingModel, InitOptions, TextEmbedding};
use std::sync::OnceLock;

static EMBEDDER: OnceLock<TextEmbedding> = OnceLock::new();

/// Get or initialize the embedding model (all-MiniLM-L6-v2)
fn get_embedder() -> Result<&'static TextEmbedding> {
    if let Some(embedder) = EMBEDDER.get() {
        return Ok(embedder);
    }

    let options = InitOptions::new(EmbeddingModel::AllMiniLML6V2).with_show_download_progress(true);
    let embedder = TextEmbedding::try_new(options)?;

    // Try to set, but if another thread beat us, just use their value
    let _ = EMBEDDER.set(embedder);
    Ok(EMBEDDER.get().unwrap())
}

/// Embed a single text
pub fn embed_text(text: &str) -> Result<Vec<f32>> {
    let embedder = get_embedder()?;
    let embeddings = embedder.embed(vec![text], None)?;
    Ok(embeddings.into_iter().next().unwrap())
}

/// Embed multiple texts
pub fn embed_texts(texts: &[&str]) -> Result<Vec<Vec<f32>>> {
    let embedder = get_embedder()?;
    let embeddings = embedder.embed(texts.to_vec(), None)?;
    Ok(embeddings)
}

/// Cosine similarity between two vectors
pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        dot / (norm_a * norm_b)
    }
}

/// Find most similar text from candidates
pub fn find_most_similar(query: &str, candidates: &[&str]) -> Result<Vec<(usize, f32)>> {
    let query_emb = embed_text(query)?;
    let candidate_embs = embed_texts(candidates)?;

    let mut similarities: Vec<(usize, f32)> = candidate_embs
        .iter()
        .enumerate()
        .map(|(i, emb)| (i, cosine_similarity(&query_emb, emb)))
        .collect();

    similarities.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
    Ok(similarities)
}
