use serde::Serialize;
use std::process::Command;

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

pub fn detect_harnesses() -> Vec<HarnessInfo> {
    let mut harnesses = vec![];

    if let Some(info) = detect_claude() {
        harnesses.push(info);
    }
    if let Some(info) = detect_ollama() {
        harnesses.push(info);
    }
    if let Some(info) = detect_llm() {
        harnesses.push(info);
    }
    if let Some(info) = detect_openai() {
        harnesses.push(info);
    }
    if let Some(info) = detect_llamafile() {
        harnesses.push(info);
    }

    harnesses
}

fn detect_claude() -> Option<HarnessInfo> {
    let path = which::which("claude").ok()?;
    let output = Command::new("claude").arg("--version").output().ok()?;
    let version = if output.status.success() {
        Some(String::from_utf8_lossy(&output.stdout).trim().to_string())
    } else {
        None
    };
    Some(HarnessInfo {
        harness_type: HarnessType::Claude,
        name: "Claude CLI".into(),
        version,
        path: path.to_string_lossy().into(),
        available: true,
    })
}

fn detect_ollama() -> Option<HarnessInfo> {
    let path = which::which("ollama").ok()?;
    let output = Command::new("ollama").arg("--version").output().ok()?;
    let version = if output.status.success() {
        Some(String::from_utf8_lossy(&output.stderr).trim().to_string())
    } else {
        None
    };
    Some(HarnessInfo {
        harness_type: HarnessType::Ollama,
        name: "Ollama".into(),
        version,
        path: path.to_string_lossy().into(),
        available: true,
    })
}

fn detect_llm() -> Option<HarnessInfo> {
    let path = which::which("llm").ok()?;
    let output = Command::new("llm").arg("--version").output().ok()?;
    let version = if output.status.success() {
        Some(String::from_utf8_lossy(&output.stdout).trim().to_string())
    } else {
        None
    };
    Some(HarnessInfo {
        harness_type: HarnessType::Llm,
        name: "LLM CLI".into(),
        version,
        path: path.to_string_lossy().into(),
        available: true,
    })
}

fn detect_openai() -> Option<HarnessInfo> {
    let path = which::which("openai").ok()?;
    let output = Command::new("openai").arg("--version").output().ok()?;
    let version = if output.status.success() {
        Some(String::from_utf8_lossy(&output.stdout).trim().to_string())
    } else {
        None
    };
    Some(HarnessInfo {
        harness_type: HarnessType::OpenAI,
        name: "OpenAI CLI".into(),
        version,
        path: path.to_string_lossy().into(),
        available: true,
    })
}

fn detect_llamafile() -> Option<HarnessInfo> {
    let path = which::which("llamafile").ok()?;
    Some(HarnessInfo {
        harness_type: HarnessType::Llamafile,
        name: "Llamafile".into(),
        version: None,
        path: path.to_string_lossy().into(),
        available: true,
    })
}
