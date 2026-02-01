use crate::embeddings;
use crate::models::{Worldview, WorldviewPoint};
use serde::Serialize;

const SIMILARITY_THRESHOLD: f32 = 0.7;

#[derive(Debug, Serialize)]
pub struct WorldviewDiff {
    pub subject_a: String,
    pub subject_b: String,
    pub agreements: Vec<PointComparison>,
    pub tensions: Vec<PointComparison>,
    pub unique_to_a: Vec<WorldviewPoint>,
    pub unique_to_b: Vec<WorldviewPoint>,
    pub similarity_score: f64,
}

#[derive(Debug, Clone, Serialize)]
pub struct PointComparison {
    pub theme: String,
    pub point_a: WorldviewPoint,
    pub point_b: WorldviewPoint,
    pub alignment: Alignment,
}

#[derive(Debug, Clone, Serialize)]
pub enum Alignment {
    Agreement,
    Tension,
    Nuance,
}

fn find_matching_point<'a>(theme: &str, points: &'a [WorldviewPoint]) -> Option<&'a WorldviewPoint> {
    // Try semantic match
    let themes: Vec<&str> = points.iter().map(|p| p.theme.as_str()).collect();
    if !themes.is_empty() {
        if let Ok(similarities) = embeddings::find_most_similar(theme, &themes) {
            if let Some(&(idx, score)) = similarities.first() {
                if score >= SIMILARITY_THRESHOLD {
                    return Some(&points[idx]);
                }
            }
        }
    }
    // Fallback to keyword
    points
        .iter()
        .find(|p| normalize_theme(&p.theme) == normalize_theme(theme))
}

pub fn diff_worldviews(a: &Worldview, b: &Worldview) -> WorldviewDiff {
    let mut agreements = vec![];
    let mut tensions = vec![];
    let mut unique_to_a = vec![];
    let mut unique_to_b = vec![];
    let mut matched_b_indices: std::collections::HashSet<usize> = std::collections::HashSet::new();

    for point_a in &a.points {
        if let Some(point_b) = find_matching_point(&point_a.theme, &b.points) {
            // Track which b points were matched
            if let Some(idx) = b.points.iter().position(|p| std::ptr::eq(p, point_b)) {
                matched_b_indices.insert(idx);
            }
            let alignment = compare_stances(&point_a.stance, &point_b.stance);
            let comparison = PointComparison {
                theme: point_a.theme.clone(),
                point_a: point_a.clone(),
                point_b: point_b.clone(),
                alignment: alignment.clone(),
            };
            match alignment {
                Alignment::Agreement | Alignment::Nuance => agreements.push(comparison),
                Alignment::Tension => tensions.push(comparison),
            }
        } else {
            unique_to_a.push(point_a.clone());
        }
    }

    // Use matched indices to determine unique_to_b
    for (idx, point_b) in b.points.iter().enumerate() {
        if !matched_b_indices.contains(&idx) {
            unique_to_b.push(point_b.clone());
        }
    }

    let total = agreements.len() + tensions.len() + unique_to_a.len() + unique_to_b.len();
    let similarity = if total > 0 {
        agreements.len() as f64 / total as f64
    } else {
        0.0
    };

    WorldviewDiff {
        subject_a: a.subject.clone(),
        subject_b: b.subject.clone(),
        agreements,
        tensions,
        unique_to_a,
        unique_to_b,
        similarity_score: similarity,
    }
}

fn normalize_theme(theme: &str) -> String {
    theme.to_lowercase().trim().to_string()
}

fn compare_stances(a: &str, b: &str) -> Alignment {
    let negatives = ["not", "against", "oppose", "reject", "deny"];
    let a_negative = negatives.iter().any(|n| a.to_lowercase().contains(n));
    let b_negative = negatives.iter().any(|n| b.to_lowercase().contains(n));

    if a_negative != b_negative {
        Alignment::Tension
    } else {
        Alignment::Agreement
    }
}
