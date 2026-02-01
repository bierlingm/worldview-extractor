use super::Movement;
use anyhow::Result;

pub fn render_json(movement: &Movement) -> Result<String> {
    Ok(serde_json::to_string_pretty(movement)?)
}
