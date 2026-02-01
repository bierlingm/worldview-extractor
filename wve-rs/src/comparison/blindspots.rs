use crate::models::{Worldview, WorldviewPoint};
use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct Blindspot {
    pub subject: String,
    pub missing_theme: String,
    pub addressed_by: Vec<String>,
    pub examples: Vec<WorldviewPoint>,
}

pub fn find_blindspots(target: &Worldview, comparisons: &[&Worldview]) -> Vec<Blindspot> {
    let target_themes: std::collections::HashSet<_> = target
        .points
        .iter()
        .map(|p| normalize_theme(&p.theme))
        .collect();

    let mut blindspots: std::collections::HashMap<String, Blindspot> =
        std::collections::HashMap::new();

    for other in comparisons {
        for point in &other.points {
            let norm = normalize_theme(&point.theme);
            if !target_themes.contains(&norm) {
                let entry = blindspots.entry(norm.clone()).or_insert_with(|| Blindspot {
                    subject: target.subject.clone(),
                    missing_theme: point.theme.clone(),
                    addressed_by: vec![],
                    examples: vec![],
                });
                entry.addressed_by.push(other.subject.clone());
                entry.examples.push(point.clone());
            }
        }
    }

    blindspots.into_values().collect()
}

fn normalize_theme(theme: &str) -> String {
    theme.to_lowercase().trim().to_string()
}
