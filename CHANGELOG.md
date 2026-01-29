# Changelog

## [0.7.0] "Shuttle" - 2026-01-29

The **Shuttle** release rebuilds the TUI from the ground up as a keyboard-first, prompt-based interface inspired by fzf, lazygit, and gum.

### Added

- **Keyboard-first TUI v2** - Completely redesigned interface
  - Stripped all Header/Footer/Button chrome - feels like terminal prompts now
  - Single-keypress actions everywhere (j/k nav, space toggle, enter confirm)
  - Key hints visible at bottom of every screen

- **Standard Keybindings** (`wve/tui/keys.py`)
  - Vim-style navigation (j/k/h/l, arrows)
  - Consistent bindings: Enter=confirm, Esc/q=back, Space=toggle, Tab=preview

- **Prompt Components** (`wve/prompts/`)
  - `FuzzySelect` - fzf-style fuzzy filtering with match count
  - `MultiSelect` - Space to toggle, a=all, n=none, Tab=preview

- **Display Components** (`wve/display/`)
  - `progress_bar()` - Inline progress: `Fetching... ████████░░░░ 8/12 [file.txt]`
  - `InlineProgress` - Textual widget version
  - `show_extraction_complete()` - Clean summary without boxes
  - `format_video_preview()` - Lazy-loaded metadata preview

- **Browse Command** - `wve browse` / `wve b` for fuzzy library search

- **Progressive CLI Disclosure**
  - `wve` = full interactive
  - `wve "Naval"` = skip subject prompt
  - `wve "Naval" --search` = skip to YouTube search
  - `wve "Naval" -s -y` = fully non-interactive

- **Config File** (`~/.config/wve/config.toml`)
  - Customizable keybindings, colors, defaults
  - Works without config file

### Changed

- **Inline Wizard** - Replaced multi-screen wizard with single-screen state machine
- **Ask Integration** - Replaced broken Ollama RAG with clipboard-based approach
  - Builds context prompt and copies to clipboard
  - Optional agent launch via `WVE_AGENT` env or config

### Removed

- Modal screens with push_screen/pop_screen
- Button widgets throughout
- App-like chrome (borders, containers styled like windows)

---

## [0.6.0] "Loom" - 2026-01-29

The **Loom** release weaves a rich, delightful terminal experience into wve.

### Added

- **Interactive TUI** - Run `wve` without arguments to launch full Textual app
  - Main menu with keyboard navigation
  - Multi-step extraction wizard (subject → source → confirm → run)
  - Library browser with split-pane view
  - Ask interface with streaming responses
  
- **Theme System** (`wve/theme.py`)
  - Consistent color palette across all commands
  - `get_console()` for themed Rich output
  
- **Branding** (`wve/branding.py`)
  - ASCII logo and tagline
  - `print_banner()` for command headers
  
- **UI Components** (`wve/ui/`)
  - `completion_panel()` - Consistent success output with next steps
  - `error_panel()` - Styled error messages with suggestions
  - `StageProgress` - Multi-stage progress tracking with nested items
  - `ProgressContext` - Context manager for live progress display

- **Auto-install prompt** - When textual not installed, offers to install it

### Changed

- `wve run` now shows branded banner and uses themed completion panels
- Legacy commands hidden from `--help` (still work for scripting):
  - `pipeline` → use `wve run`
  - `search` → use `wve discover`
  - `transcripts` → use `wve run` or `wve fetch`
  - `extract` → use `wve themes` or `wve quotes`
  - `cluster` → use `wve themes`
  - `synthesize` → use `wve run`

### Dependencies

- Added `textual>=0.50.0` as optional `[tui]` extra
- Added `textual-dev>=1.0.0` to dev dependencies

---

## [0.5.0] - Previous Release

Initial v0.2 architecture with identity management, discovery workflow, and persistent store.
