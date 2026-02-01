use clap::{Parser, Subcommand};
use clap_complete::Shell;

#[derive(Parser)]
#[command(name = "wve", version, about = "Worldview extraction and synthesis")]
pub struct Cli {
    #[arg(long, global = true)]
    pub json: bool,

    #[command(subcommand)]
    pub command: Option<Commands>,
}

#[derive(Subcommand)]
pub enum Commands {
    /// List stored worldviews
    List,
    /// Show a worldview
    Show { slug: String },
    /// Search worldviews
    Search { query: String },
    /// Prepare extraction prompt (outputs to stdout)
    Prepare { subject: String },
    /// Ingest extraction result
    Ingest {
        #[arg(default_value = "-")]
        file: String,
    },
    /// Compare two worldviews
    Diff { slug1: String, slug2: String },
    /// Show/set configuration
    Config {
        #[arg(long)]
        set: Option<String>,
    },
    /// List detected harnesses
    Harnesses,
    /// Generate shell completions
    Completions { shell: Shell },
    /// Eval framework commands
    Eval {
        #[command(subcommand)]
        action: EvalAction,
    },
    /// Synthesize multiple worldviews into a movement
    Synthesize {
        /// Slugs of worldviews to synthesize
        slugs: Vec<String>,
        /// Output format (markdown, json, both)
        #[arg(long, default_value = "markdown")]
        format: String,
        /// Output file (stdout if not specified)
        #[arg(short, long)]
        output: Option<String>,
    },
}

#[derive(Subcommand)]
pub enum EvalAction {
    /// Run eval against fixtures
    Run,
    /// Show eval report
    Report,
}
