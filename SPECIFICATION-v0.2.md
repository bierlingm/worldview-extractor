# Worldview Extractor v0.2 — Specification

**Version:** 0.2.0  
**Status:** Draft  
**Created:** 2026-01-02

---

## 1. Problem Analysis: Why v0.1 Fails

### 1.1 Identity Resolution Failure

The core problem: **common names match wrong people**.

| Guest | Search Result | Actual Match |
|-------|---------------|--------------|
| Augustine Hughes | Saint Augustine sermons | 0% correct |
| Kristian Bell | Kristen Bell (actress) | 0% correct |
| Brandon Hayes | Mixed: some correct, some wrong | ~40% correct |
| Josh Rieder | Dylan Rieder (skater) mixed in | ~50% correct |
| E.M. Burlingame | Correct (unique name) | ~100% correct |

**Root cause:** YouTube search optimizes for popularity, not precision. "Kristian Bell" returns Kristen Bell because she has 1000x more content.

### 1.2 Keyword Extraction Loses Signal

The pipeline: transcripts → keywords → clusters → synthesis

Each step loses information:
- **Keywords:** "entrepreneurship", "learning", "community" — generic
- **Clusters:** Groups generic terms together — still generic
- **Synthesis:** LLM makes up plausible-sounding points from generic input

**The actual transcripts contain gold** — specific quotes, unique framings, contrarian takes — but keyword extraction discards all of it.

### 1.3 No Human-in-the-Loop

v0.1 is fully automated. But:
- User knows if videos are correct (machine doesn't)
- User knows what's interesting about this person (machine doesn't)
- User can provide seed URLs, channel links, disambiguating context

---

## 2. Design Principles for v0.2

### 2.1 Identity-First, Not Search-First

**Old flow:**
```
search "name" → download everything → hope it's right
```

**New flow:**
```
establish identity → curate sources → then extract
```

Identity establishment:
1. **Channel anchor:** Person's own YouTube channel (most reliable)
2. **Curated URLs:** User provides known-good video URLs
3. **Disambiguation search:** Interactive refinement with user confirmation

### 2.2 Transcripts Are the Product

Stop treating transcripts as intermediate artifacts to be compressed.

**New philosophy:**
- `wve dump` output IS the primary deliverable
- Quote extraction > keyword extraction
- Full transcript context available to synthesis

### 2.3 Interactive by Default

Automation is opt-in, not opt-out.

**New flow:**
```
wve discover "name"           # Show candidates, don't download
wve confirm candidates.json   # User marks correct/incorrect
wve fetch confirmed.json      # Download only confirmed
```

For automation (CI, agents):
```
wve discover "name" --auto-confirm --channel UC123  # Trust channel match
```

---

## 3. New Commands

### 3.1 Identity Commands

#### `wve identity create <name>`

Create a new identity profile for a person.

```bash
wve identity create "Skinner Layne" \
  --channel "https://youtube.com/@exikiex" \
  --website "https://skinnerlayne.com" \
  --aliases "Skinner" "S. Layne"
```

Creates `~/.wve/identities/skinner-layne.json`:
```json
{
  "slug": "skinner-layne",
  "display_name": "Skinner Layne",
  "aliases": ["Skinner", "S. Layne"],
  "channels": [
    {"platform": "youtube", "id": "UC...", "url": "https://youtube.com/@exikiex"}
  ],
  "websites": ["https://skinnerlayne.com"],
  "confirmed_videos": [],
  "rejected_videos": [],
  "created_at": "2026-01-02T...",
  "updated_at": "2026-01-02T..."
}
```

#### `wve identity list`

List all known identities.

```
skinner-layne    Skinner Layne       1 channel, 22 videos confirmed
em-burlingame    E.M. Burlingame     0 channels, 15 videos confirmed
```

#### `wve identity show <slug>`

Show identity details and video stats.

#### `wve identity add-channel <slug> <url>`

Add a YouTube channel to an identity.

#### `wve identity add-video <slug> <url>`

Manually add a confirmed video URL.

---

### 3.2 Discovery Commands

#### `wve discover <query> [options]`

Search for videos WITHOUT downloading. Returns candidates for confirmation.

```bash
wve discover "Skinner Layne" --max-results 20
```

Output (interactive):
```
Found 20 candidates for "Skinner Layne"

LIKELY MATCHES (channel/title match):
  [1] ✓ Arctic15 114 Skinner Layne, Exosphere - Startups Are Dead
      Channel: Arctic15  |  Duration: 18m  |  2015-06-12
      
  [2] ✓ Advanced Learning in the 21st Century - EXOSPHERE Founder
      Channel: TEDx Talks  |  Duration: 15m  |  2016-03-20

UNCERTAIN (name mentioned but not primary):
  [3] ? Invest Festival 2015 - Entrepreneur Panel
      Channel: InvestChile  |  Duration: 45m  |  2015-04-15
      
FALSE POSITIVES (likely wrong person):
  [4] ✗ Lynyrd Skynyrd - Free Bird (Skinner cover)
      Channel: MusicCovers  |  Duration: 9m  |  2020-01-01

Actions:
  [c]onfirm selected    [r]eject selected    [s]ave candidates
  [a]dd numbers         [f]etch confirmed    [q]uit
  
> 
```

**Classification heuristics:**
- ✓ LIKELY: Title contains full name OR video is from known channel
- ? UNCERTAIN: Partial name match, interview/panel format
- ✗ FALSE POSITIVE: Name is substring of other words, music/entertainment channel

```bash
# Non-interactive mode (for scripting)
wve discover "Skinner Layne" --json > candidates.json

# With identity context (uses channel info)
wve discover --identity skinner-layne --max-results 50

# With channel filter
wve discover "Skinner Layne" --channel UC... --json
```

Options:
- `--max-results N`: How many to search (default: 20)
- `--identity SLUG`: Use existing identity for disambiguation
- `--channel URL`: Filter to specific channel
- `--strict`: Only return videos where full query appears in title
- `--json`: Output as JSON for scripting
- `--auto-classify`: Add heuristic classification to output

#### `wve confirm <candidates.json> [options]`

Interactive confirmation of video candidates.

```bash
wve confirm candidates.json
```

Opens TUI or interactive prompt to mark videos as confirmed/rejected.

```bash
# Batch confirm by IDs
wve confirm candidates.json --accept 1,2,3,5 --reject 4,6

# Confirm all likely matches
wve confirm candidates.json --accept-likely

# Save to identity
wve confirm candidates.json --identity skinner-layne
```

Output: `confirmed.json` with only accepted videos.

#### `wve fetch <input> [options]`

Download transcripts for confirmed videos only.

```bash
wve fetch confirmed.json -o transcripts/
wve fetch --identity skinner-layne -o transcripts/
```

Only processes videos that have been explicitly confirmed.

---

### 3.3 Source Commands

#### `wve from-channel <channel-url> [options]`

Scrape all videos from a YouTube channel.

```bash
wve from-channel "https://youtube.com/@exikiex" \
  --max-videos 50 \
  --min-duration 5 \
  -o skinner-channel/
```

This is the **most reliable** way to get content from a person with their own channel.

Options:
- `--max-videos N`: Limit number of videos
- `--min-duration M`: Minimum duration in minutes
- `--max-duration M`: Maximum duration
- `--after DATE`: Only videos after date
- `--before DATE`: Only videos before date
- `--playlist URL`: Specific playlist instead of full channel

#### `wve from-urls <file> [options]`

Process a list of manually curated video URLs.

```bash
# urls.txt contains one URL per line
wve from-urls urls.txt -o transcripts/

# Or inline
wve from-urls --url "https://youtube.com/watch?v=..." \
              --url "https://youtube.com/watch?v=..." \
              -o transcripts/
```

This is the **most accurate** method — user guarantees correctness.

#### `wve from-rss <feed-url> [options]`

Ingest podcast episodes from RSS feed.

```bash
wve from-rss "https://feeds.example.com/podcast.xml" \
  --max-episodes 20 \
  --transcribe \
  -o podcast-transcripts/
```

Options:
- `--max-episodes N`: Limit episodes
- `--after DATE`: Only episodes after date
- `--transcribe`: Use Whisper to transcribe audio (slow)
- `--transcript-service SERVICE`: Use external service (assembly.ai, etc.)

#### `wve from-text <directory> [options]`

Import existing text files (blog posts, articles, book chapters).

```bash
wve from-text ./blog-posts/ -o corpus/
wve from-text ./book-chapters/ --format markdown -o corpus/
```

Options:
- `--format`: plain, markdown, html
- `--extract-metadata`: Try to extract title, date from content

---

### 3.4 Refinement Commands

#### `wve refine <identity> [options]`

Interactive search refinement to find more content.

```bash
wve refine skinner-layne
```

Flow:
```
Current corpus: 22 videos, ~8 hours of content

Suggested searches to find more:
  1. "Skinner Layne interview"     (estimated: 5-10 new)
  2. "Exosphere founder"           (estimated: 3-5 new)
  3. "Skinner entrepreneurship"    (estimated: 2-4 new)

[s]earch suggestion  [c]ustom search  [d]one

> s1

Searching "Skinner Layne interview"...
Found 8 new candidates (not in corpus):

  [1] ? The Tim Ferriss Show - Skinner Layne on Building Exosphere
      Channel: Tim Ferriss  |  Duration: 1h 20m  |  2017-08-15
      
  [2] ✓ Nomad Capitalist - Interview with Skinner Layne
      Channel: Nomad Capitalist  |  Duration: 45m  |  2018-03-22

[a]dd to confirmed  [r]eject  [b]ack

>
```

The system learns from confirmations:
- Channels that produce confirmed videos become "trusted"
- Title patterns that produce false positives become "suspicious"
- These heuristics improve `--auto-classify` accuracy

#### `wve suggest <identity>`

Suggest related people/content based on corpus.

```bash
wve suggest skinner-layne
```

Output:
```
Based on Skinner Layne's corpus, you might also research:

People frequently mentioned:
  - Tyler Cowen (12 mentions across 8 videos)
  - Peter Thiel (8 mentions across 6 videos)
  - Nassim Taleb (6 mentions across 4 videos)

Related channels:
  - EconTalk (Skinner appeared 2x)
  - Nomad Capitalist (interview host)

Topics for deeper exploration:
  - "antifragile organizations" (mentioned 15x)
  - "educational arbitrage" (mentioned 9x)
```

---

### 3.5 Enhanced Analysis Commands

#### `wve quotes <input> [options]`

Extract notable quotes from transcripts.

```bash
wve quotes transcripts/ --identity skinner-layne
```

Output:
```json
{
  "quotes": [
    {
      "text": "Startups are dead. The interesting thing now is...",
      "source": "arctic15-2015.txt",
      "timestamp_approx": "5:23",
      "context": "Discussing the evolution of entrepreneurship",
      "themes": ["entrepreneurship", "startups", "innovation"]
    }
  ]
}
```

Options:
- `--min-length N`: Minimum quote length in words
- `--max-quotes N`: Limit number of quotes
- `--themes THEME,...`: Filter to quotes matching themes
- `--controversial`: Prioritize contrarian/unusual statements

Quote extraction heuristics:
- Statements with strong sentiment (positive or negative)
- Statements with named entities or specific claims
- Statements following "I believe", "The truth is", "Most people think X but"
- Statements that are repeated across multiple videos

#### `wve contrast <input> [options]`

Find contrarian or distinctive beliefs.

```bash
wve contrast transcripts/ --subject "Skinner Layne"
```

Prompts the LLM specifically for:
- "What does {subject} believe that most people don't?"
- "Where does {subject} disagree with mainstream views?"
- "What's surprising or counterintuitive about their worldview?"

Output includes quotes that support each contrarian point.

#### `wve themes <input> [options]`

Extract themes with supporting quotes (not just keywords).

```bash
wve themes transcripts/ -o themes.json
```

Output:
```json
{
  "themes": [
    {
      "name": "Anti-credentialism",
      "description": "Belief that formal credentials are overvalued...",
      "frequency": 23,
      "supporting_quotes": [
        {"text": "...", "source": "..."},
        {"text": "...", "source": "..."}
      ],
      "related_themes": ["education", "apprenticeship"]
    }
  ]
}
```

---

### 3.6 Output Commands

#### `wve dump` (enhanced)

Already implemented in v0.1. Enhancements:

```bash
# With quote highlighting
wve dump transcripts/ --highlight-quotes quotes.json

# With theme annotations
wve dump transcripts/ --annotate-themes themes.json

# For specific LLM context window
wve dump transcripts/ --max-tokens 100000 --prioritize recent
```

#### `wve report <identity> [options]`

Generate comprehensive report.

```bash
wve report skinner-layne -o report.md
```

Output: Markdown report with:
- Subject overview
- Corpus statistics (N videos, total hours, date range)
- Top themes with quotes
- Distinctive/contrarian beliefs
- Key quotes organized by theme
- Source list with links

#### `wve export <identity> --format <format>`

Export to various formats.

```bash
wve export skinner-layne --format notion
wve export skinner-layne --format obsidian
wve export skinner-layne --format json
```

---

## 4. Interactive Workflows

### 4.1 New Person Workflow (Interactive)

```bash
# Step 1: Create identity
wve identity create "Josh Rieder"

# Step 2: Discover candidates
wve discover "Josh Rieder" --max-results 30

# Interactive classification appears:
# - Mark correct videos
# - Reject wrong ones
# - System learns patterns

# Step 3: Refine search
wve refine josh-rieder
# Suggests additional searches based on confirmed videos
# "Josh Rieder podcast", "Showing Up Josh", etc.

# Step 4: Fetch transcripts
wve fetch --identity josh-rieder -o transcripts/

# Step 5: Extract and analyze
wve themes transcripts/ -o themes.json
wve quotes transcripts/ -o quotes.json
wve contrast transcripts/ --subject "Josh Rieder" -o contrast.json

# Step 6: Generate report
wve report josh-rieder -o report.md
```

### 4.2 New Person Workflow (Automated)

For use in scripts or by AI agents:

```bash
# If channel is known (most reliable)
wve from-channel "https://youtube.com/@joshrieder" \
  --max-videos 20 \
  -o transcripts/

# If URLs are curated
wve from-urls curated-urls.txt -o transcripts/

# If must search (least reliable)
wve discover "Josh Rieder" \
  --auto-classify \
  --accept-likely \
  --json | \
wve fetch --stdin -o transcripts/

# Then analyze
wve synthesize transcripts/ --depth deep --json
```

### 4.3 Podcast Guest Research Workflow

Integration with capablefew pipeline:

```bash
#!/bin/bash
# research-worldview-v2

GUEST_SLUG="$1"
EPISODE_DIR="episodes/$GUEST_SLUG"
WVE_DIR="$EPISODE_DIR/wve"

# Get guest info from metadata
FULL_NAME=$(jq -r '.guest.name' "$EPISODE_DIR/metadata.json")
CHANNEL=$(jq -r '.guest.links.youtube // empty' "$EPISODE_DIR/metadata.json")

# Create or load identity
wve identity create "$FULL_NAME" --slug "$GUEST_SLUG" 2>/dev/null || true

if [[ -n "$CHANNEL" ]]; then
  # Channel known - most reliable
  wve from-channel "$CHANNEL" --max-videos 30 -o "$WVE_DIR/transcripts"
else
  # Interactive discovery
  wve discover "$FULL_NAME" --identity "$GUEST_SLUG"
  wve fetch --identity "$GUEST_SLUG" -o "$WVE_DIR/transcripts"
fi

# Analysis
wve themes "$WVE_DIR/transcripts" -o "$WVE_DIR/themes.json"
wve quotes "$WVE_DIR/transcripts" --max-quotes 50 -o "$WVE_DIR/quotes.json"
wve contrast "$WVE_DIR/transcripts" --subject "$FULL_NAME" -o "$WVE_DIR/contrast.json"

# Generate report
wve report "$GUEST_SLUG" -o "$WVE_DIR/worldview-report.md"

# Generate interview questions based on findings
wve questions "$GUEST_SLUG" -o "$EPISODE_DIR/suggested-questions.md"
```

---

## 5. Data Models (New/Updated)

### 5.1 Identity Model

```python
class Channel(BaseModel):
    platform: Literal["youtube", "vimeo", "rumble"]
    id: str
    url: str
    name: str | None = None
    verified: bool = False

class Identity(BaseModel):
    slug: str
    display_name: str
    aliases: list[str] = []
    channels: list[Channel] = []
    websites: list[str] = []
    confirmed_videos: list[str] = []  # video IDs
    rejected_videos: list[str] = []   # video IDs
    trusted_channels: list[str] = []  # channel IDs that produce good results
    suspicious_patterns: list[str] = []  # title patterns that produce false positives
    created_at: datetime
    updated_at: datetime
```

### 5.2 Candidate Model

```python
class VideoCandidate(BaseModel):
    id: str
    title: str
    channel: str
    channel_id: str
    duration_seconds: int
    url: str
    published: datetime
    
    # Classification
    classification: Literal["likely", "uncertain", "false_positive"] | None
    classification_reason: str | None
    confidence: float = 0.0
    
    # User decision
    confirmed: bool | None = None
    rejected: bool | None = None

class CandidateSet(BaseModel):
    query: str
    identity_slug: str | None
    candidates: list[VideoCandidate]
    created_at: datetime
```

### 5.3 Quote Model

```python
class Quote(BaseModel):
    text: str
    source_id: str
    source_title: str
    timestamp_approx: str | None  # "5:23" or None
    context: str | None
    themes: list[str] = []
    sentiment: float = 0.0  # -1 to 1
    is_contrarian: bool = False
    
class QuoteCollection(BaseModel):
    subject: str
    quotes: list[Quote]
    created_at: datetime
```

### 5.4 Theme Model (Enhanced)

```python
class Theme(BaseModel):
    name: str
    description: str
    frequency: int
    confidence: float
    supporting_quotes: list[Quote]
    related_themes: list[str] = []
    is_distinctive: bool = False  # True if contrarian/unusual
    
class ThemeAnalysis(BaseModel):
    subject: str
    themes: list[Theme]
    total_sources: int
    created_at: datetime
```

---

## 6. Classification Heuristics

### 6.1 Video Candidate Classification

```python
def classify_candidate(
    candidate: VideoCandidate,
    query: str,
    identity: Identity | None = None
) -> tuple[str, str, float]:
    """
    Returns (classification, reason, confidence)
    """
    title_lower = candidate.title.lower()
    query_lower = query.lower()
    query_parts = query_lower.split()
    
    # Check against known channels
    if identity and candidate.channel_id in identity.trusted_channels:
        return ("likely", "from trusted channel", 0.95)
    
    if identity and candidate.channel_id in [c.id for c in identity.channels]:
        return ("likely", "from subject's own channel", 0.99)
    
    # Check if already confirmed/rejected
    if identity:
        if candidate.id in identity.confirmed_videos:
            return ("likely", "previously confirmed", 1.0)
        if candidate.id in identity.rejected_videos:
            return ("false_positive", "previously rejected", 1.0)
    
    # Full name in title
    if query_lower in title_lower:
        return ("likely", "full name in title", 0.85)
    
    # All name parts in title
    if all(part in title_lower for part in query_parts):
        # Check for false positive patterns
        if identity and any(p in title_lower for p in identity.suspicious_patterns):
            return ("false_positive", "matches suspicious pattern", 0.7)
        return ("likely", "all name parts in title", 0.75)
    
    # Interview/podcast format indicators
    interview_indicators = ["interview", "podcast", "conversation", "talks with", "featuring"]
    if any(ind in title_lower for ind in interview_indicators):
        if any(part in title_lower for part in query_parts):
            return ("uncertain", "interview format with partial match", 0.5)
    
    # Music/entertainment channels (common false positive)
    entertainment_indicators = ["cover", "reaction", "music video", "official video", "lyrics"]
    if any(ind in title_lower for ind in entertainment_indicators):
        return ("false_positive", "entertainment content", 0.8)
    
    # Partial match only
    if any(part in title_lower for part in query_parts):
        return ("uncertain", "partial name match", 0.3)
    
    # No match
    return ("false_positive", "no name match", 0.9)
```

### 6.2 Learning from User Feedback

```python
def update_identity_from_feedback(
    identity: Identity,
    candidate: VideoCandidate,
    confirmed: bool
):
    """Update identity heuristics based on user confirmation."""
    if confirmed:
        identity.confirmed_videos.append(candidate.id)
        
        # Trust this channel more
        if candidate.channel_id not in identity.trusted_channels:
            # Check if multiple videos from this channel confirmed
            confirmed_from_channel = sum(
                1 for vid_id in identity.confirmed_videos
                if get_video_channel(vid_id) == candidate.channel_id
            )
            if confirmed_from_channel >= 2:
                identity.trusted_channels.append(candidate.channel_id)
    else:
        identity.rejected_videos.append(candidate.id)
        
        # Learn suspicious patterns
        # Extract potential false-positive patterns from title
        patterns = extract_suspicious_patterns(candidate.title, identity.display_name)
        for pattern in patterns:
            if pattern not in identity.suspicious_patterns:
                identity.suspicious_patterns.append(pattern)
```

---

## 7. Quote Extraction Algorithm

### 7.1 Heuristic Extraction

```python
def extract_quotes(
    text: str,
    source_id: str,
    source_title: str,
    min_length: int = 10,
    max_length: int = 100
) -> list[Quote]:
    """Extract notable quotes using heuristics."""
    quotes = []
    sentences = split_sentences(text)
    
    for i, sentence in enumerate(sentences):
        words = sentence.split()
        if not (min_length <= len(words) <= max_length):
            continue
        
        score = 0.0
        reasons = []
        
        # Strong opinion indicators
        opinion_starters = [
            "I believe", "I think", "The truth is", "Most people",
            "The problem is", "What matters is", "The key is",
            "Contrary to", "Unlike most", "The reality is"
        ]
        for starter in opinion_starters:
            if sentence.lower().startswith(starter.lower()):
                score += 0.3
                reasons.append(f"starts with '{starter}'")
                break
        
        # Contrarian indicators
        contrarian_phrases = [
            "but actually", "however", "on the contrary",
            "most people think", "conventional wisdom",
            "the opposite is true", "counterintuitively"
        ]
        for phrase in contrarian_phrases:
            if phrase in sentence.lower():
                score += 0.2
                reasons.append("contrarian indicator")
                break
        
        # Named entities or specific claims
        if has_named_entities(sentence):
            score += 0.15
            reasons.append("contains named entities")
        
        if has_numbers_or_statistics(sentence):
            score += 0.1
            reasons.append("contains specifics")
        
        # Emotional intensity
        sentiment = analyze_sentiment(sentence)
        if abs(sentiment) > 0.5:
            score += 0.1
            reasons.append("strong sentiment")
        
        # Repeated across corpus (would need corpus context)
        # This would be a second pass
        
        if score >= 0.3:
            quotes.append(Quote(
                text=sentence.strip(),
                source_id=source_id,
                source_title=source_title,
                timestamp_approx=estimate_timestamp(i, len(sentences)),
                context=get_surrounding_context(sentences, i),
                sentiment=sentiment,
                is_contrarian="contrarian" in " ".join(reasons)
            ))
    
    return sorted(quotes, key=lambda q: q.sentiment, reverse=True)
```

### 7.2 LLM-Assisted Extraction

For higher quality, use LLM to extract quotes:

```python
QUOTE_EXTRACTION_PROMPT = """
Analyze this transcript and extract the most notable quotes.

Focus on:
1. Statements of belief or opinion ("I believe...", "The truth is...")
2. Contrarian or counterintuitive claims
3. Specific, concrete statements (with names, numbers, examples)
4. Memorable or quotable phrases
5. Statements that reveal core worldview

For each quote, provide:
- The exact quote (verbatim from transcript)
- Why it's notable
- What theme or belief it represents

Transcript:
{transcript}

Return as JSON array of quotes.
"""
```

---

## 8. Synthesis Enhancement

### 8.1 Quote-Grounded Synthesis

Instead of: keywords → clusters → generic synthesis

New approach: transcripts → quotes → themes → grounded synthesis

```python
GROUNDED_SYNTHESIS_PROMPT = """
Based on these quotes from {subject}'s appearances, identify their core worldview.

QUOTES:
{quotes_with_sources}

For each worldview point:
1. State the belief clearly and specifically
2. Provide 2-3 direct quotes that support this belief
3. Explain what's distinctive or contrarian about this view
4. Rate confidence based on how many quotes support it

REQUIREMENTS:
- Every point MUST be supported by actual quotes
- NO generic statements like "believes X is important"
- Focus on what makes {subject}'s view DIFFERENT from mainstream
- Be specific: use proper nouns, concrete claims, named concepts

Return as JSON.
"""
```

### 8.2 Iterative Refinement

Allow user to refine synthesis:

```bash
wve synthesize transcripts/ --subject "Skinner Layne" -o worldview.json

# User reviews, provides feedback
wve refine-synthesis worldview.json \
  --feedback "Point 3 is too generic, dig deeper on education views"
```

The refinement prompt includes:
- Original synthesis
- User feedback
- Full transcript access for finding supporting evidence

---

## 9. Storage & Caching

### 9.1 Identity Storage

```
~/.wve/
├── identities/
│   ├── skinner-layne.json
│   ├── em-burlingame.json
│   └── ...
├── cache/
│   ├── transcripts/
│   │   └── {video_id}.txt
│   ├── embeddings/
│   │   └── {content_hash}.npy
│   └── search/
│       └── {query_hash}.json
└── config.toml
```

### 9.2 Project-Local Storage

When used within a project (like capablefew):

```
episodes/josh-rieder/
└── wve/
    ├── identity.json        # Local identity snapshot
    ├── candidates.json      # Search candidates
    ├── confirmed.json       # Confirmed videos
    ├── transcripts/
    │   ├── manifest.json
    │   └── *.txt
    ├── themes.json
    ├── quotes.json
    ├── contrast.json
    └── worldview-report.md
```

---

## 10. CLI Design Principles

### 10.1 Human Mode (Default)

- Interactive prompts for decisions
- Rich terminal output with colors
- Progress indicators
- Confirmation before destructive actions

### 10.2 Robot Mode (--json, --yes, --quiet)

- `--json`: All output as JSON to stdout, logs to stderr
- `--yes`: Auto-confirm all prompts
- `--quiet`: Minimal output, exit codes only
- `--stdin`: Accept input from pipe

Example robot usage:
```bash
wve discover "Name" --json --auto-classify | \
  jq '.candidates[] | select(.classification == "likely")' | \
  wve fetch --stdin --json -o transcripts/
```

### 10.3 Consistent Patterns

All commands follow:
```
wve <verb> <input> [options]
```

Common options across all commands:
- `-o, --output`: Output file/directory
- `--json`: JSON output mode
- `--quiet`: Minimal output
- `--verbose`: Debug output
- `--identity SLUG`: Use identity context

---

## 11. Implementation Priority

### Phase 1: Core Identity & Discovery (Week 1)

1. `wve identity create/list/show`
2. `wve discover` with classification heuristics
3. `wve confirm` (interactive and batch)
4. `wve fetch` (replaces current transcript download)

### Phase 2: Source Commands (Week 2)

5. `wve from-channel`
6. `wve from-urls`
7. Enhanced `wve dump`

### Phase 3: Analysis Commands (Week 3)

8. `wve quotes`
9. `wve themes` (quote-grounded)
10. `wve contrast`

### Phase 4: Refinement & Reports (Week 4)

11. `wve refine`
12. `wve report`
13. `wve suggest`
14. Integration with capablefew pipeline

---

## 12. Success Metrics

### 12.1 Identity Resolution

- **Precision:** >95% of fetched videos are correct person
- **Recall:** >80% of available relevant videos discovered
- **Efficiency:** <5 videos rejected per identity on average

### 12.2 Quote Extraction

- **Relevance:** >80% of extracted quotes are genuinely notable
- **Coverage:** Key themes have 3+ supporting quotes
- **Accuracy:** Quotes are verbatim from source

### 12.3 Synthesis Quality

- **Groundedness:** 100% of worldview points cite specific quotes
- **Distinctiveness:** >50% of points are non-obvious/contrarian
- **Specificity:** 0 generic platitudes ("X is important")

### 12.4 User Experience

- **Time to first insight:** <10 minutes for known-channel workflow
- **Interaction overhead:** <5 confirmations for well-known person
- **Automation success:** >80% accuracy with --auto-classify for unique names

---

## 13. Open Questions

1. **Whisper integration:** Should we auto-transcribe videos without captions?
   - Pro: More content accessible
   - Con: Slow, requires GPU for quality
   
2. **Multi-language support:** How to handle non-English content?
   - Translation before analysis?
   - Language-specific models?
   
3. **Video vs. Audio:** Should we analyze visual content (slides, etc.)?
   - Pro: Richer context
   - Con: Significant complexity
   
4. **Real-time updates:** Should identities auto-update when new videos appear?
   - Could run as background job
   - RSS-style monitoring

5. **Collaboration:** Should identities be shareable?
   - Export/import identities
   - Community-curated identity database?
