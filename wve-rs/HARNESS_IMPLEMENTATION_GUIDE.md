# Harness Integration Implementation Guide

**Target:** Extend existing harness detection in wve-rs with trait-based abstraction
**Current State:** Binary detection only (`which` + `--version`)
**Goal State:** Pluggable harness handlers with capability routing

---

## Quick Reference: File Changes Needed

```
src/harness/
├── mod.rs              (existing)
├── detect.rs           (existing - enhance)
├── config.rs           (existing)
├── handler.rs          (NEW - trait definition)
├── claude.rs           (NEW - Claude implementation)
├── ollama.rs           (NEW - Ollama implementation)
├── lm_studio.rs        (NEW - LM Studio implementation)
├── llamafile.rs        (NEW - Llamafile implementation)
├── openai.rs           (NEW - OpenAI implementation)
├── factory.rs          (NEW - factory pattern)
├── router.rs           (NEW - routing logic)
├── capabilities.rs     (NEW - capability definitions)
└── tests/
    ├── mock.rs         (NEW - mock handlers)
    └── integration.rs  (NEW - integration tests)
```

---

## Step 1: Update Cargo.toml

Add required dependencies:

```toml
[dependencies]
# ... existing ...

# Async trait support
async-trait = "0.1"

# HTTP client for remote harnesses
reqwest = { version = "0.12", features = ["json"] }

# URL parsing
url = "2"

# Structured concurrency
tokio = { version = "1", features = ["full"] }

# For OrderedFloat in routing
ordered-float = "4.0"

# For retry logic
backoff = { version = "0.4", features = ["tokio"] }
```

---

## Step 2: Define the Handler Trait

**File: `src/harness/handler.rs`** (NEW)

```rust
use anyhow::Result;
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::time::Duration;

/// Core trait that all harness implementations must implement
#[async_trait]
pub trait HarnessHandler: Send + Sync {
    /// Get harness type identifier
    fn harness_type(&self) -> HarnessType;

    /// Get human-readable name
    fn name(&self) -> &str;

    /// Check if harness is available and operational
    async fn is_available(&self) -> bool;

    /// Get version string (if available)
    async fn version(&self) -> Option<String>;

    /// List available models
    async fn list_models(&self) -> Result<Vec<ModelInfo>>;

    /// Execute a synthesis prompt (returns text)
    async fn synthesize(
        &self,
        model: &str,
        system_prompt: &str,
        user_prompt: &str,
    ) -> Result<String>;

    /// Execute a chat completion
    async fn chat(
        &self,
        model: &str,
        messages: Vec<Message>,
    ) -> Result<String>;

    /// Get maximum tokens supported (if applicable)
    fn max_tokens(&self) -> Option<usize> {
        None
    }

    /// Test connectivity with timeout
    async fn test_connection(&self) -> Result<()> {
        if !self.is_available().await {
            anyhow::bail!("{} is not available", self.name());
        }
        Ok(())
    }

    /// Get configuration if needed
    fn config(&self) -> crate::harness::HarnessConfig;
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum HarnessType {
    Claude,
    Ollama,
    Llm,
    OpenAI,
    Llamafile,
    LMStudio,
    Custom,
}

impl std::fmt::Display for HarnessType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Claude => write!(f, "claude"),
            Self::Ollama => write!(f, "ollama"),
            Self::Llm => write!(f, "llm"),
            Self::OpenAI => write!(f, "openai"),
            Self::Llamafile => write!(f, "llamafile"),
            Self::LMStudio => write!(f, "lm-studio"),
            Self::Custom => write!(f, "custom"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelInfo {
    pub name: String,
    pub size: Option<String>,
    pub available: bool,
    pub quantization: Option<String>,
    pub context_window: Option<usize>,
}

#[derive(Debug, Clone)]
pub struct Message {
    pub role: String,  // "system", "user", "assistant"
    pub content: String,
}

impl Message {
    pub fn system(content: impl Into<String>) -> Self {
        Self {
            role: "system".to_string(),
            content: content.into(),
        }
    }

    pub fn user(content: impl Into<String>) -> Self {
        Self {
            role: "user".to_string(),
            content: content.into(),
        }
    }

    pub fn assistant(content: impl Into<String>) -> Self {
        Self {
            role: "assistant".to_string(),
            content: content.into(),
        }
    }
}
```

---

## Step 3: Define Capabilities

**File: `src/harness/capabilities.rs`** (NEW)

```rust
use serde::{Deserialize, Serialize};
use std::cmp::Ordering;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Capabilities {
    pub supports_chat: bool,
    pub supports_completion: bool,
    pub supports_embeddings: bool,
    pub supports_json_output: bool,
    pub supports_structured_output: bool,
    pub latency_class: LatencyClass,
    pub cost_per_1m_tokens: f64,  // USD for 1M tokens
    pub stream_support: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum LatencyClass {
    #[serde(rename = "low")]
    Low,      // Local: Ollama, LM Studio, Llamafile
    #[serde(rename = "medium")]
    Medium,   // CLI: Claude
    #[serde(rename = "high")]
    High,     // Remote API: OpenAI
}

impl Capabilities {
    pub fn for_claude() -> Self {
        Self {
            supports_chat: true,
            supports_completion: true,
            supports_embeddings: false,
            supports_json_output: true,
            supports_structured_output: true,
            latency_class: LatencyClass::Medium,
            cost_per_1m_tokens: 30.0,  // Approximate for Sonnet
            stream_support: false,     // Not easily via CLI
        }
    }

    pub fn for_ollama() -> Self {
        Self {
            supports_chat: true,
            supports_completion: true,
            supports_embeddings: false,
            supports_json_output: true,
            supports_structured_output: false,
            latency_class: LatencyClass::Low,
            cost_per_1m_tokens: 0.0,
            stream_support: true,
        }
    }

    pub fn for_lm_studio() -> Self {
        Self {
            supports_chat: true,
            supports_completion: true,
            supports_embeddings: true,
            supports_json_output: true,
            supports_structured_output: false,
            latency_class: LatencyClass::Low,
            cost_per_1m_tokens: 0.0,
            stream_support: true,
        }
    }

    pub fn for_llamafile() -> Self {
        Self {
            supports_chat: true,
            supports_completion: true,
            supports_embeddings: false,
            supports_json_output: true,
            supports_structured_output: false,
            latency_class: LatencyClass::Low,
            cost_per_1m_tokens: 0.0,
            stream_support: true,
        }
    }

    pub fn for_openai() -> Self {
        Self {
            supports_chat: true,
            supports_completion: true,
            supports_embeddings: true,
            supports_json_output: true,
            supports_structured_output: true,
            latency_class: LatencyClass::High,
            cost_per_1m_tokens: 150.0,  // GPT-4o approximate
            stream_support: true,
        }
    }
}
```

---

## Step 4: Implement Claude Handler

**File: `src/harness/claude.rs`** (NEW)

```rust
use crate::harness::{
    handler::{HarnessHandler, HarnessType, Message, ModelInfo},
    HarnessConfig,
};
use anyhow::Result;
use async_trait::async_trait;
use serde_json::{json, Value};
use std::path::PathBuf;
use std::process::Stdio;
use tokio::io::AsyncWriteExt;
use tokio::process::Command;

pub struct ClaudeHandler {
    pub path: PathBuf,
    pub version: Option<String>,
    config: HarnessConfig,
}

impl ClaudeHandler {
    pub fn new(path: PathBuf, version: Option<String>) -> Self {
        Self {
            path,
            version,
            config: HarnessConfig {
                name: "Claude CLI".to_string(),
                harness_type: "claude".to_string(),
                endpoint: None,
                model: None,
                enabled: true,
            },
        }
    }

    async fn run_claude_command(&self, prompt: &str) -> Result<String> {
        let mut child = Command::new(&self.path)
            .arg("-p")
            .arg(prompt)
            .arg("--output-format")
            .arg("json")
            .arg("--max-turns")
            .arg("1")
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?;

        let output = child.wait_with_output().await?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("Claude CLI failed: {}", stderr);
        }

        let response: Value = serde_json::from_slice(&output.stdout)?;

        // Extract text from response
        Ok(response["text"]
            .as_str()
            .or_else(|| response.get("message").and_then(|m| m.as_str()))
            .unwrap_or("")
            .to_string())
    }
}

#[async_trait]
impl HarnessHandler for ClaudeHandler {
    fn harness_type(&self) -> HarnessType {
        HarnessType::Claude
    }

    fn name(&self) -> &str {
        "Claude CLI"
    }

    async fn is_available(&self) -> bool {
        match Command::new(&self.path)
            .arg("--version")
            .output()
            .await
        {
            Ok(output) => output.status.success(),
            Err(_) => false,
        }
    }

    async fn version(&self) -> Option<String> {
        self.version.clone()
    }

    async fn list_models(&self) -> Result<Vec<ModelInfo>> {
        // Claude CLI manages models internally
        // Return known Claude models
        Ok(vec![
            ModelInfo {
                name: "claude-opus-4-5".to_string(),
                size: None,
                available: true,
                quantization: None,
                context_window: Some(200_000),
            },
            ModelInfo {
                name: "claude-sonnet-4-5".to_string(),
                size: None,
                available: true,
                quantization: None,
                context_window: Some(200_000),
            },
            ModelInfo {
                name: "claude-haiku-4-5".to_string(),
                size: None,
                available: true,
                quantization: None,
                context_window: Some(200_000),
            },
        ])
    }

    async fn synthesize(
        &self,
        _model: &str,
        system_prompt: &str,
        user_prompt: &str,
    ) -> Result<String> {
        let full_prompt = if system_prompt.is_empty() {
            user_prompt.to_string()
        } else {
            format!("{}\n\n{}", system_prompt, user_prompt)
        };

        self.run_claude_command(&full_prompt).await
    }

    async fn chat(
        &self,
        _model: &str,
        messages: Vec<Message>,
    ) -> Result<String> {
        let prompt = messages
            .iter()
            .map(|m| {
                if m.role == "system" {
                    format!("System: {}", m.content)
                } else if m.role == "user" {
                    format!("User: {}", m.content)
                } else {
                    format!("Assistant: {}", m.content)
                }
            })
            .collect::<Vec<_>>()
            .join("\n\n");

        self.run_claude_command(&prompt).await
    }

    fn config(&self) -> HarnessConfig {
        self.config.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    #[ignore] // Only run with `cargo test -- --ignored --nocapture`
    async fn test_claude_available() {
        if which::which("claude").is_ok() {
            let handler = ClaudeHandler::new(which::which("claude").unwrap(), None);
            assert!(handler.is_available().await);
        }
    }

    #[tokio::test]
    #[ignore]
    async fn test_claude_synthesize() {
        if which::which("claude").is_ok() {
            let handler = ClaudeHandler::new(which::which("claude").unwrap(), None);
            let result = handler
                .synthesize("", "You are a helpful assistant", "Say hello")
                .await;
            assert!(result.is_ok());
        }
    }
}
```

---

## Step 5: Implement Ollama Handler

**File: `src/harness/ollama.rs`** (NEW)

```rust
use crate::harness::{
    handler::{HarnessHandler, HarnessType, Message, ModelInfo},
    HarnessConfig,
};
use anyhow::Result;
use async_trait::async_trait;
use serde_json::{json, Value};
use std::time::Duration;

pub struct OllamaHandler {
    endpoint: String,
    client: reqwest::Client,
    config: HarnessConfig,
}

impl OllamaHandler {
    pub fn new(endpoint: String) -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(300))
            .build()
            .unwrap();

        Self {
            endpoint,
            client,
            config: HarnessConfig {
                name: "Ollama".to_string(),
                harness_type: "ollama".to_string(),
                endpoint: Some(endpoint.clone()),
                model: None,
                enabled: true,
            },
        }
    }

    fn endpoint(&self) -> &str {
        &self.endpoint
    }

    async fn get_models_raw(&self) -> Result<Value> {
        let response = self.client
            .get(format!("{}/api/tags", self.endpoint()))
            .timeout(Duration::from_secs(5))
            .send()
            .await?;

        if !response.status().is_success() {
            anyhow::bail!("Failed to fetch Ollama models: {}", response.status());
        }

        Ok(response.json().await?)
    }
}

#[async_trait]
impl HarnessHandler for OllamaHandler {
    fn harness_type(&self) -> HarnessType {
        HarnessType::Ollama
    }

    fn name(&self) -> &str {
        "Ollama"
    }

    async fn is_available(&self) -> bool {
        self.test_connection().await.is_ok()
    }

    async fn version(&self) -> Option<String> {
        // Ollama doesn't expose version via API
        None
    }

    async fn list_models(&self) -> Result<Vec<ModelInfo>> {
        let body = self.get_models_raw().await?;

        let models = body["models"]
            .as_array()
            .unwrap_or(&vec![])
            .iter()
            .map(|m| ModelInfo {
                name: m["name"].as_str().unwrap_or("unknown").to_string(),
                size: m["size"]
                    .as_u64()
                    .map(|s| format!("{:.2}GB", s as f64 / 1_000_000_000.0)),
                available: true,
                quantization: m["details"]["quantization_level"]
                    .as_str()
                    .map(|q| q.to_string()),
                context_window: m["details"]["parameter_size"]
                    .as_str()
                    .and_then(|p| {
                        if p.contains("7B") {
                            Some(3_072)
                        } else if p.contains("13B") {
                            Some(4_096)
                        } else if p.contains("70B") {
                            Some(8_192)
                        } else {
                            None
                        }
                    }),
            })
            .collect();

        Ok(models)
    }

    async fn synthesize(
        &self,
        model: &str,
        system_prompt: &str,
        user_prompt: &str,
    ) -> Result<String> {
        let prompt = if system_prompt.is_empty() {
            user_prompt.to_string()
        } else {
            format!("{}\n\n{}", system_prompt, user_prompt)
        };

        let request = json!({
            "model": model,
            "prompt": prompt,
            "format": "json",
            "stream": false,
        });

        let response = self.client
            .post(format!("{}/api/generate", self.endpoint()))
            .json(&request)
            .timeout(Duration::from_secs(300))
            .send()
            .await?;

        let body: Value = response.json().await?;
        Ok(body["response"]
            .as_str()
            .unwrap_or("")
            .to_string())
    }

    async fn chat(
        &self,
        model: &str,
        messages: Vec<Message>,
    ) -> Result<String> {
        let request = json!({
            "model": model,
            "messages": messages
                .iter()
                .map(|m| json!({
                    "role": m.role,
                    "content": m.content
                }))
                .collect::<Vec<_>>(),
            "stream": false,
        });

        let response = self.client
            .post(format!("{}/api/chat", self.endpoint()))
            .json(&request)
            .timeout(Duration::from_secs(300))
            .send()
            .await?;

        let body: Value = response.json().await?;
        Ok(body["message"]["content"]
            .as_str()
            .unwrap_or("")
            .to_string())
    }

    async fn test_connection(&self) -> Result<()> {
        let response = self.client
            .get(format!("{}/api/tags", self.endpoint()))
            .timeout(Duration::from_secs(2))
            .send()
            .await?;

        if response.status().is_success() {
            Ok(())
        } else {
            anyhow::bail!("Ollama not responding ({})", response.status())
        }
    }

    fn config(&self) -> HarnessConfig {
        self.config.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    #[ignore]
    async fn test_ollama_connection() {
        let handler = OllamaHandler::new("http://localhost:11434".to_string());
        let result = handler.test_connection().await;
        println!("Ollama connection test: {:?}", result);
    }

    #[tokio::test]
    #[ignore]
    async fn test_ollama_list_models() {
        let handler = OllamaHandler::new("http://localhost:11434".to_string());
        if handler.is_available().await {
            let models = handler.list_models().await.unwrap();
            println!("Available models: {:?}", models);
            assert!(!models.is_empty());
        }
    }
}
```

---

## Step 6: Create Router

**File: `src/harness/router.rs`** (NEW)

```rust
use crate::harness::capabilities::Capabilities;
use crate::harness::handler::HarnessHandler;
use anyhow::Result;
use ordered_float::OrderedFloat;

pub struct HarnessRouter {
    handlers: Vec<(String, Box<dyn HarnessHandler>, Capabilities)>,
}

impl HarnessRouter {
    pub fn new(handlers: Vec<(String, Box<dyn HarnessHandler>, Capabilities)>) -> Self {
        Self { handlers }
    }

    /// Get best harness for synthesis (quality > latency > cost)
    pub fn route_synthesis(&self) -> Option<(&str, &dyn HarnessHandler)> {
        self.handlers
            .iter()
            .filter(|(_, _, caps)| caps.supports_json_output)
            .min_by_key(|(_, _, caps)| {
                (
                    // Prefer structured output
                    !caps.supports_structured_output,
                    // Then prefer lower latency
                    caps.latency_class,
                    // Then prefer lower cost
                    OrderedFloat(caps.cost_per_1m_tokens),
                )
            })
            .map(|(name, h, _)| (name.as_str(), h.as_ref()))
    }

    /// Get best harness for RAG queries (speed > cost)
    pub fn route_rag(&self) -> Option<(&str, &dyn HarnessHandler)> {
        self.handlers
            .iter()
            .filter(|(_, _, caps)| caps.supports_chat)
            .min_by_key(|(_, _, caps)| caps.latency_class)
            .map(|(name, h, _)| (name.as_str(), h.as_ref()))
    }

    /// Get fallback chain for synthesis
    pub fn fallback_chain_synthesis(&self) -> Vec<(&str, &dyn HarnessHandler)> {
        let mut chain: Vec<_> = self.handlers
            .iter()
            .filter(|(_, _, caps)| caps.supports_json_output)
            .collect();

        chain.sort_by_key(|(_, _, caps)| {
            (
                !caps.supports_structured_output,
                caps.latency_class,
                OrderedFloat(caps.cost_per_1m_tokens),
            )
        });

        chain
            .into_iter()
            .map(|(name, h, _)| (name.as_str(), h.as_ref()))
            .collect()
    }

    /// Get all available handlers
    pub fn handlers(&self) -> Vec<(&str, &dyn HarnessHandler)> {
        self.handlers
            .iter()
            .map(|(name, h, _)| (name.as_str(), h.as_ref()))
            .collect()
    }

    /// Get handler by name
    pub fn get_by_name(&self, name: &str) -> Option<&dyn HarnessHandler> {
        self.handlers
            .iter()
            .find(|(n, _, _)| n == name)
            .map(|(_, h, _)| h.as_ref())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_router_selection() {
        // Mock test (requires mock handlers)
        // Would test routing logic
    }
}
```

---

## Step 7: Update Harness Module

**File: `src/harness/mod.rs`** (MODIFY)

```rust
pub mod capabilities;
pub mod config;
pub mod detect;
pub mod handler;

// New modules
pub mod claude;
pub mod llamafile;
pub mod ollama;
pub mod openai;
pub mod lm_studio;
pub mod factory;
pub mod router;

pub use capabilities::Capabilities;
pub use config::HarnessConfig;
pub use detect::{detect_harnesses, HarnessInfo};
pub use handler::{HarnessHandler, HarnessType, Message, ModelInfo};
pub use router::HarnessRouter;

// Re-export for convenience
pub use claude::ClaudeHandler;
pub use ollama::OllamaHandler;
```

---

## Step 8: Integration Example

**How to use in synthesis pipeline:**

```rust
// src/synthesis/synthesize.rs

use crate::harness::{HarnessRouter, Capabilities};

pub async fn synthesize_worldview(
    clusters: &ClusterResult,
    extraction: &Extraction,
    subject: &str,
) -> Result<Worldview> {
    // Detect all available harnesses
    let harnesses = detect_and_create_handlers().await?;
    let router = HarnessRouter::new(harnesses);

    // Try primary handler, then fallback
    for (name, handler) in router.fallback_chain_synthesis() {
        eprintln!("Attempting synthesis with {}", name);

        let models = match handler.list_models().await {
            Ok(m) if !m.is_empty() => m,
            _ => continue,
        };

        let model = &models[0].name;
        let system_prompt = build_system_prompt();
        let user_prompt = build_user_prompt(clusters, extraction, subject);

        match handler.synthesize(model, &system_prompt, &user_prompt).await {
            Ok(response) => {
                return parse_worldview(&response);
            }
            Err(e) => {
                eprintln!("  Failed: {}", e);
                continue;
            }
        }
    }

    anyhow::bail!("No harness available for synthesis")
}

async fn detect_and_create_handlers() -> Result<Vec<(String, Box<dyn HarnessHandler>, Capabilities)>> {
    let detected = detect_harnesses();
    let config = HarnessConfig::load()?;

    let mut handlers = vec![];

    for harness_info in detected {
        match create_handler(&harness_info, &config).await {
            Ok((name, handler, caps)) => {
                if handler.is_available().await {
                    handlers.push((name, handler, caps));
                }
            }
            Err(e) => {
                eprintln!("Failed to create handler for {:?}: {}", harness_info.harness_type, e);
            }
        }
    }

    Ok(handlers)
}

async fn create_handler(
    harness_info: &HarnessInfo,
    config: &HarnessConfig,
) -> Result<(String, Box<dyn HarnessHandler>, Capabilities)> {
    match harness_info.harness_type {
        HarnessType::Claude => {
            let handler = Box::new(ClaudeHandler::new(
                PathBuf::from(&harness_info.path),
                harness_info.version.clone(),
            ));
            Ok((
                "claude".to_string(),
                handler,
                Capabilities::for_claude(),
            ))
        }
        HarnessType::Ollama => {
            let endpoint = config
                .harnesses
                .iter()
                .find(|h| h.harness_type == "ollama")
                .and_then(|h| h.endpoint.clone())
                .or_else(|| std::env::var("OLLAMA_HOST").ok())
                .unwrap_or_else(|_| "http://localhost:11434".to_string());

            let handler = Box::new(OllamaHandler::new(endpoint));
            Ok((
                "ollama".to_string(),
                handler,
                Capabilities::for_ollama(),
            ))
        }
        // ... other harnesses
        _ => anyhow::bail!("Unsupported harness: {:?}", harness_info.harness_type),
    }
}
```

---

## Step 9: Testing

**File: `src/harness/tests/mock.rs`** (NEW)

```rust
#[cfg(test)]
mod mock {
    use crate::harness::handler::{HarnessHandler, HarnessType, Message, ModelInfo};
    use crate::harness::HarnessConfig;
    use anyhow::Result;
    use async_trait::async_trait;

    pub struct MockHandler {
        pub responses: std::collections::HashMap<String, String>,
        pub should_fail: bool,
    }

    impl MockHandler {
        pub fn new() -> Self {
            Self {
                responses: std::collections::HashMap::new(),
                should_fail: false,
            }
        }

        pub fn with_response(mut self, prompt: &str, response: &str) -> Self {
            self.responses.insert(prompt.to_string(), response.to_string());
            self
        }
    }

    #[async_trait]
    impl HarnessHandler for MockHandler {
        fn harness_type(&self) -> HarnessType {
            HarnessType::Custom
        }

        fn name(&self) -> &str {
            "Mock"
        }

        async fn is_available(&self) -> bool {
            !self.should_fail
        }

        async fn version(&self) -> Option<String> {
            Some("1.0.0".to_string())
        }

        async fn list_models(&self) -> Result<Vec<ModelInfo>> {
            Ok(vec![ModelInfo {
                name: "mock-model".to_string(),
                size: None,
                available: true,
                quantization: None,
                context_window: Some(4096),
            }])
        }

        async fn synthesize(
            &self,
            _model: &str,
            _system_prompt: &str,
            user_prompt: &str,
        ) -> Result<String> {
            if self.should_fail {
                anyhow::bail!("Mock handler forced failure");
            }
            Ok(self
                .responses
                .get(user_prompt)
                .cloned()
                .unwrap_or_else(|| "Mock response".to_string()))
        }

        async fn chat(&self, _model: &str, _messages: Vec<Message>) -> Result<String> {
            Ok("Mock chat response".to_string())
        }

        fn config(&self) -> HarnessConfig {
            HarnessConfig {
                name: "Mock".to_string(),
                harness_type: "mock".to_string(),
                endpoint: None,
                model: None,
                enabled: true,
            }
        }
    }
}
```

---

## Implementation Checklist

- [ ] Add dependencies to Cargo.toml (async-trait, reqwest, etc.)
- [ ] Create `handler.rs` with trait definition
- [ ] Create `capabilities.rs` with capability definitions
- [ ] Implement `claude.rs` handler
- [ ] Implement `ollama.rs` handler
- [ ] Implement `lm_studio.rs` handler
- [ ] Implement `llamafile.rs` handler (optional)
- [ ] Implement `openai.rs` handler (optional)
- [ ] Create `router.rs` with routing logic
- [ ] Update `mod.rs` to export new modules
- [ ] Create `tests/mock.rs` for mock handlers
- [ ] Update synthesis pipeline to use router
- [ ] Add integration tests
- [ ] Test with actual Claude CLI
- [ ] Test with actual Ollama
- [ ] Update CLI with `--harness` option
- [ ] Update documentation

---

## Quick Start: Running Tests

```bash
# Run all tests (mocks only)
cargo test harness::

# Run with ignored tests (requires Ollama/Claude running)
cargo test harness:: -- --ignored --nocapture

# Run specific harness tests
cargo test harness::claude:: -- --ignored
cargo test harness::ollama:: -- --ignored

# Run router tests
cargo test harness::router::
```

---

## Integration Points

1. **Synthesis pipeline** → Use `HarnessRouter::route_synthesis()`
2. **RAG queries** → Use `HarnessRouter::route_rag()`
3. **CLI commands** → Add `--harness` option to specify which to use
4. **Configuration** → Load from `~/.wve/config.toml`
5. **Fallbacks** → Use `fallback_chain_*` methods for robustness

