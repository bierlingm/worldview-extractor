use anyhow::Result;
use std::path::PathBuf;

/// Check if this is first run (no config exists)
pub fn is_first_run() -> bool {
    !config_path().exists()
}

fn config_path() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".wve")
        .join("config.toml")
}

/// Run the setup wizard
pub fn run_wizard() -> Result<()> {
    use crate::harness::config::{ConfiguredHarness, HarnessConfig};
    use crate::harness::detect_harnesses;

    println!("Welcome to wve - Worldview Extractor\n");
    println!("Let's set up your configuration.\n");

    // Detect available harnesses
    let detected = detect_harnesses();

    if detected.is_empty() {
        println!("No LLM harnesses detected. You can still use wve with:");
        println!("  wve prepare <subject> | <your-llm-tool> | wve ingest -");
        println!("\nSupported harnesses: claude, ollama, llm, openai, llamafile");
    } else {
        println!("Detected {} harness(es):", detected.len());
        for h in &detected {
            println!("  - {} ({})", h.name, h.path);
        }
        println!();
    }

    // Create default config
    let config = HarnessConfig {
        default_harness: detected.first().map(|h| h.name.clone()),
        harnesses: detected
            .iter()
            .map(|h| ConfiguredHarness {
                name: h.name.clone(),
                harness_type: format!("{:?}", h.harness_type),
                endpoint: None,
                model: None,
                enabled: true,
            })
            .collect(),
    };

    // Save config
    config.save()?;
    println!("Configuration saved to ~/.wve/config.toml");
    println!("\nRun 'wve' again to start the TUI, or use CLI commands:");
    println!("  wve list              - List stored worldviews");
    println!("  wve prepare <subject> - Generate extraction prompt");
    println!("  wve harnesses         - Show detected harnesses");

    Ok(())
}
