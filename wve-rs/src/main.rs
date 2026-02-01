mod cli;
mod comparison;
mod embeddings;
mod eval;
mod extraction;
mod harness;
mod models;
mod storage;
mod synthesis;
mod tui;
mod wizard;

use anyhow::Result;
use clap::{CommandFactory, Parser};
use clap_complete::generate;
use cli::{Cli, Commands, EvalAction};
use std::io;

fn main() -> Result<()> {
    let cli = Cli::parse();

    // Auto-run wizard on first launch
    if wizard::is_first_run() && cli.command.is_none() && !cli.json {
        return wizard::run_wizard();
    }

    match cli.command {
        Some(Commands::List) => cmd_list(cli.json),
        Some(Commands::Show { slug }) => cmd_show(&slug, cli.json),
        Some(Commands::Search { query }) => cmd_search(&query, cli.json),
        Some(Commands::Prepare { subject }) => cmd_prepare(&subject, cli.json),
        Some(Commands::Ingest { file }) => cmd_ingest(&file, cli.json),
        Some(Commands::Diff { slug1, slug2 }) => cmd_diff(&slug1, &slug2, cli.json),
        Some(Commands::Config { set }) => cmd_config(set.as_deref(), cli.json),
        Some(Commands::Harnesses) => cmd_harnesses(cli.json),
        Some(Commands::Completions { shell }) => {
            generate(shell, &mut Cli::command(), "wve", &mut io::stdout());
            Ok(())
        }
        Some(Commands::Eval { action }) => cmd_eval(action, cli.json),
        Some(Commands::Synthesize { slugs, format, output }) => {
            cmd_synthesize(&slugs, &format, output.as_deref(), cli.json)
        }
        None => {
            if cli.json {
                Cli::command().print_help()?;
            } else {
                tui::app::run()?;
            }
            Ok(())
        }
    }
}

fn cmd_list(json: bool) -> Result<()> {
    let slugs = storage::json_store::list_worldview_slugs()?;

    if json {
        let worldviews: Vec<_> = slugs
            .iter()
            .filter_map(|slug| storage::json_store::load_worldview(slug).ok())
            .collect();
        println!("{}", serde_json::to_string(&worldviews)?);
    } else {
        if slugs.is_empty() {
            println!("No worldviews stored yet");
        } else {
            println!("Stored worldviews:");
            for slug in &slugs {
                if let Ok(wv) = storage::json_store::load_worldview(slug) {
                    println!("  {} - {} ({})", wv.slug, wv.subject, wv.created_at.format("%Y-%m-%d"));
                } else {
                    println!("  {} (error loading)", slug);
                }
            }
        }
    }
    Ok(())
}

fn cmd_show(slug: &str, json: bool) -> Result<()> {
    match storage::json_store::load_worldview(slug) {
        Ok(wv) => {
            if json {
                println!("{}", serde_json::to_string(&wv)?);
            } else {
                println!("Worldview: {}", wv.slug);
                println!("  Subject: {}", wv.subject);
                println!("  Created: {}", wv.created_at.format("%Y-%m-%d %H:%M"));
                println!("  Points: {}", wv.points.len());
                for point in &wv.points {
                    println!("    • {} ({}%)", point.theme, (point.confidence * 100.0) as i32);
                }
            }
            Ok(())
        }
        Err(e) => {
            if json {
                println!("{{\"error\": \"{}\"}}", e);
            } else {
                eprintln!("Error: {}", e);
            }
            Ok(())
        }
    }
}

fn cmd_search(_query: &str, json: bool) -> Result<()> {
    if json {
        println!("[]");
    } else {
        println!("Search not yet implemented");
    }
    Ok(())
}

fn cmd_prepare(subject: &str, _json: bool) -> Result<()> {
    let transcripts: Vec<String> = vec![];
    let prompt = extraction::prompt::generate_extraction_prompt(subject, &transcripts);
    println!("{}", prompt);
    Ok(())
}

fn cmd_ingest(file: &str, json: bool) -> Result<()> {
    use std::io::Read;

    let content = if file == "-" {
        let mut buf = String::new();
        io::stdin().read_to_string(&mut buf)?;
        buf
    } else {
        std::fs::read_to_string(file)?
    };

    let worldview = extraction::ingest::parse_extraction(&content)?;
    storage::json_store::save_worldview(&worldview)?;

    if json {
        println!("{}", serde_json::to_string(&worldview)?);
    } else {
        println!("Ingested worldview: {} ({} points)", worldview.slug, worldview.points.len());
    }
    Ok(())
}

fn cmd_diff(slug1: &str, slug2: &str, json: bool) -> Result<()> {
    let wv_a = storage::json_store::load_worldview(slug1)?;
    let wv_b = storage::json_store::load_worldview(slug2)?;
    let diff = comparison::diff::diff_worldviews(&wv_a, &wv_b);

    if json {
        println!("{}", serde_json::to_string(&diff)?);
    } else {
        println!("Comparing {} vs {}", diff.subject_a, diff.subject_b);
        println!("Similarity: {:.0}%", diff.similarity_score * 100.0);
        println!();
        if !diff.agreements.is_empty() {
            println!("Agreements ({}):", diff.agreements.len());
            for a in &diff.agreements {
                println!("  • {}", a.theme);
            }
        }
        if !diff.tensions.is_empty() {
            println!("Tensions ({}):", diff.tensions.len());
            for t in &diff.tensions {
                println!("  • {}", t.theme);
            }
        }
        if !diff.unique_to_a.is_empty() {
            println!("Unique to {} ({}):", diff.subject_a, diff.unique_to_a.len());
            for p in &diff.unique_to_a {
                println!("  • {}", p.theme);
            }
        }
        if !diff.unique_to_b.is_empty() {
            println!("Unique to {} ({}):", diff.subject_b, diff.unique_to_b.len());
            for p in &diff.unique_to_b {
                println!("  • {}", p.theme);
            }
        }
    }
    Ok(())
}

fn cmd_config(_set: Option<&str>, json: bool) -> Result<()> {
    if json {
        println!("{{}}");
    } else {
        println!("Config not yet implemented");
    }
    Ok(())
}

fn cmd_harnesses(json: bool) -> Result<()> {
    let harnesses = harness::detect_harnesses();

    if json {
        println!("{}", serde_json::to_string(&harnesses)?);
    } else {
        if harnesses.is_empty() {
            println!("No harnesses detected");
        } else {
            println!("Detected harnesses:");
            for h in &harnesses {
                let ver = h.version.as_deref().unwrap_or("unknown");
                println!("  {} ({}) - {}", h.name, ver, h.path);
            }
        }
    }
    Ok(())
}

fn cmd_eval(action: EvalAction, json: bool) -> Result<()> {
    use eval::{run_eval, EvalCriteria};

    match action {
        EvalAction::Run => {
            let criteria = EvalCriteria::default_strict();
            let extracted: Vec<(String, models::Worldview)> = vec![];
            let report = run_eval(&extracted, &criteria);

            if json {
                println!("{}", serde_json::to_string(&report)?);
            } else {
                println!("Eval run: {}/{} passed", report.passed, report.total);
                for r in &report.results {
                    let status = if r.passed { "✓" } else { "✗" };
                    println!("  {} {} (coverage: {:.0}%)", status, r.fixture_name, r.theme_coverage * 100.0);
                }
            }
            Ok(())
        }
        EvalAction::Report => {
            let fixtures = eval::fixtures::load_fixtures()?;
            if json {
                println!("{}", serde_json::to_string(&fixtures)?);
            } else {
                println!("Fixtures: {}", fixtures.len());
                for f in &fixtures {
                    println!("  {} ({} required, {} forbidden)",
                        f.name,
                        f.required_themes.len(),
                        f.forbidden_themes.len()
                    );
                }
            }
            Ok(())
        }
    }
}

fn cmd_synthesize(slugs: &[String], format: &str, output: Option<&str>, _json: bool) -> Result<()> {
    use synthesis::{generate_movement, json::render_json, markdown::render_markdown};

    if slugs.is_empty() {
        anyhow::bail!("At least one worldview slug is required");
    }

    let worldviews: Vec<_> = slugs
        .iter()
        .map(|slug| storage::json_store::load_worldview(slug))
        .collect::<Result<Vec<_>, _>>()?;

    let movement = generate_movement(&worldviews, None);

    let output_content = match format {
        "json" => render_json(&movement)?,
        "both" => {
            let md = render_markdown(&movement);
            let json = render_json(&movement)?;
            format!("{}\n\n---\n\n```json\n{}\n```", md, json)
        }
        _ => render_markdown(&movement),
    };

    if let Some(path) = output {
        std::fs::write(path, &output_content)?;
        println!("Wrote synthesis to {}", path);
    } else {
        println!("{}", output_content);
    }

    Ok(())
}
