# wve TUI v2: Keyboard-First Terminal Interface

## The Problem with v1

The current TUI feels like a desktop app shoehorned into a terminal:
- Big buttons requiring navigation
- Modal screens with chrome (headers, footers)
- App-like flow that fights the terminal
- Dumps results and exits without integration

## Design Philosophy

### The TUI Commandments (adapted from bczsalba.com)

1. **Do few things exceptionally** - wve should launch, help you pick what to extract, and get out of the way
2. **Deterministic interface** - same inputs = same results, no surprises
3. **Single keypress as basic unit** - every action is one key, not Tab→Tab→Enter
4. **User configurable** - keybinds and colors should be overridable
5. **Use CLI arguments** - TUI should be a thin interactive layer over CLI
6. **Launch and terminate immediately** - no loading screens, no spinners for UI
7. **Avoid reimplementing terminal behavior** - use native scrollback, selection
8. **Use TUI with purpose** - if `wve discover "Naval"` works, don't wrap it in UI

### Inspiration: Best-in-Class Tools

| Tool | What it does right |
|------|-------------------|
| **fzf** | Single purpose, instant feedback, composes with everything |
| **lazygit** | Panels show context, single keys do actions, `?` shows help |
| **tig** | Vim-like navigation, inline help, respects terminal |
| **gum** | Beautiful prompts that compose, returns values to shell |
| **gh** | Interactive when needed, CLI when not, `--help` is gold |

## Core Principles

### 1. Interactive Filter, Not Application

Instead of an "app" with screens, wve should be a series of **composable prompts**:

```
$ wve
? Who do you want to understand? [type to filter recent, or enter new]
> Naval Ravikant
  Balaji Srinivasan  
  Paul Graham
  [+ New subject]
  
? Where to find content? [↑↓ to select, enter to confirm]
> 🔍 YouTube search "Naval Ravikant"
  📺 From YouTube channel
  🔗 Paste video URLs
  📁 Local files
  
Searching YouTube for "Naval Ravikant"...
Found 47 candidates (23 likely, 15 uncertain, 9 unlikely)

? Review candidates? [y/N] y

[launches fzf-style picker with candidates]
```

### 2. Inline Help, Not Hidden

Every prompt shows available keys:

```
? Select videos to include:
  [space] toggle  [a] all  [n] none  [tab] preview  [enter] confirm  [?] help
  
  ✓ Naval Ravikant on The Tim Ferriss Show (42m)
  ✓ Naval: How to Get Rich (1h2m) 
    Naval Discusses Meditation (likely different person)
  ✓ The Almanack of Naval Ravikant - Full Audiobook (3h)
```

### 3. Progressive Disclosure

Start minimal, reveal on demand:

```
$ wve                              # Interactive mode
$ wve "Naval Ravikant"             # Skip to source selection  
$ wve "Naval" --search             # Skip to YouTube search
$ wve "Naval" --search -y          # Auto-accept likely, no interaction
```

### 4. Return Values, Not Side Effects

The TUI should produce commands/data, not execute them:

```
$ wve
...wizard...
→ wve discover "Naval Ravikant" | wve confirm --accept-likely | wve fetch -o transcripts/

Run this pipeline? [Y/n/e(dit)]
```

Or for simple cases, just do the work inline with a progress bar.

## Interface Patterns

### Pattern 1: Fuzzy Select (fzf-style)

For picking from lists (subjects, videos, worldviews):

```
┌────────────────────────────────────────────────────────────┐
│ > nav                                                      │
│   3/47                                                     │
│ > Naval Ravikant on The Tim Ferriss Show #473         42m  │
│   Naval: How to Get Rich Without Getting Lucky        62m  │
│   The Almanack of Naval Ravikant - Audiobook         180m  │
└────────────────────────────────────────────────────────────┘
```

Keys: Type to filter, ↑↓ or j/k to move, Enter to select, Esc to cancel, Tab to preview

### Pattern 2: Multi-Select (fzf --multi style)

For selecting multiple items:

```
┌────────────────────────────────────────────────────────────┐
│ > nav                                              3 sel   │
│   47 candidates                                            │
│ ✓ Naval Ravikant on Tim Ferriss                       42m  │
│ ✓ Naval: How to Get Rich                              62m  │
│   Naval-like name discussing unrelated topic          15m  │
│ ✓ Almanack of Naval - Audiobook                      180m  │
├────────────────────────────────────────────────────────────┤
│ space:toggle  a:all  n:none  tab:preview  enter:done       │
└────────────────────────────────────────────────────────────┘
```

### Pattern 3: Quick Prompts (gum-style)

For simple inputs:

```
Subject name: Naval Ravikant█
```

For choices:

```
Source type:
> YouTube search
  Channel URL
  Video URLs
  Local files
```

### Pattern 4: Progress (inline, not modal)

```
Fetching transcripts... ████████████░░░░░░░░ 12/20  [naval-tim-ferriss.txt]
```

### Pattern 5: Preview Pane (tig/lazygit style)

When Tab is pressed on a candidate:

```
┌─ Candidates ──────────────────┬─ Preview ─────────────────────┐
│ > Naval on Tim Ferriss    42m │ Channel: Tim Ferriss          │
│   Naval: How to Get Rich  62m │ Published: 2024-03-15         │
│   Almanack Audiobook     180m │ Duration: 42 minutes          │
│                               │ Views: 2.4M                   │
│                               │                               │
│                               │ Description:                  │
│                               │ In this episode, Naval and    │
│                               │ Tim discuss wealth, happi...  │
└───────────────────────────────┴───────────────────────────────┘
```

## Proposed Flows

### Flow 1: New Extraction (Happy Path)

```
$ wve

wve · worldview extraction

? Subject: Naval Ravikant
? Source: YouTube search (↑↓ enter)

Searching... found 47 candidates

? Select videos: (space:toggle  a:all-likely  enter:done)
  [23 likely pre-selected]
  
Selected 23 videos. Fetching transcripts...
████████████████████████████████ 23/23 done

Analyzing 23 transcripts...
████████████████████████████████ done

✓ Worldview saved: naval-ravikant

  12 transcripts · 47 quotes · 8 themes
  
  Top themes: wealth, happiness, leverage, reading, meditation
  
  Next: wve ask naval-ravikant "What does he think about X?"
        wve show naval-ravikant
```

### Flow 2: Browse Library

```
$ wve browse     # or just: wve b

┌────────────────────────────────────────────────────────────┐
│ > Search library...                                        │
│   5 worldviews                                             │
│                                                            │
│ > naval-ravikant        12 sources  47 quotes   2024-01    │
│   balaji-srinivasan      8 sources  31 quotes   2024-01    │
│   paul-graham           15 sources  52 quotes   2023-12    │
├────────────────────────────────────────────────────────────┤
│ enter:view  d:delete  a:ask  n:new  q:quit                 │
└────────────────────────────────────────────────────────────┘
```

Pressing enter on a worldview:

```
naval-ravikant · Naval Ravikant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sources: 12 transcripts
Quotes:  47 notable, 8 contrarian
Themes:  wealth, happiness, leverage, reading, meditation

Top Quotes:
  1. "Seek wealth, not money or status. Wealth is having assets that
     earn while you sleep."
  2. "Play iterated games. All the returns in life come from compound
     interest in long-term games."
  3. ...

[a] ask  [t] themes  [q] quotes  [r] report  [esc] back
```

### Flow 3: Ask Question

```
$ wve ask naval-ravikant "What does he think about reading?"

# Or interactively:
$ wve ask

? Which worldview? naval-ravikant
? Question: What does he think about reading?

Searching 12 transcripts...

Naval on Reading
━━━━━━━━━━━━━━━━

Naval emphasizes reading as a foundational habit for building wealth
and happiness. Key points:

• Read what you love until you love to read
• Reread the great books rather than racing through new ones
• "I don't want to read everything. I just want to read the 100 
   great books over and over again."

Sources: tim-ferriss-473.txt, joe-rogan-1309.txt

[c] copy  [o] open in $EDITOR  [a] ask another  [q] quit
```

## Implementation Approach

### Option A: Stay with Textual, Simplify Radically

Strip current TUI to essentials:
- Remove Header/Footer chrome
- Remove Button widgets entirely
- Use Input + ListView as core primitives
- Single-screen flow with inline state changes
- Keyboard hints at bottom as plain text

Pros: Python-native, already have it working
Cons: Textual wants to be an app framework, fighting its nature

### Option B: Use prompt_toolkit

Python library that powers IPython, designed for exactly this:
- Fuzzy completion built-in
- Multi-line editing
- Key bindings are first-class
- Composes well with Click

Pros: Perfect fit for keyboard-first prompts
Cons: New dependency, learning curve

### Option C: Shell out to gum/fzf

Use charmbracelet's gum or fzf for interactive bits:

```python
def select_source():
    result = subprocess.run([
        "gum", "choose", 
        "YouTube search",
        "Channel URL",
        "Video URLs",
        "Local files"
    ], capture_output=True, text=True)
    return result.stdout.strip()
```

Pros: Best-in-class UX immediately, tiny code
Cons: External dependency, user must install

### Option D: Hybrid (Recommended)

- Use Click + Rich for basic CLI
- Use prompt_toolkit for interactive prompts
- Use simple ANSI for progress bars
- Fall back to plain input() if prompt_toolkit unavailable

```python
@cli.command()
@click.argument('subject', required=False)
def new(subject):
    """Start a new worldview extraction."""
    
    # If no subject, prompt interactively
    if not subject:
        subject = prompt_subject()  # prompt_toolkit fuzzy
    
    # Show source choices
    source = prompt_source()  # prompt_toolkit select
    
    if source == "search":
        # Do the search, show results
        candidates = discover(subject)
        
        # Let user filter/select
        selected = prompt_select_videos(candidates)  # fzf-style
        
        # Fetch and analyze
        with progress_bar() as p:
            transcripts = fetch_transcripts(selected, progress=p)
            worldview = analyze(transcripts, progress=p)
        
        # Show summary
        show_summary(worldview)
```

## Key Bindings Standard

Following vim/readline conventions:

| Key | Action |
|-----|--------|
| `j/↓` | Move down |
| `k/↑` | Move up |
| `h/←` | Collapse/left |
| `l/→` | Expand/right |
| `g/Home` | Go to top |
| `G/End` | Go to bottom |
| `Enter` | Confirm/select |
| `Esc/q` | Back/quit |
| `Space` | Toggle selection |
| `Tab` | Preview/expand |
| `/` | Search/filter |
| `?` | Show help |
| `Ctrl-C` | Abort immediately |

## Migration Path

### Phase 1: Simplify Current TUI
- Remove buttons, use key hints
- Remove modal screens, use inline state
- Make Enter work everywhere
- Remove app chrome

### Phase 2: Add prompt_toolkit
- Replace Textual inputs with prompt_toolkit
- Add fuzzy select for worldview browser
- Add multi-select for video candidates

### Phase 3: Polish
- Add preview panes
- Add progress bars
- Add configuration file for keybinds
- Add shell completions

## File Structure

```
wve/
├── cli.py              # Main Click entrypoint
├── prompts/
│   ├── __init__.py
│   ├── subject.py      # Subject name input
│   ├── source.py       # Source type selection  
│   ├── select.py       # Multi-select for videos
│   └── confirm.py      # Yes/no confirmations
├── display/
│   ├── __init__.py
│   ├── summary.py      # Worldview summary display
│   ├── progress.py     # Progress bars
│   └── table.py        # Tabular output
└── ...
```

## Success Criteria

1. **Time to first action** < 500ms (no loading screens)
2. **Keystrokes to complete common task** < 10
3. **Works without mouse** 100%
4. **Works in tmux/screen** 100%
5. **Works with piping** `wve discover "X" | wve confirm -y | wve fetch`
6. **Graceful degradation** Plain prompts if fancy libs unavailable

## Open Questions

1. Should `wve` with no args show the fuzzy browser or the new-extraction wizard?
2. Should we require prompt_toolkit or make it optional?
3. Should video preview fetch metadata from YouTube (slower) or just show what we have?
4. Should the "ask" feature launch Claude/configured agent, or run local RAG?

## References

- [TUI Commandments](https://bczsalba.com/post/the-tui-commandments)
- [fzf Getting Started](https://junegunn.github.io/fzf/getting-started/)
- [lazygit](https://github.com/jesseduffield/lazygit)
- [gum](https://github.com/charmbracelet/gum)
- [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/)
- [Julia Evans: Terminal Rules](https://jvns.ca/blog/2024/11/26/terminal-rules/)
