use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct HarnessConfig {
    pub default_harness: Option<String>,
    #[serde(default)]
    pub harnesses: Vec<ConfiguredHarness>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfiguredHarness {
    pub name: String,
    pub harness_type: String,
    pub endpoint: Option<String>,
    pub model: Option<String>,
    #[serde(default = "default_enabled")]
    pub enabled: bool,
}

fn default_enabled() -> bool {
    true
}

impl HarnessConfig {
    pub fn load() -> anyhow::Result<Self> {
        let path = config_path();
        if path.exists() {
            let content = std::fs::read_to_string(&path)?;
            Ok(toml::from_str(&content)?)
        } else {
            Ok(Self::default())
        }
    }

    pub fn save(&self) -> anyhow::Result<()> {
        let path = config_path();
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let content = toml::to_string_pretty(self)?;
        std::fs::write(&path, content)?;
        Ok(())
    }
}

fn config_path() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".wve")
        .join("config.toml")
}
