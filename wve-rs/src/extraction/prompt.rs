use super::schema::WORLDVIEW_SCHEMA;

pub fn generate_extraction_prompt(subject: &str, transcripts: &[String]) -> String {
    format!(
        r#"
# Worldview Extraction Task

Extract the worldview of **{subject}** from the following transcripts.

## Instructions
1. Identify 10-20 distinct worldview points (beliefs, values, positions)
2. For each point, provide:
   - theme: A short label (2-5 words)
   - stance: Their position on this theme (1-2 sentences)
   - confidence: How clearly expressed (0.0-1.0)
   - evidence: Direct quotes that support this (include timestamps if available)
   - sources: Which transcript(s) this came from

3. Focus on distinctive positions, not generic statements
4. Prefer contrarian or nuanced takes over obvious points
5. Include tensions or contradictions if present

## Transcripts

{transcripts}

## Output Format
Respond with valid JSON matching this schema:
{schema}
"#,
        subject = subject,
        transcripts = transcripts.join("\n\n---\n\n"),
        schema = WORLDVIEW_SCHEMA
    )
}
