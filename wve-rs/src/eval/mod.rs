pub mod criteria;
pub mod fixtures;
pub mod runner;

pub use criteria::EvalCriteria;
pub use runner::{run_eval, EvalReport, EvalResult};
