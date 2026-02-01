use crate::models::Worldview;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EvalCriteria {
    pub min_points: usize,
    pub max_points: usize,
    pub min_avg_confidence: f64,
    pub require_evidence: bool,
    pub max_elaboration_words: usize,
}

impl EvalCriteria {
    pub fn default_strict() -> Self {
        Self {
            min_points: 5,
            max_points: 25,
            min_avg_confidence: 0.5,
            require_evidence: true,
            max_elaboration_words: 150,
        }
    }

    pub fn evaluate(&self, worldview: &Worldview) -> Vec<CriteriaViolation> {
        let mut violations = vec![];

        if worldview.points.len() < self.min_points {
            violations.push(CriteriaViolation {
                criterion: "min_points".into(),
                message: format!(
                    "Only {} points, expected at least {}",
                    worldview.points.len(),
                    self.min_points
                ),
            });
        }

        if worldview.points.len() > self.max_points {
            violations.push(CriteriaViolation {
                criterion: "max_points".into(),
                message: format!(
                    "{} points exceeds max {}",
                    worldview.points.len(),
                    self.max_points
                ),
            });
        }

        if !worldview.points.is_empty() {
            let avg_conf: f64 =
                worldview.points.iter().map(|p| p.confidence).sum::<f64>() / worldview.points.len() as f64;
            if avg_conf < self.min_avg_confidence {
                violations.push(CriteriaViolation {
                    criterion: "min_avg_confidence".into(),
                    message: format!(
                        "Average confidence {:.2} below minimum {:.2}",
                        avg_conf, self.min_avg_confidence
                    ),
                });
            }
        }

        if self.require_evidence {
            for (i, point) in worldview.points.iter().enumerate() {
                if point.evidence.is_empty() {
                    violations.push(CriteriaViolation {
                        criterion: "require_evidence".into(),
                        message: format!("Point {} '{}' has no evidence", i, point.theme),
                    });
                }
            }
        }

        violations
    }
}

#[derive(Debug, Serialize)]
pub struct CriteriaViolation {
    pub criterion: String,
    pub message: String,
}
