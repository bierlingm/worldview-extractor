use super::Movement;

pub fn render_markdown(movement: &Movement) -> String {
    let mut out = String::new();

    out.push_str(&format!("# {}\n\n", movement.title));
    out.push_str(&format!(
        "*Generated: {}*\n\n",
        movement.generated_at.format("%Y-%m-%d %H:%M UTC")
    ));
    out.push_str(&format!(
        "**Subjects:** {}\n\n",
        movement.subjects.join(", ")
    ));
    out.push_str(&format!("## Summary\n\n{}\n\n", movement.summary));

    for section in &movement.sections {
        out.push_str(&format!("## {}\n\n", section.name));

        for item in &section.content {
            out.push_str(&format!("### {}\n\n", item.theme));

            for voice in &item.voices {
                out.push_str(&format!(
                    "**{}** (confidence: {:.0}%): {}\n\n",
                    voice.subject,
                    voice.confidence * 100.0,
                    voice.stance
                ));
            }

            out.push_str(&format!("*{}*\n\n", item.synthesis));
            out.push_str("---\n\n");
        }
    }

    out
}
