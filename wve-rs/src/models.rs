use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Worldview {
    pub id: Option<i64>,
    pub slug: String,
    pub subject: String,
    pub points: Vec<WorldviewPoint>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorldviewPoint {
    pub theme: String,
    pub stance: String,
    pub confidence: f64,
    pub evidence: Vec<String>,
    pub sources: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HarnessConfig {
    pub name: String,
    pub harness_type: String,
    pub endpoint: Option<String>,
    pub api_key_ref: Option<String>,
    pub model: Option<String>,
}
