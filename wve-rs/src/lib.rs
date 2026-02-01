pub mod cli;
pub mod embeddings;
pub mod comparison;
pub mod eval;
pub mod extraction;
pub mod harness;
pub mod models;
pub mod storage;
pub mod synthesis;
pub mod transcripts;
pub mod tui;
pub mod wizard;

pub use comparison::{diff_worldviews, Alignment, Blindspot, PointComparison, WorldviewDiff};
pub use models::{HarnessConfig, Worldview, WorldviewPoint};
pub use synthesis::{generate_movement, Movement, MovementSection};
