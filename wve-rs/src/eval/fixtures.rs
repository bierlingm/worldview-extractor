use crate::models::Worldview;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize)]
pub struct EvalFixture {
    pub name: String,
    pub transcript_path: PathBuf,
    pub expected_worldview: Worldview,
    pub required_themes: Vec<String>,
    pub forbidden_themes: Vec<String>,
}

pub fn fixtures_dir() -> PathBuf {
    dirs::home_dir()
        .unwrap()
        .join(".wve")
        .join("eval")
        .join("fixtures")
}

pub fn load_fixtures() -> Result<Vec<EvalFixture>> {
    let fixtures_dir = fixtures_dir();
    if !fixtures_dir.exists() {
        return Ok(vec![]);
    }

    let mut fixtures = vec![];
    for entry in std::fs::read_dir(fixtures_dir)? {
        let entry = entry?;
        if entry
            .path()
            .extension()
            .map(|e| e == "json")
            .unwrap_or(false)
        {
            let content = std::fs::read_to_string(entry.path())?;
            let fixture: EvalFixture = serde_json::from_str(&content)?;
            fixtures.push(fixture);
        }
    }
    Ok(fixtures)
}

pub fn save_fixture(fixture: &EvalFixture) -> Result<PathBuf> {
    let dir = fixtures_dir();
    std::fs::create_dir_all(&dir)?;
    let path = dir.join(format!(
        "{}.json",
        fixture.name.replace(" ", "-").to_lowercase()
    ));
    std::fs::write(&path, serde_json::to_string_pretty(fixture)?)?;
    Ok(path)
}
