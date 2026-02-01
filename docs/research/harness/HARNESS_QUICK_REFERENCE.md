# LLM Harness Quick Reference Card

## Harness Comparison Matrix

| Feature | Claude | Ollama | LM Studio | vLLM | Llamafile | OpenAI |
|---------|--------|--------|-----------|------|-----------|--------|
| **Detection** | `which claude` | `which ollama` | `lms --version` | Python pkg | `which llamafile` | `openai --version` |
| **Endpoint** | Subprocess | http://localhost:11434 | http://localhost:1234 | http://localhost:8000 | http://localhost:8080 | https://api.openai.com/v1 |
| **API Type** | CLI | REST JSON | OpenAI-compat | OpenAI-compat | OpenAI-compat | HTTPS REST |
| **Models** | Managed by CLI | User downloads | GUI management | Manual + config | Bundled | Cloud-hosted |
| **Cost** | Per token (API) | Free | Free | Free | Free | Per token |
| **Latency** | Medium (CLI) | Low (local) | Low (local) | Low (local) | Low (local) | High (cloud) |
| **Structured Output** | ✅ Yes | ✅ Yes | ⚠️ Limited | ✅ Yes | ⚠️ Limited | ✅ Yes |
| **Streaming** | ❌ No (CLI) | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Embeddings** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes |
| **Works Offline** | ⚠️ No (auth) | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Setup Complexity** | ⭐ (1 cmd) | ⭐⭐ (install + models) | ⭐⭐⭐ (GUI) | ⭐⭐⭐⭐ (complex) | ⭐ (1 file) | ⭐ (API key) |

## Environment Variables Cheat Sheet

```bash
# Claude CLI (uses system auth automatically)
export ANTHROPIC_API_KEY="sk-..."  # Optional, for manual override

# Ollama
export OLLAMA_HOST="http://127.0.0.1:11434"     # Default
export OLLAMA_MODELS="/path/to/models"           # Custom location
export OLLAMA_KEEP_ALIVE="5m"                   # Model unload timeout

# LM Studio
# No standard env vars (uses internal config)

# vLLM (example)
export VLLM_API_SERVER="http://localhost:8000"  # Not standard

# Llamafile
export LLAMAFILE_PORT="8080"                    # Custom port

# OpenAI
export OPENAI_API_KEY="sk-..."                  # Required
export OPENAI_API_BASE="https://api.openai.com/v1"  # Custom endpoint
```

## Detection Code Patterns

### Quick Detection (Binary Only)
```rust
// Fast, but doesn't verify service is running
if which::which("claude").is_ok() {
    println!("Claude CLI installed");
}
```

### Service Availability (HTTP)
```rust
// For remote services - verify they're actually running
async fn is_ollama_available() -> bool {
    reqwest::Client::new()
        .get("http://localhost:11434/api/tags")
        .timeout(Duration::from_secs(2))
        .send()
        .await
        .is_ok()
}
```

### Version Detection
```bash
# Claude
claude --version
# Output: Claude Code 1.0.0

# Ollama
ollama --version
# Output: ollama version X.X.X (stderr!)

# LM Studio
lms --version
# Output: lms version X.X.X

# OpenAI
openai --version
# Output: openai-cli/X.X.X
```

## API Endpoint Reference

### Claude CLI
```bash
# Simple invocation
claude -p "your prompt" --output-format json

# With system prompt
claude -p "system: help me
user: question" --output-format json

# With budget limits
claude -p "prompt" --output-format json --max-turns 1 --max-budget-usd 0.50

# With model selection
claude -p "prompt" --model opus --output-format json
```

### Ollama
```bash
# List models
curl http://localhost:11434/api/tags

# Generate text
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"mistral","prompt":"hello","stream":false}'

# Chat
curl -X POST http://localhost:11434/api/chat \
  -d '{"model":"mistral","messages":[{"role":"user","content":"hi"}]}'
```

### LM Studio
```bash
# List models
curl http://localhost:1234/api/v0/models

# Chat (OpenAI-compatible)
curl -X POST http://localhost:1234/api/v0/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"model-name","messages":[{"role":"user","content":"hi"}]}'
```

### vLLM
```bash
# List models
curl http://localhost:8000/v1/models

# Chat (OpenAI-compatible)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"model-id","messages":[{"role":"user","content":"hi"}]}'
```

### Llamafile
```bash
# List models
curl http://localhost:8080/v1/models

# Chat (OpenAI-compatible)
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"","messages":[{"role":"user","content":"hi"}]}'
```

### OpenAI
```bash
# List models
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Chat completions
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o","messages":[{"role":"user","content":"hi"}]}'
```

## Configuration File Format

**Location:** `~/.wve/config.toml`

```toml
# Default harness to use if multiple available
default_harness = "claude"

# Configure available harnesses
[[harnesses]]
name = "claude-default"
harness_type = "claude"
# No endpoint needed - uses CLI and system auth
# Models managed by Claude CLI
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
name = "openai-api"
harness_type = "openai"
endpoint = "https://api.openai.com/v1"
# API key comes from OPENAI_API_KEY env var
model = "gpt-4o"
enabled = false  # Disabled by default due to cost
```

## Routing Decision Tree

### For Synthesis (Quality First)
```
Needs JSON output?
├─ Yes: has structured_output support?
│  ├─ Yes: use Claude
│  └─ No: use Ollama
└─ No: use fastest available
```

### For RAG Queries (Speed First)
```
Latency preference?
├─ Low (interactive): use local (Ollama > LM Studio)
├─ Medium (batch): use Claude
└─ High (no constraint): use any available
```

### For Embeddings (Accuracy First)
```
Has embeddings support?
├─ Yes (LM Studio/OpenAI): use cheapest available
└─ No: fall back to sentence-transformers
```

## Fallback Chain Examples

### Default (Balanced)
```
1. Claude (best quality)
2. Ollama (local, free)
3. LM Studio (local, free)
4. OpenAI (cloud, expensive)
```

### Cost-Conscious
```
1. Ollama (free, local)
2. LM Studio (free, local)
3. Claude (small budget)
4. OpenAI (not used)
```

### Quality-First (No Cost Limit)
```
1. Claude (best all-rounder)
2. OpenAI (cutting-edge)
3. Ollama (backup)
```

## Rust Dependency Versions

```toml
async-trait = "0.1"
reqwest = { version = "0.12", features = ["json"] }
serde_json = "1"
tokio = { version = "1", features = ["full"] }
which = "5"
toml = "0.8"
ordered-float = "4.0"
```

## Common Error Handling

### Claude CLI Errors
```
"Claude execution failed: command not found"
→ Solution: Install Claude Code (npm i -g @anthropic-ai/claude-code)

"Claude execution failed: not authenticated"
→ Solution: Run `claude` once interactively to authenticate

"Claude execution failed: timeout"
→ Solution: Increase timeout or use --max-turns to limit work
```

### Ollama Errors
```
"Connection refused"
→ Solution: Start Ollama (ollama serve)

"Model not found: mistral"
→ Solution: Download model (ollama pull mistral)

"No such host"
→ Solution: Check OLLAMA_HOST env var (default localhost:11434)
```

### LM Studio Errors
```
"Connection refused: localhost:1234"
→ Solution: Start LM Studio and load a model

"No models available"
→ Solution: Load a model in LM Studio GUI first
```

### OpenAI Errors
```
"Invalid API key"
→ Solution: Set OPENAI_API_KEY env var

"Rate limited"
→ Solution: Reduce request frequency or upgrade account

"Context length exceeded"
→ Solution: Reduce prompt size or use different model
```

## Performance Characteristics

### Latency (per request)
| Harness | Cold Start | Warm Start | Notes |
|---------|-----------|-----------|-------|
| Claude | 500-2000ms | 500-1000ms | Network latency to Anthropic |
| Ollama | 100-500ms | 100-300ms | Depends on model size & GPU |
| LM Studio | 100-500ms | 100-300ms | Depends on model size & GPU |
| OpenAI | 500-2000ms | 500-1000ms | Network latency + queue |
| Llamafile | 200-800ms | 200-500ms | Single file, moderate speed |

### Memory Usage
| Harness | Process | Model | Total |
|---------|---------|-------|-------|
| Claude | ~100MB | N/A | ~100MB |
| Ollama | ~50MB | 4-32GB | 4GB-32GB+ |
| LM Studio | ~200MB | 4-32GB | 4GB-32GB+ |
| OpenAI | ~50MB | N/A | ~50MB (cloud) |
| Llamafile | ~100MB | 4-8GB | 4-8GB+ |

### Token Throughput
| Harness | Tokens/sec | Notes |
|---------|-----------|-------|
| Claude | 10-50 | Depends on load |
| Ollama | 5-20 | Depends on GPU |
| LM Studio | 5-20 | Depends on GPU |
| OpenAI | 20-100 | High throughput with batching |
| Llamafile | 2-10 | CPU-friendly but slower |

## Debugging Commands

```bash
# Check which harnesses are available
wve harnesses

# Test specific harness connection
wve config harnesses list

# See default configuration
cat ~/.wve/config.toml

# Override default for one command
wve --harness ollama synthesize ...

# Enable debug logging (if implemented)
WVE_DEBUG=1 wve synthesize ...

# Test Claude directly
claude -p "test" --output-format json

# Test Ollama directly
curl http://localhost:11434/api/tags

# Test LM Studio directly
curl http://localhost:1234/api/v0/models
```

## Migration Paths

### From Pure Ollama to Multi-Harness
1. Add HarnessHandler trait
2. Implement OllamaHandler
3. Update synthesize() to use handler.synthesize()
4. Add fallback to Claude if Ollama unavailable

### From Pure Claude to Multi-Harness
1. Add HarnessHandler trait
2. Implement ClaudeHandler
3. Update synthesize() to use handler.synthesize()
4. Add fallback to Ollama for high-volume scenarios

### Adding New Harness
1. Implement HarnessHandler trait
2. Add detection in detect_harnesses()
3. Add factory case for creating handler
4. Update config.toml template
5. Add tests

---

## Summary

**Out-of-the-box:** Claude works with zero config
**For local inference:** Install Ollama, use default config
**For GPU acceleration:** LM Studio or vLLM
**For production:** Claude + Ollama fallback
**For cost optimization:** Ollama + Claude as needed

See `LLM_HARNESS_INTEGRATION.md` for detailed specifications.
See `HARNESS_IMPLEMENTATION_GUIDE.md` for step-by-step implementation.
