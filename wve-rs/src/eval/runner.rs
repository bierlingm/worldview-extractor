use super::criteria::{CriteriaViolation, EvalCriteria};
use super::fixtures::{load_fixtures, EvalFixture};
use crate::models::Worldview;
use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct EvalResult {
    pub fixture_name: String,
    pub passed: bool,
    pub criteria_violations: Vec<CriteriaViolation>,
    pub missing_required_themes: Vec<String>,
    pub found_forbidden_themes: Vec<String>,
    pub theme_coverage: f64,
}

#[derive(Debug, Serialize)]
pub struct EvalReport {
    pub total: usize,
    pub passed: usize,
    pub failed: usize,
    pub results: Vec<EvalResult>,
}

pub fn run_eval(extracted: &[(String, Worldview)], criteria: &EvalCriteria) -> EvalReport {
    let fixtures = load_fixtures().unwrap_or_default();
    let mut results = vec![];

    for fixture in &fixtures {
        if let Some((_, worldview)) = extracted.iter().find(|(name, _)| name == &fixture.name) {
            let result = eval_against_fixture(worldview, fixture, criteria);
            results.push(result);
        }
    }

    let passed = results.iter().filter(|r| r.passed).count();
    EvalReport {
        total: results.len(),
        passed,
        failed: results.len() - passed,
        results,
    }
}

fn eval_against_fixture(
    worldview: &Worldview,
    fixture: &EvalFixture,
    criteria: &EvalCriteria,
) -> EvalResult {
    let violations = criteria.evaluate(worldview);

    let extracted_themes: std::collections::HashSet<_> = worldview
        .points
        .iter()
        .map(|p| p.theme.to_lowercase())
        .collect();

    let missing: Vec<_> = fixture
        .required_themes
        .iter()
        .filter(|t| !extracted_themes.contains(&t.to_lowercase()))
        .cloned()
        .collect();

    let forbidden: Vec<_> = fixture
        .forbidden_themes
        .iter()
        .filter(|t| extracted_themes.contains(&t.to_lowercase()))
        .cloned()
        .collect();

    let coverage = if fixture.required_themes.is_empty() {
        1.0
    } else {
        (fixture.required_themes.len() - missing.len()) as f64 / fixture.required_themes.len() as f64
    };

    let passed = violations.is_empty() && missing.is_empty() && forbidden.is_empty();

    EvalResult {
        fixture_name: fixture.name.clone(),
        passed,
        criteria_violations: violations,
        missing_required_themes: missing,
        found_forbidden_themes: forbidden,
        theme_coverage: coverage,
    }
}
