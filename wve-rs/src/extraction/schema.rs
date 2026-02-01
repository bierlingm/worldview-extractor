pub const WORLDVIEW_SCHEMA: &str = r#"{
  "type": "object",
  "properties": {
    "subject": { "type": "string" },
    "points": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "theme": { "type": "string" },
          "stance": { "type": "string" },
          "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
          "evidence": { "type": "array", "items": { "type": "string" } },
          "sources": { "type": "array", "items": { "type": "string" } }
        },
        "required": ["theme", "stance", "confidence", "evidence"]
      }
    }
  },
  "required": ["subject", "points"]
}"#;
