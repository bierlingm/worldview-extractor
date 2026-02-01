"""Quote extraction from transcripts (v0.2)."""

import re
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class Quote(BaseModel):
    """A notable quote extracted from a transcript."""

    text: str
    source_id: str
    source_title: str
    timestamp_approx: str | None = None
    context: str | None = None
    themes: list[str] = Field(default_factory=list)
    score: float = 0.0
    is_contrarian: bool = False


class QuoteCollection(BaseModel):
    """Collection of quotes from a corpus."""

    subject: str | None = None
    quotes: list[Quote] = Field(default_factory=list)
    source_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


# Opinion/belief indicators
OPINION_STARTERS = [
    "i believe", "i think", "the truth is", "most people",
    "the problem is", "what matters is", "the key is",
    "contrary to", "unlike most", "the reality is",
    "in my view", "in my experience", "i've found that",
    "what i've learned", "the important thing",
]

# Contrarian indicators
CONTRARIAN_PHRASES = [
    "but actually", "however", "on the contrary",
    "most people think", "conventional wisdom",
    "the opposite is true", "counterintuitively",
    "what's often missed", "contrary to popular",
    "the counterintuitive", "surprisingly",
]

# Specificity indicators
SPECIFICITY_PATTERNS = [
    r"\d+%",  # percentages
    r"\d+ (years|months|days|percent|people|times)",  # quantities
    r"\$\d+",  # money
    r"(first|second|third|specifically|exactly)",
]


def split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    # Basic sentence splitting - handles common cases
    text = re.sub(r"\s+", " ", text)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def score_sentence(sentence: str) -> tuple[float, list[str], bool]:
    """
    Score a sentence for quote-worthiness.
    
    Returns (score, reasons, is_contrarian).
    """
    score = 0.0
    reasons = []
    is_contrarian = False
    sentence_lower = sentence.lower()

    # Opinion starters
    for starter in OPINION_STARTERS:
        if sentence_lower.startswith(starter):
            score += 0.3
            reasons.append(f"opinion_starter:{starter}")
            break

    # Contrarian phrases
    for phrase in CONTRARIAN_PHRASES:
        if phrase in sentence_lower:
            score += 0.25
            reasons.append("contrarian")
            is_contrarian = True
            break

    # Specificity (numbers, percentages, etc.)
    for pattern in SPECIFICITY_PATTERNS:
        if re.search(pattern, sentence_lower):
            score += 0.15
            reasons.append("specific")
            break

    # Quotable structure (shorter, punchier)
    words = sentence.split()
    if 10 <= len(words) <= 30:
        score += 0.1
        reasons.append("good_length")

    # Named entities (capitalized words that aren't sentence starts)
    caps = re.findall(r"(?<!\. )\b[A-Z][a-z]+\b", sentence)
    if len(caps) >= 2:
        score += 0.1
        reasons.append("named_entities")

    return score, reasons, is_contrarian


def extract_quotes(
    text: str,
    source_id: str,
    source_title: str = "",
    min_words: int = 8,
    max_words: int = 60,
    min_score: float = 0.3,
) -> list[Quote]:
    """Extract notable quotes from a transcript."""
    sentences = split_sentences(text)
    quotes = []

    for i, sentence in enumerate(sentences):
        words = sentence.split()
        if not (min_words <= len(words) <= max_words):
            continue

        score, reasons, is_contrarian = score_sentence(sentence)

        if score >= min_score:
            # Estimate timestamp (rough approximation)
            progress = i / max(len(sentences), 1)
            timestamp = f"~{int(progress * 100)}%"

            # Get context (surrounding sentences)
            context_parts = []
            if i > 0:
                context_parts.append(sentences[i - 1][:100])
            context_parts.append(f">>> {sentence}")
            if i < len(sentences) - 1:
                context_parts.append(sentences[i + 1][:100])
            context = " ... ".join(context_parts)

            quotes.append(Quote(
                text=sentence.strip(),
                source_id=source_id,
                source_title=source_title,
                timestamp_approx=timestamp,
                context=context,
                score=score,
                is_contrarian=is_contrarian,
            ))

    # Sort by score descending
    quotes.sort(key=lambda q: q.score, reverse=True)
    return quotes


def extract_quotes_from_dir(
    transcript_dir: Path,
    max_quotes: int = 50,
    min_score: float = 0.3,
) -> QuoteCollection:
    """Extract quotes from all transcripts in a directory."""
    all_quotes = []
    source_count = 0

    # Load transcripts
    for txt_file in transcript_dir.glob("*.txt"):
        if txt_file.name == "manifest.json":
            continue

        source_id = txt_file.stem
        text = txt_file.read_text()
        source_count += 1

        quotes = extract_quotes(
            text,
            source_id=source_id,
            source_title=source_id,
            min_score=min_score,
        )
        all_quotes.extend(quotes)

    # Sort all by score and limit
    all_quotes.sort(key=lambda q: q.score, reverse=True)
    all_quotes = all_quotes[:max_quotes]

    return QuoteCollection(
        quotes=all_quotes,
        source_count=source_count,
    )
