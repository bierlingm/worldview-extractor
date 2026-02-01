use crate::comparison::diff::diff_worldviews;
use crate::models::Worldview;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// A synthesis "movement" - a snapshot of discourse across worldviews
#[derive(Debug, Serialize, Deserialize)]
pub struct Movement {
    pub title: String,
    pub generated_at: DateTime<Utc>,
    pub subjects: Vec<String>,
    pub sections: Vec<MovementSection>,
    pub summary: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MovementSection {
    pub name: String, // e.g., "Convergences", "Tensions", "Unique Voices"
    pub content: Vec<SectionItem>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SectionItem {
    pub theme: String,
    pub voices: Vec<VoicePosition>,
    pub synthesis: String, // AI-generated synthesis of the positions
}

#[derive(Debug, Serialize, Deserialize)]
pub struct VoicePosition {
    pub subject: String,
    pub stance: String,
    pub confidence: f64,
}

/// Generate a movement from multiple worldviews
pub fn generate_movement(worldviews: &[Worldview], title: Option<&str>) -> Movement {
    let subjects: Vec<_> = worldviews.iter().map(|w| w.subject.clone()).collect();
    let title = title.unwrap_or("Synthesis Movement").to_string();

    let mut convergences = vec![];
    let mut tensions = vec![];
    let mut unique_voices = vec![];

    // Compare all pairs
    for i in 0..worldviews.len() {
        for j in (i + 1)..worldviews.len() {
            let diff = diff_worldviews(&worldviews[i], &worldviews[j]);

            for agreement in &diff.agreements {
                convergences.push(SectionItem {
                    theme: agreement.theme.clone(),
                    voices: vec![
                        VoicePosition {
                            subject: worldviews[i].subject.clone(),
                            stance: agreement.point_a.stance.clone(),
                            confidence: agreement.point_a.confidence,
                        },
                        VoicePosition {
                            subject: worldviews[j].subject.clone(),
                            stance: agreement.point_b.stance.clone(),
                            confidence: agreement.point_b.confidence,
                        },
                    ],
                    synthesis: format!(
                        "Both {} and {} converge on: {}",
                        worldviews[i].subject, worldviews[j].subject, agreement.theme
                    ),
                });
            }

            for tension in &diff.tensions {
                tensions.push(SectionItem {
                    theme: tension.theme.clone(),
                    voices: vec![
                        VoicePosition {
                            subject: worldviews[i].subject.clone(),
                            stance: tension.point_a.stance.clone(),
                            confidence: tension.point_a.confidence,
                        },
                        VoicePosition {
                            subject: worldviews[j].subject.clone(),
                            stance: tension.point_b.stance.clone(),
                            confidence: tension.point_b.confidence,
                        },
                    ],
                    synthesis: format!(
                        "Tension between {} and {} on: {}",
                        worldviews[i].subject, worldviews[j].subject, tension.theme
                    ),
                });
            }
        }

        // Unique points for this worldview
        for point in &worldviews[i].points {
            let is_unique = worldviews
                .iter()
                .enumerate()
                .filter(|(idx, _)| *idx != i)
                .all(|(_, other)| {
                    !other
                        .points
                        .iter()
                        .any(|p| p.theme.to_lowercase() == point.theme.to_lowercase())
                });

            if is_unique {
                unique_voices.push(SectionItem {
                    theme: point.theme.clone(),
                    voices: vec![VoicePosition {
                        subject: worldviews[i].subject.clone(),
                        stance: point.stance.clone(),
                        confidence: point.confidence,
                    }],
                    synthesis: format!("Unique to {}: {}", worldviews[i].subject, point.theme),
                });
            }
        }
    }

    let sections = vec![
        MovementSection {
            name: "Convergences".into(),
            content: convergences,
        },
        MovementSection {
            name: "Tensions".into(),
            content: tensions,
        },
        MovementSection {
            name: "Unique Voices".into(),
            content: unique_voices,
        },
    ];

    let summary = format!(
        "Synthesis of {} worldviews: {} convergences, {} tensions, {} unique positions.",
        subjects.len(),
        sections[0].content.len(),
        sections[1].content.len(),
        sections[2].content.len()
    );

    Movement {
        title,
        generated_at: Utc::now(),
        subjects,
        sections,
        summary,
    }
}
