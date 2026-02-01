use anyhow::{anyhow, Context, Result};
use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VideoInfo {
    pub id: String,
    pub title: String,
    pub channel: String,
    pub duration_seconds: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transcript {
    pub video_id: String,
    pub text: String,
    pub segments: Vec<TranscriptSegment>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranscriptSegment {
    pub start: f64,
    pub duration: f64,
    pub text: String,
}

#[derive(Debug, Deserialize)]
struct YtdlpVideoInfo {
    id: String,
    title: Option<String>,
    channel: Option<String>,
    uploader: Option<String>,
    duration: Option<f64>,
}

#[derive(Debug, Deserialize)]
struct YtdlpSubtitleEntry {
    start: Option<f64>,
    dur: Option<f64>,
    text: Option<String>,
}

pub fn check_ytdlp() -> bool {
    Command::new("yt-dlp").arg("--version").output().is_ok()
}

pub fn ytdlp_version() -> Option<String> {
    Command::new("yt-dlp")
        .arg("--version")
        .output()
        .ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .map(|s| s.trim().to_string())
}

pub fn search_videos(query: &str, max_results: usize) -> Result<Vec<VideoInfo>> {
    let search_query = format!("ytsearch{}:{}", max_results, query);
    let output = Command::new("yt-dlp")
        .args(["--dump-json", "--flat-playlist", &search_query])
        .output()
        .context("Failed to execute yt-dlp")?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(anyhow!("yt-dlp search failed: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let mut videos = Vec::new();

    for line in stdout.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let info: YtdlpVideoInfo = serde_json::from_str(line)
            .with_context(|| format!("Failed to parse yt-dlp JSON: {}", line))?;

        videos.push(VideoInfo {
            id: info.id,
            title: info.title.unwrap_or_default(),
            channel: info.channel.or(info.uploader).unwrap_or_default(),
            duration_seconds: info.duration.unwrap_or(0.0) as u64,
        });
    }

    Ok(videos)
}

pub fn download_transcript(video_id: &str) -> Result<Transcript> {
    let url = format!("https://www.youtube.com/watch?v={}", video_id);
    let temp_dir = std::env::temp_dir();
    let output_template = temp_dir.join("%(id)s");

    let output = Command::new("yt-dlp")
        .args([
            "--write-auto-sub",
            "--sub-lang", "en",
            "--sub-format", "json3",
            "--skip-download",
            "-o", output_template.to_str().unwrap(),
            &url,
        ])
        .output()
        .context("Failed to execute yt-dlp")?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(anyhow!("yt-dlp transcript download failed: {}", stderr));
    }

    let json3_path = temp_dir.join(format!("{}.en.json3", video_id));
    let vtt_path = temp_dir.join(format!("{}.en.vtt", video_id));

    let transcript = if json3_path.exists() {
        parse_json3_transcript(video_id, &json3_path)?
    } else if vtt_path.exists() {
        parse_vtt_transcript(video_id, &vtt_path)?
    } else {
        return Err(anyhow!("No transcript file found for video {}", video_id));
    };

    let _ = std::fs::remove_file(&json3_path);
    let _ = std::fs::remove_file(&vtt_path);

    Ok(transcript)
}

fn parse_json3_transcript(video_id: &str, path: &std::path::Path) -> Result<Transcript> {
    #[derive(Deserialize)]
    struct Json3Root {
        events: Option<Vec<Json3Event>>,
    }

    #[derive(Deserialize)]
    struct Json3Event {
        #[serde(rename = "tStartMs")]
        t_start_ms: Option<i64>,
        #[serde(rename = "dDurationMs")]
        d_duration_ms: Option<i64>,
        segs: Option<Vec<Json3Seg>>,
    }

    #[derive(Deserialize)]
    struct Json3Seg {
        utf8: Option<String>,
    }

    let content = std::fs::read_to_string(path).context("Failed to read json3 file")?;
    let root: Json3Root = serde_json::from_str(&content).context("Failed to parse json3")?;

    let mut segments = Vec::new();
    let mut full_text = String::new();

    if let Some(events) = root.events {
        for event in events {
            if let Some(segs) = event.segs {
                let text: String = segs.iter().filter_map(|s| s.utf8.as_deref()).collect();
                if text.trim().is_empty() {
                    continue;
                }

                let start = event.t_start_ms.unwrap_or(0) as f64 / 1000.0;
                let duration = event.d_duration_ms.unwrap_or(0) as f64 / 1000.0;

                if !full_text.is_empty() {
                    full_text.push(' ');
                }
                full_text.push_str(text.trim());

                segments.push(TranscriptSegment {
                    start,
                    duration,
                    text: text.trim().to_string(),
                });
            }
        }
    }

    Ok(Transcript {
        video_id: video_id.to_string(),
        text: full_text,
        segments,
    })
}

fn parse_vtt_transcript(video_id: &str, path: &std::path::Path) -> Result<Transcript> {
    let content = std::fs::read_to_string(path).context("Failed to read vtt file")?;
    let mut segments = Vec::new();
    let mut full_text = String::new();
    let mut lines = content.lines().peekable();

    while let Some(line) = lines.next() {
        if line.contains("-->") {
            let times: Vec<&str> = line.split("-->").collect();
            if times.len() >= 2 {
                let start = parse_vtt_time(times[0].trim());
                let end = parse_vtt_time(times[1].split_whitespace().next().unwrap_or(""));
                let duration = end - start;

                let mut text = String::new();
                while let Some(next) = lines.peek() {
                    if next.is_empty() || next.contains("-->") {
                        break;
                    }
                    let t = lines.next().unwrap();
                    let clean = strip_vtt_tags(t);
                    if !clean.is_empty() {
                        if !text.is_empty() {
                            text.push(' ');
                        }
                        text.push_str(&clean);
                    }
                }

                if !text.is_empty() {
                    if !full_text.is_empty() {
                        full_text.push(' ');
                    }
                    full_text.push_str(&text);
                    segments.push(TranscriptSegment { start, duration, text });
                }
            }
        }
    }

    Ok(Transcript {
        video_id: video_id.to_string(),
        text: full_text,
        segments,
    })
}

fn parse_vtt_time(s: &str) -> f64 {
    let parts: Vec<&str> = s.split(':').collect();
    match parts.len() {
        3 => {
            let h: f64 = parts[0].parse().unwrap_or(0.0);
            let m: f64 = parts[1].parse().unwrap_or(0.0);
            let s: f64 = parts[2].replace(',', ".").parse().unwrap_or(0.0);
            h * 3600.0 + m * 60.0 + s
        }
        2 => {
            let m: f64 = parts[0].parse().unwrap_or(0.0);
            let s: f64 = parts[1].replace(',', ".").parse().unwrap_or(0.0);
            m * 60.0 + s
        }
        _ => 0.0,
    }
}

fn strip_vtt_tags(s: &str) -> String {
    let mut result = String::new();
    let mut in_tag = false;
    for c in s.chars() {
        if c == '<' {
            in_tag = true;
        } else if c == '>' {
            in_tag = false;
        } else if !in_tag {
            result.push(c);
        }
    }
    result.trim().to_string()
}

pub fn update_ytdlp() -> Result<()> {
    let output = Command::new("yt-dlp")
        .arg("-U")
        .output()
        .context("Failed to execute yt-dlp update")?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(anyhow!("yt-dlp update failed: {}", stderr));
    }

    Ok(())
}
