use crate::models::Worldview;
use anyhow::Result;

pub fn parse_extraction(json_str: &str) -> Result<Worldview> {
    let worldview: Worldview = serde_json::from_str(json_str)?;
    validate_worldview(&worldview)?;
    Ok(worldview)
}

fn validate_worldview(wv: &Worldview) -> Result<()> {
    if wv.points.is_empty() {
        anyhow::bail!("Worldview has no points");
    }
    for point in &wv.points {
        if point.confidence < 0.0 || point.confidence > 1.0 {
            anyhow::bail!("Invalid confidence: {}", point.confidence);
        }
    }
    Ok(())
}
