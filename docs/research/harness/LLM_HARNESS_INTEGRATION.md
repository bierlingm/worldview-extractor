# LLM Harness Detection & Integration Research

**Date:** February 2026
**Context:** Worldview Extractor (wve) — Multi-harness support for synthesis, RAG, and analysis
**Status:** Comprehensive research document for implementation planning

---

## Executive Summary

This document covers:
1. **Current harness detection patterns** in the wve-rs Rust codebase
2. **LLM harness specifics** (Claude CLI, Ollama, LM Studio, OpenAI, vLLM, Llamafile)
3. **Trait-based abstraction patterns** for pluggable harness support
4. **Default Claude integration** strategies for zero-config usage
5. **Multi-harness pipeline routing** and fallback chains
6. **Factory/Droid pattern** context from the cass project

---

## Part 1: Current Harness Detection Architecture

### 1.1 Existing Detection Code in wve-rs

**Location:** `/Users/moritzbierling/werk/wield/weave/wve-rs/src/harness/detect.rs`

**Current Pattern:**
- Uses `which` crate to find binaries in PATH
- Executes `--version` flags to detect and retrieve version info
- Returns `HarnessInfo` struct with availability status

```rust
#[derive(Debug, Clone, Serialize)]
pub enum HarnessType {
    Claude,
    Ollama,
    Llm,
    OpenAI,
    Llamafile,
    LMStudio,
    Custom,
}

#[derive(Debug, Clone, Serialize)]
pub struct HarnessInfo {
    pub harness_type: HarnessType,
    pub name: String,
    pub version: Option<String>,
    pub path: String,
    pub available: bool,
}

pub fn detect_harnesses() -> Vec<HarnessInfo>
```

**Current Detections:**
1. **Claude CLI** → `which claude` + `claude --version`
2. **Ollama** → `which ollama` + `ollama --version` (stderr)
3. **LLM CLI** → `which llm` + `llm --version`
4. **OpenAI CLI** → `which openai` + `openai --version`
5. **Llamafile** → `which llamafile` (no version check)

**Configuration:**
- File: `/Users/moritzbierling/werk/wield/weave/wve-rs/src/harness/config.rs`
- Format: TOML stored in `~/.wve/config.toml`
- Supports per-harness configuration with name, type, endpoint, and model

**Key Insight:** Detection is currently binary-based (does the command exist?), not capability-based (can it actually respond to requests?).

---

## Part 2: LLM Harness Specifications

### 2.1 Claude CLI

**Detection:**
- Binary: `claude` in PATH
- Version check: `claude --version`
- No environment variables needed (uses system authentication)

**Key Capabilities:**
- Interactive mode: `claude` or `claude "query"`
- Print mode (non-interactive): `claude -p "query"` or `-p` flag
- Structured output: `--output-format json`
- Session persistence: `--continue/-c`, `--resume/-r`
- Model selection: `--model sonnet|opus`
- Fallback models: `--fallback-model`
- Streaming output: `--output-format stream-json`
- Budget limits: `--max-budget-usd`, `--max-turns`
- JSON schema validation: `--json-schema`
- Error handling: Exits with error on failure; structured JSON when `--output-format json`

**Integration Pattern (from CLI reference):**
```bash
# Direct prompt (non-interactive)
claude -p "your prompt" --output-format json

# With structured output validation
claude -p "prompt" --json-schema '{"type":"object","properties":{...}}'

# With budget/turn limits
claude -p "prompt" --output-format json --max-turns 3 --max-budget-usd 5.00

# Continue conversation
claude -c -p "follow-up question"
```

**Advantages:**
- Works out-of-the-box (no endpoint config needed)
- Supports latest Claude models automatically
- Native session management
- Structured output support
- Cost control via flags

**Disadvantages:**
- Requires Claude CLI installation
- Requires Anthropic authentication
- Each invocation is independent (no session reuse by default)

### 2.2 Ollama

**Detection:**
- Binary: `ollama` in PATH
- Version check: `ollama --version` (note: output is in stderr, not stdout)
- Environment variables:
  - `OLLAMA_HOST` (default: `http://127.0.0.1:11434`)
  - `OLLAMA_MODELS` (directory for model storage)
  - `OLLAMA_KEEP_ALIVE` (model unload timeout)
  - `OLLAMA_ORIGINS` (CORS origins)
  - `OLLAMA_FLASH_ATTENTION` (enable Flash Attention)

**API Endpoint:**
- Default: `http://localhost:11434/api/`
- Base endpoint detection: `GET /api/tags` (list models)
- Generation: `POST /api/generate`
- Chat: `POST /api/chat`

**Detection Pattern:**
```rust
// Test if service is running
GET http://localhost:11434/api/tags
// Returns JSON with available models
```

**Key Capabilities:**
- Run locally without internet
- Support for quantized models (saves memory)
- Model streaming for long outputs
- Context management
- GPU acceleration (CUDA, Metal, etc.)

**Model Detection:**
```bash
curl http://localhost:11434/api/tags
# Returns: {"models": [{"name": "mistral", "size": "...", ...}, ...]}
```

**Usage Pattern:**
```python
import ollama
client = ollama.Client(host="http://localhost:11434")
response = client.generate(model="llama3", prompt="...", format="json")
```

**Advantages:**
- Fully local (privacy preserving)
- Simple API (OpenAI-like format available)
- Good model variety
- Streaming support

**Disadvantages:**
- Requires local compute power
- Model download time
- Slow on CPU-only systems
- Server must be running separately

### 2.3 LM Studio

**Detection:**
- Binary: `lms` in PATH
- Version check: `lms --version`
- Default server: `http://localhost:1234`
- Environment variables: None standard (uses LM Studio's internal config)

**API Endpoints:**
- Models: `GET /api/v0/models` (list models with metadata)
- Chat completions: `POST /api/v0/chat/completions` (OpenAI-compatible)
- Completions: `POST /api/v0/completions` (text generation)
- Embeddings: `POST /api/v0/embeddings` (embedding generation)

**Detection Pattern:**
```bash
# Simple connectivity check
curl http://localhost:1234/api/v0/models

# Returns JSON with available models
```

**Key Capabilities:**
- Desktop app with GUI (user-friendly)
- OpenAI API compatibility
- Multi-format support (chat, completions, embeddings)
- Model detection through API
- Automatic quantization

**Advantages:**
- GUI for model management
- OpenAI-compatible API (no special library)
- Works well on consumer hardware
- Good documentation

**Disadvantages:**
- Desktop application required
- Windows/Mac/Linux support varies
- No native CLI (though has `lms` CLI tool)
- Requires manual model loading through GUI typically

### 2.4 vLLM

**Detection:**
- Binary: `python -m vllm.entrypoints.openai.api_server` (not PATH-discoverable)
- Version check: Via Python package metadata
- Default server: `http://localhost:8000` (configurable with `--host`, `--port`)
- Environment variables:
  - `VLLM_HOST` (not standard, but configurable at launch)
  - `VLLM_PORT` (configurable)

**API Endpoints:**
- OpenAI-compatible: `POST /v1/chat/completions`
- Model list: `GET /v1/models`
- Completions: `POST /v1/completions`

**Detection Pattern:**
```bash
# Check if service is running
curl http://localhost:8000/v1/models

# Requires explicit host/port knowledge
```

**Key Capabilities:**
- OpenAI API compatibility (drop-in replacement)
- High-performance serving (tensor parallelism, batching)
- Structured output support
- Vision support (multimodal)

**Advantages:**
- OpenAI-compatible (works with existing clients)
- Excellent performance
- Production-ready
- Advanced features (guided generation, etc.)

**Disadvantages:**
- Not discoverable by PATH (starts as Python script)
- Requires port configuration knowledge
- Complex setup for high-performance scenarios
- Less user-friendly than Ollama

### 2.5 Llamafile

**Detection:**
- Binary: `llamafile` in PATH
- Version check: Limited (no --version flag traditionally)
- Default server: `http://localhost:8080` (or custom with `-p`)
- Environment variables:
  - `LLAMAFILE_PORT` (custom port)
  - `LLAMAFILE_GPU` (enable GPU)

**API Endpoints:**
- OpenAI-compatible: `POST /v1/chat/completions`
- Model list: `GET /v1/models`

**Detection Pattern:**
```bash
# Test if service is running
curl http://localhost:8080/v1/models
```

**Key Capabilities:**
- Single-file executable (no install needed)
- Includes weights (portable)
- OpenAI API compatibility
- Runs without system dependencies

**Advantages:**
- Extremely portable (single file)
- No dependencies
- Works offline
- Simple startup

**Disadvantages:**
- Limited model selection (bundled weights)
- Fixed models (can't swap easily)
- Slower than optimized frameworks

### 2.6 OpenAI API

**Detection:**
- Binary: `openai` CLI in PATH
- Version check: `openai --version`
- API Key: Required via `OPENAI_API_KEY` environment variable
- Default endpoint: `https://api.openai.com/v1/`

**API Endpoints:**
- Chat completions: `POST https://api.openai.com/v1/chat/completions`
- Model list: `GET https://api.openai.com/v1/models`

**Detection Pattern:**
```bash
# Verify credentials work
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Key Capabilities:**
- Cloud-based (no local compute)
- Latest models
- Vision, function calling, etc.
- Proven reliability

**Advantages:**
- No local compute needed
- Cutting-edge models
- Reliable API
- Easy integration

**Disadvantages:**
- Requires API key and internet
- Per-token cost
- Data sent to cloud
- Rate limiting

---

## Part 3: Detection Patterns & Strategies

### 3.1 Binary Detection (Current Approach)

**Strengths:**
- Fast (just PATH lookup)
- No false positives (if binary exists, it's installed)
- Works offline

**Weaknesses:**
- Doesn't verify server is running (Ollama, LM Studio might be installed but not started)
- Doesn't check version compatibility
- Environment variables may override binary location

**Pattern:**
```rust
fn detect_ollama() -> Option<HarnessInfo> {
    let path = which::which("ollama").ok()?;
    let output = Command::new("ollama").arg("--version").output().ok()?;
    // ...
}
```

### 3.2 Service Availability Testing (Recommended for remote services)

**Pattern:**
```rust
async fn test_harness_availability(harness: &HarnessInfo) -> bool {
    match harness.harness_type {
        HarnessType::Ollama => {
            // Test connectivity to http://localhost:11434/api/tags
            test_http_endpoint("http://localhost:11434/api/tags").await
        }
        HarnessType::LMStudio => {
            test_http_endpoint("http://localhost:1234/api/v0/models").await
        }
        HarnessType::Llamafile => {
            test_http_endpoint("http://localhost:8080/v1/models").await
        }
        HarnessType::Claude => {
            // Test: `claude --version` with timeout
            test_command_execution("claude", &["--version"]).await
        }
        HarnessType::OpenAI => {
            // Test API key and connectivity
            test_openai_api_key().await
        }
        _ => true, // Unknown types
    }
}

async fn test_http_endpoint(url: &str) -> bool {
    reqwest::Client::new()
        .get(url)
        .timeout(Duration::from_secs(2))
        .send()
        .await
        .is_ok()
}
```

### 3.3 Environment Variable Detection

**Pattern for detecting endpoint overrides:**
```rust
fn get_harness_endpoint(harness_type: &HarnessType) -> String {
    match harness_type {
        HarnessType::Ollama => {
            std::env::var("OLLAMA_HOST")
                .unwrap_or_else(|_| "http://localhost:11434".to_string())
        }
        HarnessType::LMStudio => {
            // LM Studio doesn't have standard env var
            "http://localhost:1234".to_string()
        }
        HarnessType::Llamafile => {
            // Check for custom port
            let port = std::env::var("LLAMAFILE_PORT").unwrap_or("8080".to_string());
            format!("http://localhost:{}", port)
        }
        _ => String::new(),
    }
}
```

### 3.4 API Capability Detection

**After detecting a harness, test what it can do:**

```rust
async fn detect_capabilities(harness: &HarnessInfo) -> Capabilities {
    match harness.harness_type {
        HarnessType::Ollama => {
            let models = list_ollama_models(harness).await;
            Capabilities {
                supports_chat: true,
                supports_completion: true,
                supports_embeddings: false,
                available_models: models,
            }
        }
        HarnessType::LMStudio => {
            let models = list_lm_studio_models(harness).await;
            Capabilities {
                supports_chat: true,
                supports_completion: true,
                supports_embeddings: true,
                available_models: models,
            }
        }
        // ...
    }
}
```

---

## Part 4: Factory/Droid Context

### 4.1 What is Factory/Droid?

From the cass project (`/Users/moritzbierling/werk/keep/cass/src/connectors/factory.rs`):

**Factory** is an AI coding assistant (similar to Claude Code) that stores sessions in:
```
~/.factory/sessions/{workspace-path-slug}/{session-uuid}.jsonl
~/.factory/sessions/{workspace-path-slug}/{session-uuid}.settings.json
```

**Droid** appears to be the computation/execution backend (inferred from the "Compute hierarchy" in AGENTS.md):
```
Code → Local NLP → Local embeddings → Ollama → Droid
```

**Use Cases:**
- Factory sessions represent completed AI agent work (conversation logs)
- Droid would be a more sophisticated synthesis backend (could be Claude API, could be remote inference)
- Pattern shows hierarchical fallback: start local, graduate to more powerful systems

### 4.2 Integration Pattern Insight

The Factory connector shows a pattern:
1. **Detection** → Check if `~/.factory/sessions/` exists
2. **Scanning** → Walk directory tree for `.jsonl` files
3. **Parsing** → Extract messages, metadata, timestamps
4. **Normalization** → Convert to `NormalizedConversation`

**For wve**, the analogous pattern would be:
1. **Detection** → Check if harness binary/service exists
2. **Capability testing** → Verify it responds to API calls
3. **Model enumeration** → List available models
4. **Configuration** → Store in `~/.wve/config.toml`

---

## Part 5: Trait-Based Abstraction Architecture

### 5.1 Core Trait Design

```rust
// src/harness/handler.rs (new file)

use anyhow::Result;
use async_trait::async_trait;
use serde_json::{json, Value};

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

    /// Execute a synthesis prompt
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

    /// Test connectivity with a timeout
    async fn test_connection(&self) -> Result<()>;

    /// Get configuration if needed
    fn config(&self) -> HarnessConfig;
}

#[derive(Debug, Clone)]
pub struct ModelInfo {
    pub name: String,
    pub size: Option<String>,
    pub available: bool,
    pub quantization: Option<String>,
}

#[derive(Debug, Clone)]
pub struct Message {
    pub role: String,  // "system", "user", "assistant"
    pub content: String,
}
```

### 5.2 Concrete Implementations

**Claude Handler:**
```rust
pub struct ClaudeHandler {
    path: PathBuf,
    version: Option<String>,
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
        tokio::process::Command::new(&self.path)
            .arg("--version")
            .output()
            .await
            .is_ok()
    }

    async fn synthesize(
        &self,
        _model: &str,
        system_prompt: &str,
        user_prompt: &str,
    ) -> Result<String> {
        let full_prompt = format!("{}\n\n{}", system_prompt, user_prompt);

        let output = tokio::process::Command::new(&self.path)
            .arg("-p")
            .arg(&full_prompt)
            .arg("--output-format")
            .arg("json")
            .arg("--max-turns")
            .arg("1")
            .output()
            .await?;

        if !output.status.success() {
            anyhow::bail!(
                "Claude execution failed: {}",
                String::from_utf8_lossy(&output.stderr)
            );
        }

        // Parse JSON response
        let response: Value = serde_json::from_slice(&output.stdout)?;
        Ok(response["text"].as_str().unwrap_or("").to_string())
    }

    async fn chat(
        &self,
        _model: &str,
        messages: Vec<Message>,
    ) -> Result<String> {
        // Convert to prompt format
        let prompt = messages
            .iter()
            .map(|m| format!("{}: {}", m.role, m.content))
            .collect::<Vec<_>>()
            .join("\n\n");

        let output = tokio::process::Command::new(&self.path)
            .arg("-p")
            .arg(&prompt)
            .arg("--output-format")
            .arg("json")
            .output()
            .await?;

        let response: Value = serde_json::from_slice(&output.stdout)?;
        Ok(response["text"].as_str().unwrap_or("").to_string())
    }

    async fn list_models(&self) -> Result<Vec<ModelInfo>> {
        // Claude doesn't expose model list, return known versions
        Ok(vec![
            ModelInfo {
                name: "claude-opus-4-5".to_string(),
                size: None,
                available: true,
                quantization: None,
            },
            ModelInfo {
                name: "claude-sonnet-4-5".to_string(),
                size: None,
                available: true,
                quantization: None,
            },
        ])
    }

    async fn test_connection(&self) -> Result<()> {
        let output = tokio::process::Command::new(&self.path)
            .arg("--version")
            .output()
            .await?;

        if output.status.success() {
            Ok(())
        } else {
            anyhow::bail!("Claude CLI not responding")
        }
    }

    fn config(&self) -> HarnessConfig {
        HarnessConfig {
            name: "Claude CLI".to_string(),
            harness_type: "claude".to_string(),
            endpoint: None,
            model: None,
            enabled: true,
        }
    }
}
```

**Ollama Handler:**
```rust
pub struct OllamaHandler {
    endpoint: String,  // http://localhost:11434
    client: reqwest::Client,
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

    async fn synthesize(
        &self,
        model: &str,
        system_prompt: &str,
        user_prompt: &str,
    ) -> Result<String> {
        let prompt = format!("{}\n\n{}", system_prompt, user_prompt);

        let request = json!({
            "model": model,
            "prompt": prompt,
            "format": "json",
            "stream": false,
        });

        let response = self.client
            .post(format!("{}/api/generate", self.endpoint))
            .json(&request)
            .send()
            .await?;

        let body: Value = response.json().await?;
        Ok(body["response"].as_str().unwrap_or("").to_string())
    }

    async fn chat(
        &self,
        model: &str,
        messages: Vec<Message>,
    ) -> Result<String> {
        let request = json!({
            "model": model,
            "messages": messages.iter().map(|m| json!({
                "role": m.role,
                "content": m.content
            })).collect::<Vec<_>>(),
            "stream": false,
        });

        let response = self.client
            .post(format!("{}/api/chat", self.endpoint))
            .json(&request)
            .send()
            .await?;

        let body: Value = response.json().await?;
        Ok(body["message"]["content"]
            .as_str()
            .unwrap_or("")
            .to_string())
    }

    async fn list_models(&self) -> Result<Vec<ModelInfo>> {
        let response = self.client
            .get(format!("{}/api/tags", self.endpoint))
            .send()
            .await?;

        let body: Value = response.json().await?;
        let models = body["models"]
            .as_array()
            .unwrap_or(&vec![])
            .iter()
            .map(|m| ModelInfo {
                name: m["name"].as_str().unwrap_or("unknown").to_string(),
                size: m["size"].as_str().map(|s| s.to_string()),
                available: true,
                quantization: None,
            })
            .collect();

        Ok(models)
    }

    async fn test_connection(&self) -> Result<()> {
        let response = self.client
            .get(format!("{}/api/tags", self.endpoint))
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
        HarnessConfig {
            name: "Ollama".to_string(),
            harness_type: "ollama".to_string(),
            endpoint: Some(self.endpoint.clone()),
            model: None,
            enabled: true,
        }
    }
}
```

**Similar implementations for LM Studio, vLLM, Llamafile, OpenAI...**

### 5.3 Factory Pattern for Handler Creation

```rust
// src/harness/factory.rs (new file)

pub struct HarnessFactory;

impl HarnessFactory {
    pub async fn create_handler(
        harness_info: &HarnessInfo,
        config: &HarnessConfig,
    ) -> Result<Box<dyn HarnessHandler>> {
        match harness_info.harness_type {
            HarnessType::Claude => {
                let handler = ClaudeHandler {
                    path: PathBuf::from(&harness_info.path),
                    version: harness_info.version.clone(),
                };
                Ok(Box::new(handler))
            }
            HarnessType::Ollama => {
                let endpoint = config.endpoint.clone()
                    .or_else(|| std::env::var("OLLAMA_HOST").ok())
                    .unwrap_or_else(|_| "http://localhost:11434".to_string());

                let handler = OllamaHandler {
                    endpoint,
                    client: reqwest::Client::new(),
                };
                Ok(Box::new(handler))
            }
            HarnessType::LMStudio => {
                let endpoint = config.endpoint.clone()
                    .unwrap_or_else(|_| "http://localhost:1234".to_string());

                let handler = LMStudioHandler {
                    endpoint,
                    client: reqwest::Client::new(),
                };
                Ok(Box::new(handler))
            }
            // ... other harnesses
            _ => anyhow::bail!("Unsupported harness type"),
        }
    }

    pub async fn detect_and_create() -> Result<Vec<Box<dyn HarnessHandler>>> {
        let detected = detect_harnesses();
        let config = HarnessConfig::load()?;

        let mut handlers = vec![];
        for harness_info in detected {
            if let Ok(handler) = Self::create_handler(&harness_info, &config).await {
                if handler.is_available().await {
                    handlers.push(handler);
                }
            }
        }

        Ok(handlers)
    }
}
```

---

## Part 6: Configuration Architecture

### 6.1 TOML Configuration Format

```toml
# ~/.wve/config.toml

# Default harness for synthesis (Claude, Ollama, etc)
default_harness = "claude"

# Harnesses can be configured with custom endpoints, models, etc
[[harnesses]]
name = "claude-default"
harness_type = "claude"
# No endpoint needed - uses system auth
# model is managed by Claude CLI itself
enabled = true

[[harnesses]]
name = "ollama-local"
harness_type = "ollama"
endpoint = "http://localhost:11434"
model = "mistral"
enabled = true

[[harnesses]]
name = "lm-studio-local"
harness_type = "lm-studio"
endpoint = "http://localhost:1234"
model = "mistral-7b"
enabled = true

[[harnesses]]
name = "llamafile-portable"
harness_type = "llamafile"
endpoint = "http://localhost:8080"
enabled = false  # Disabled if not running

[[harnesses]]
name = "openai-api"
harness_type = "openai"
endpoint = "https://api.openai.com/v1"
# API key comes from OPENAI_API_KEY env var
model = "gpt-4o"
enabled = false
```

### 6.2 Environment Variable Precedence

1. **Harness endpoint overrides:**
   - `OLLAMA_HOST` → overrides harnesses[].endpoint for Ollama
   - `OPENAI_API_KEY` → required for OpenAI harness
   - `LLAMAFILE_PORT` → can override port

2. **Default harness:**
   - `WVE_DEFAULT_HARNESS` → overrides config file setting

3. **Claude-specific:**
   - `ANTHROPIC_API_KEY` → Claude CLI uses this automatically

---

## Part 7: Default Claude Integration (Zero-Config)

### 7.1 Strategy

Claude should work out-of-the-box without configuration:

1. **Detect at startup:** `which claude` (binary in PATH)
2. **Test connectivity:** `claude --version`
3. **Use as default:** Make Claude the default if available
4. **Fallback chain:** If Claude unavailable, try Ollama, then LM Studio

### 7.2 Implementation

```rust
// src/harness/default_handler.rs (new file)

pub struct DefaultHarnessManager;

impl DefaultHarnessManager {
    pub async fn get_default_handler() -> Result<Box<dyn HarnessHandler>> {
        let config = HarnessConfig::load().unwrap_or_default();

        // 1. Check explicit config
        if let Some(default_name) = &config.default_harness {
            if let Ok(handler) = Self::handler_by_name(default_name, &config).await {
                if handler.is_available().await {
                    return Ok(handler);
                }
            }
        }

        // 2. Fallback chain: Claude → Ollama → LM Studio
        let fallback_chain = vec!["claude", "ollama", "lm-studio"];

        for harness_name in fallback_chain {
            if let Ok(handler) = Self::handler_by_name(harness_name, &config).await {
                if handler.is_available().await {
                    return Ok(handler);
                }
            }
        }

        anyhow::bail!("No LLM harness available. Install Claude CLI, Ollama, or LM Studio.")
    }

    async fn handler_by_name(
        name: &str,
        config: &HarnessConfig,
    ) -> Result<Box<dyn HarnessHandler>> {
        // Detect specific harness
        let harness_info = match name {
            "claude" => detect_claude()?,
            "ollama" => detect_ollama()?,
            "lm-studio" => detect_lm_studio()?,
            _ => anyhow::bail!("Unknown harness: {}", name),
        };

        HarnessFactory::create_handler(&harness_info, config).await
    }
}

// Usage in synthesis
pub async fn synthesize_with_default(
    clusters: &ClusterResult,
    extraction: &Extraction,
) -> Result<Worldview> {
    let handler = DefaultHarnessManager::get_default_handler().await?;
    let model = handler.list_models().await?
        .first()
        .map(|m| m.name.clone())
        .ok_or_else(|| anyhow::anyhow!("No models available"))?;

    let prompt = build_synthesis_prompt(clusters, extraction);
    let response = handler.synthesize(&model, "", &prompt).await?;

    parse_worldview(&response)
}
```

### 7.3 Shell Integration

Ensure `claude` command is discoverable:

```bash
# In ~/.bashrc or ~/.zshrc
# Claude Code CLI is auto-installed and should be in PATH
# If not found, verify: which claude

# For system-wide installation (if needed):
# npm install -g @anthropic-ai/claude-code
# or: brew install anthropic/tap/claude-code
```

---

## Part 8: Multi-Harness Pipeline Routing

### 8.1 Route Different Tasks to Appropriate Harnesses

```rust
// src/harness/router.rs (new file)

pub struct HarnessRouter {
    handlers: Vec<(Box<dyn HarnessHandler>, Capabilities)>,
}

#[derive(Debug, Clone)]
pub struct Capabilities {
    pub supports_chat: bool,
    pub supports_completion: bool,
    pub supports_embeddings: bool,
    pub supports_json_output: bool,
    pub supports_structured_output: bool,
    pub latency_class: LatencyClass,  // Low, Medium, High
    pub cost_per_token: f64,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub enum LatencyClass {
    Low,      // Local (Ollama, LM Studio, Llamafile)
    Medium,   // Claude CLI
    High,     // Remote API (OpenAI)
}

impl HarnessRouter {
    pub async fn new() -> Result<Self> {
        let handlers = HarnessFactory::detect_and_create().await?;

        let mut router_handlers = vec![];
        for handler in handlers {
            let caps = Self::detect_capabilities(&*handler).await;
            router_handlers.push((handler, caps));
        }

        Ok(HarnessRouter {
            handlers: router_handlers,
        })
    }

    async fn detect_capabilities(handler: &dyn HarnessHandler) -> Capabilities {
        match handler.harness_type() {
            HarnessType::Claude => Capabilities {
                supports_chat: true,
                supports_completion: true,
                supports_embeddings: false,
                supports_json_output: true,
                supports_structured_output: true,
                latency_class: LatencyClass::Medium,
                cost_per_token: 0.00003,  // Approximate
            },
            HarnessType::Ollama => Capabilities {
                supports_chat: true,
                supports_completion: true,
                supports_embeddings: false,
                supports_json_output: true,
                supports_structured_output: false,
                latency_class: LatencyClass::Low,
                cost_per_token: 0.0,
            },
            HarnessType::LMStudio => Capabilities {
                supports_chat: true,
                supports_completion: true,
                supports_embeddings: true,
                supports_json_output: true,
                supports_structured_output: false,
                latency_class: LatencyClass::Low,
                cost_per_token: 0.0,
            },
            HarnessType::OpenAI => Capabilities {
                supports_chat: true,
                supports_completion: true,
                supports_embeddings: true,
                supports_json_output: true,
                supports_structured_output: true,
                latency_class: LatencyClass::High,
                cost_per_token: 0.00015,
            },
            _ => Capabilities {
                supports_chat: false,
                supports_completion: false,
                supports_embeddings: false,
                supports_json_output: false,
                supports_structured_output: false,
                latency_class: LatencyClass::High,
                cost_per_token: 0.0,
            },
        }
    }

    // Route to best harness for synthesis (quality, then latency, then cost)
    pub fn route_synthesis(&self) -> Option<&dyn HarnessHandler> {
        self.handlers
            .iter()
            .filter(|(_, caps)| caps.supports_json_output)
            .min_by_key(|(_, caps)| (
                // Prefer structured output support
                !caps.supports_structured_output,
                // Then prefer lower latency (local > remote)
                caps.latency_class.clone(),
                // Then prefer lower cost
                OrderedFloat(caps.cost_per_token),
            ))
            .map(|(h, _)| h.as_ref())
    }

    // Route to best harness for RAG queries (speed over cost)
    pub fn route_rag_query(&self) -> Option<&dyn HarnessHandler> {
        self.handlers
            .iter()
            .filter(|(_, caps)| caps.supports_chat)
            .min_by_key(|(_, caps)| {
                // Prefer low latency for interactive queries
                caps.latency_class.clone()
            })
            .map(|(h, _)| h.as_ref())
    }

    // Route to best harness for embeddings (if available)
    pub fn route_embeddings(&self) -> Option<&dyn HarnessHandler> {
        self.handlers
            .iter()
            .find(|(_, caps)| caps.supports_embeddings)
            .map(|(h, _)| h.as_ref())
    }

    // Get fallback chain for robustness
    pub fn fallback_chain_for_synthesis(&self) -> Vec<&dyn HarnessHandler> {
        let mut chain: Vec<_> = self.handlers
            .iter()
            .filter(|(_, caps)| caps.supports_json_output)
            .map(|(h, _)| h.as_ref())
            .collect();

        // Sort by: structured_output > latency > cost
        chain.sort_by_key(|(_, caps)| (
            !caps.supports_structured_output,
            caps.latency_class.clone(),
            OrderedFloat(caps.cost_per_token),
        ));

        chain
    }
}

// Usage
pub async fn synthesize_with_routing(
    clusters: &ClusterResult,
    extraction: &Extraction,
) -> Result<Worldview> {
    let router = HarnessRouter::new().await?;

    // Try primary handler, fallback to others
    for handler in router.fallback_chain_for_synthesis() {
        if let Ok(response) = handler.synthesize(
            handler.list_models().await?.first().unwrap().name.as_str(),
            SYSTEM_PROMPT,
            &build_synthesis_prompt(clusters, extraction),
        ).await {
            return parse_worldview(&response);
        }
    }

    anyhow::bail!("All synthesis harnesses failed")
}
```

### 8.2 Cost/Performance Tradeoffs

**Quick Synthesis (speed > cost):**
```rust
router.route_rag_query()  // Local is fastest
```

**Quality Synthesis (quality > cost):**
```rust
router.route_synthesis()  // Structured output > latency
```

**High-Budget Synthesis (no cost constraints):**
```rust
router.handlers
    .iter()
    .filter(|(_, caps)| caps.supports_structured_output)
    .map(|(h, _)| h.as_ref())
    .next()
```

---

## Part 9: Implementation Roadmap

### Phase 1: Trait Definition (1-2 hours)
- [ ] Define `HarnessHandler` trait
- [ ] Define `Capabilities` struct
- [ ] Create `HarnessFactory`

### Phase 2: Claude Handler (1 hour)
- [ ] Implement `ClaudeHandler`
- [ ] Test with `claude -p` invocation
- [ ] Verify JSON output parsing

### Phase 3: Ollama Handler (1-2 hours)
- [ ] Implement `OllamaHandler`
- [ ] Add HTTP client (reqwest)
- [ ] Test model listing
- [ ] Test chat/completion API

### Phase 4: LM Studio Handler (1 hour)
- [ ] Implement `LMStudioHandler`
- [ ] Verify OpenAI-compatible endpoints

### Phase 5: Router & Fallback (2 hours)
- [ ] Implement `HarnessRouter`
- [ ] Add capability detection
- [ ] Create routing logic
- [ ] Test fallback chains

### Phase 6: Integration (2 hours)
- [ ] Update CLI to use router
- [ ] Update synthesis pipeline
- [ ] Update RAG pipeline
- [ ] Add `--harness` option to CLI

### Phase 7: Testing & Documentation (2 hours)
- [ ] Unit tests for each handler
- [ ] Integration tests
- [ ] Update README
- [ ] Update AGENTS.md

---

## Part 10: Key Implementation Patterns

### 10.1 Error Handling Strategy

```rust
// Different error levels for different harnesses
pub enum HarnessError {
    NotAvailable,        // Harness not installed/running
    TemporarilyUnavailable(String),  // Running but overloaded
    InvalidConfiguration(String),
    InvalidResponse(String),
    RateLimited,
}

// Distinguish between fatal and retriable errors
impl HarnessHandler {
    async fn synthesize_with_retry(
        &self,
        model: &str,
        system_prompt: &str,
        user_prompt: &str,
    ) -> Result<String> {
        for attempt in 1..=3 {
            match self.synthesize(model, system_prompt, user_prompt).await {
                Ok(result) => return Ok(result),
                Err(e) if e.is_retriable() => {
                    if attempt < 3 {
                        tokio::time::sleep(Duration::from_secs(2_u64.pow(attempt))).await;
                        continue;
                    }
                }
                Err(e) => return Err(e),
            }
        }
        anyhow::bail!("Failed after 3 retries")
    }
}
```

### 10.2 Connection Pooling for HTTP Harnesses

```rust
pub struct PooledOllamaHandler {
    endpoint: String,
    client: reqwest::Client,  // Connection pool included
    pool: Arc<Mutex<Vec<Ollama>>>,  // Optional connection pool
}

impl PooledOllamaHandler {
    pub fn new(endpoint: String) -> Self {
        let client = reqwest::Client::builder()
            .pool_connections(10)
            .pool_idle_timeout(Duration::from_secs(30))
            .timeout(Duration::from_secs(300))
            .build()
            .unwrap();

        Self {
            endpoint,
            client,
            pool: Arc::new(Mutex::new(Vec::new())),
        }
    }
}
```

### 10.3 Structured Output Validation

```rust
pub trait StructuredOutput {
    fn json_schema(&self) -> serde_json::Value;
    fn validate(&self, output: &str) -> Result<serde_json::Value>;
}

pub struct SynthesisOutput {
    // Define schema for worldview synthesis
}

impl StructuredOutput for SynthesisOutput {
    fn json_schema(&self) -> serde_json::Value {
        json!({
            "type": "object",
            "properties": {
                "points": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "theme": {"type": "string"},
                            "confidence": {"type": "number"},
                            "evidence": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                }
            },
            "required": ["points"]
        })
    }

    fn validate(&self, output: &str) -> Result<serde_json::Value> {
        let parsed: serde_json::Value = serde_json::from_str(output)?;
        // Validate against schema
        Ok(parsed)
    }
}
```

---

## Part 11: Testing Strategy

### 11.1 Mock Handlers for Testing

```rust
pub struct MockHandler {
    pub responses: HashMap<String, String>,
}

#[async_trait]
impl HarnessHandler for MockHandler {
    fn harness_type(&self) -> HarnessType {
        HarnessType::Custom
    }

    fn name(&self) -> &str {
        "Mock"
    }

    async fn synthesize(
        &self,
        _model: &str,
        _system_prompt: &str,
        user_prompt: &str,
    ) -> Result<String> {
        Ok(self.responses
            .get(user_prompt)
            .cloned()
            .unwrap_or_else(|| "Mock response".to_string()))
    }

    // ... other methods return test data
}
```

### 11.2 Integration Tests

```bash
# Test each harness locally
cargo test harness::tests::claude::* --features test-claude
cargo test harness::tests::ollama::* --features test-ollama
cargo test harness::tests::router::*
```

---

## Part 12: References & Resources

### Claude CLI
- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference)
- [Shipyard Claude Code Cheatsheet](https://shipyard.build/blog/claude-code-cheat-sheet/)

### Ollama
- [Ollama API Reference](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Ollama Environment Variables](https://www.arsturn.com/blog/setting-up-environment-variables-for-ollama)

### LM Studio
- [LM Studio REST API Endpoints](https://lmstudio.ai/docs/developer/rest/endpoints)
- [LM Studio Documentation](https://lmstudio.ai/docs/app)

### Other Tools
- [vLLM OpenAI Compatibility](https://www.glukhov.org/post/2026/01/vllm-quickstart/)
- [Llamafile Mozilla](https://github.com/Mozilla-Ocho/llamafile)
- [Complete Local LLM Guide 2026](https://www.glukhov.org/post/2025/11/hosting-llms-ollama-localai-jan-lmstudio-vllm-comparison/)

### Rust Patterns
- [async_trait](https://docs.rs/async-trait/)
- [reqwest HTTP client](https://docs.rs/reqwest/)
- [serde for serialization](https://docs.rs/serde/)

---

## Summary

This research provides a comprehensive blueprint for:

1. **Detection:** Binary + service availability + capability testing
2. **Abstraction:** Trait-based `HarnessHandler` with concrete implementations
3. **Configuration:** TOML-based with environment variable overrides
4. **Integration:** Default Claude support with fallback chains
5. **Routing:** Smart selection based on capabilities and constraints
6. **Testing:** Mock handlers and integration test patterns

The architecture supports:
- Zero-config Claude setup (works out-of-the-box)
- Multiple simultaneous harnesses (fallback chains)
- Cost/performance tradeoffs (choose what's optimal)
- Future extensibility (add new harnesses easily)
- Robust error handling (distinguish fatal vs retriable)

Implementation can proceed incrementally, testing each harness independently before wiring into the synthesis/RAG pipelines.
