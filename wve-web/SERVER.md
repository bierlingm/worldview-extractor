# Rust HTTP Server Stub

This document describes how to integrate the web UI with a Rust backend server.

## Building the Web UI for Production

First, build the React app:

```bash
npm run build
```

This generates optimized static files in the `dist/` directory.

## Simple Rust Server Example

Here's a minimal Axum server that serves the web UI and provides API endpoints:

```rust
// main.rs
use axum::{
    extract::Path,
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tower_http::services::ServeDir;

#[derive(Debug, Serialize, Deserialize)]
pub struct Worldview {
    pub subject: String,
    pub points: Vec<Belief>,
    pub method: Option<String>,
    pub depth: Option<String>,
    pub generated_at: String,
    pub source_videos: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Belief {
    pub point: String,
    pub elaboration: Option<String>,
    pub confidence: f64,
    pub evidence: Vec<String>,
    pub sources: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct WorldviewMetadata {
    pub slug: String,
    pub subject: String,
    pub generated_at: String,
    pub belief_count: usize,
}

#[tokio::main]
async fn main() {
    // Serve static files from dist/ directory
    let static_files = ServeDir::new("wve-web/dist");

    let router = Router::new()
        // API routes
        .route("/api/worldviews", get(list_worldviews))
        .route("/api/worldviews/:slug", get(get_worldview))
        .route("/api/worldviews/:slug/graph", get(get_graph))
        .route("/api/compare", get(compare_worldviews))
        // Fallback to static files (including index.html)
        .fallback_service(static_files);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:3030")
        .await
        .expect("Failed to bind port 3030");

    println!("Server running on http://127.0.0.1:3030");

    axum::serve(listener, router)
        .await
        .expect("Server failed");
}

async fn list_worldviews() -> Json<Vec<WorldviewMetadata>> {
    // Load worldviews from data directory
    // This is a placeholder - implement actual loading logic
    Json(vec![])
}

async fn get_worldview(Path(slug): Path<String>) -> Result<Json<Worldview>, StatusCode> {
    // Load specific worldview from data directory
    Err(StatusCode::NOT_FOUND)
}

async fn get_graph(Path(slug): Path<String>) -> Result<Json<serde_json::Value>, StatusCode> {
    // Generate or load graph data for worldview
    Err(StatusCode::NOT_FOUND)
}

async fn compare_worldviews(
    axum::extract::Query(params): axum::extract::Query<std::collections::HashMap<String, String>>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    // Compare two worldviews by slug
    Err(StatusCode::NOT_FOUND)
}
```

## Cargo.toml Dependencies

```toml
[dependencies]
axum = "0.7"
tokio = { version = "1", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tower-http = { version = "0.5", features = ["services"] }

[dev-dependencies]
# Add test dependencies as needed
```

## Key Implementation Steps

1. **Load Worldviews**: Implement file I/O to load JSON worldview files from `../data/` directory
2. **Graph Generation**: Use the graph generation logic from the frontend `api.ts` or create equivalent Rust logic
3. **Comparison Logic**: Implement worldview comparison that identifies agreements, tensions, and unique beliefs
4. **CORS Headers**: Add CORS middleware if frontend and backend run on different ports during development

## Example Implementation with File Loading

```rust
use std::fs;
use serde_json::json;

async fn list_worldviews() -> Json<Vec<WorldviewMetadata>> {
    let mut worldviews = Vec::new();

    if let Ok(entries) = fs::read_dir("../data") {
        for entry in entries {
            if let Ok(entry) = entry {
                let path = entry.path();
                if path.join("worldview.json").exists() {
                    if let Ok(content) = fs::read_to_string(path.join("worldview.json")) {
                        if let Ok(wv) = serde_json::from_str::<Worldview>(&content) {
                            let slug = path
                                .file_name()
                                .and_then(|n| n.to_str())
                                .unwrap_or("unknown")
                                .to_string();

                            worldviews.push(WorldviewMetadata {
                                slug,
                                subject: wv.subject,
                                generated_at: wv.generated_at,
                                belief_count: wv.points.len(),
                            });
                        }
                    }
                }
            }
        }
    }

    Json(worldviews)
}
```

## Running in Development

Terminal 1 (Frontend):
```bash
cd wve-web
npm run dev
# Runs on http://localhost:5173
```

Terminal 2 (Backend):
```bash
# In your Rust project
cargo run
# Runs on http://localhost:3030 (optional, frontend mocks data without it)
```

The frontend will automatically fall back to mock data if the backend is unavailable.

## Deployment

For production:

1. Build the React app: `npm run build`
2. Embed the `dist/` directory in your Rust binary or serve separately
3. Configure environment variables for API endpoints
4. Deploy with your preferred Rust hosting solution (Fly.io, Heroku, AWS EC2, etc.)

## CORS Configuration for Development

If developing with separate frontend/backend ports, add CORS middleware:

```rust
use tower_http::cors::CorsLayer;
use http::Method;

let cors = CorsLayer::permissive();

let router = Router::new()
    .route(...)
    .layer(cors);
```

Or more restrictively:

```rust
let cors = CorsLayer::very_permissive()
    .allow_methods([Method::GET, Method::POST])
    .allow_origin("http://localhost:5173".parse().unwrap());
```
