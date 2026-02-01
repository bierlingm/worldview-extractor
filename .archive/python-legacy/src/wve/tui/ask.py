"""Ask interface for wve TUI."""

import os
import subprocess
from pathlib import Path
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Static, Input, Select

from wve.config import get_config


class AskScreen(Screen):
    """Interactive Q&A interface for worldviews."""
    
    BINDINGS = [
        Binding("escape", "back", "Back", show=False),
        Binding("ctrl+l", "clear", "Clear", show=False),
    ]
    
    CSS = """
    #ask-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    
    #subject-selector {
        width: 100%;
        height: 3;
        margin-bottom: 1;
    }
    
    #conversation {
        width: 100%;
        height: 1fr;
        padding: 1;
        margin-bottom: 1;
    }
    
    #question-input {
        width: 100%;
    }
    
    .message {
        margin-bottom: 1;
    }
    """
    
    def __init__(self, slug: str | None = None):
        super().__init__()
        self.current_slug = slug
        self.messages: list[dict] = []
        self.is_loading = False
    
    def compose(self) -> ComposeResult:
        with Vertical(id="ask-container"):
            yield Select(
                [],
                prompt="Select a worldview",
                id="subject-selector",
            )
            with ScrollableContainer(id="conversation"):
                yield Static(
                    "[dim]Ask a question about the selected worldview...[/dim]",
                    classes="empty-state",
                )
            yield Input(
                placeholder="What do they think about...",
                id="question-input",
            )
        yield Static("[esc] back  [ctrl+l] clear  [enter] ask")
    
    def on_mount(self) -> None:
        self._load_subjects()
        self.query_one("#question-input", Input).focus()
    
    def _load_subjects(self) -> None:
        """Load available worldviews."""
        try:
            from wve.store import list_entries
            entries = list_entries()
            options = [(e.display_name, e.slug) for e in entries]
        except Exception:
            options = []
        
        selector = self.query_one("#subject-selector", Select)
        selector.set_options(options)
        
        if self.current_slug:
            selector.value = self.current_slug
        elif options:
            selector.value = options[0][1]
            self.current_slug = options[0][1]
    
    def on_select_changed(self, event: Select.Changed) -> None:
        self.current_slug = event.value
        self._clear_conversation()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "question-input":
            self._send_question()
    
    def _send_question(self) -> None:
        """Send the current question."""
        if self.is_loading or not self.current_slug:
            return
        
        input_widget = self.query_one("#question-input", Input)
        question = input_widget.value.strip()
        if not question:
            return
        
        input_widget.value = ""
        self._add_message("user", question)
        self.is_loading = True
        self._get_answer(question)
    
    def _add_message(self, role: str, content: str, sources: list[str] | None = None) -> None:
        """Add a message to the conversation."""
        self.messages.append({"role": role, "content": content, "sources": sources})
        self._render_conversation()
    
    def _render_conversation(self) -> None:
        """Render all messages."""
        container = self.query_one("#conversation", ScrollableContainer)
        
        for child in list(container.children):
            child.remove()
        
        if not self.messages and not self.is_loading:
            container.mount(Static(
                "[dim]Ask a question about the selected worldview...[/dim]",
                classes="empty-state placeholder",
            ))
            return
        
        for msg in self.messages:
            if msg["role"] == "user":
                widget = Static(
                    f"[bold]You:[/bold] {msg['content']}",
                    classes="message user-message",
                )
            else:
                content = f"[bold]Answer:[/bold]\n{msg['content']}"
                if msg.get("sources"):
                    content += f"\n\n[dim]Sources: {', '.join(msg['sources'])}[/dim]"
                widget = Static(content, classes="message assistant-message")
            
            container.mount(widget)
        
        if self.is_loading:
            container.mount(Static("[dim]Building prompt...[/dim]", classes="loading-indicator"))
        
        container.scroll_end(animate=False)
    
    def _build_context(self, question: str) -> str:
        """Build context from transcripts."""
        try:
            from wve.store import load_entry
            
            entry = load_entry(self.current_slug)
            
            if not entry.transcripts_dir:
                return ""
            
            transcripts_path = Path(entry.transcripts_dir)
            if not transcripts_path.exists():
                return ""
            
            context_parts = []
            for txt_file in sorted(transcripts_path.glob("*.txt"))[:10]:
                content = txt_file.read_text(encoding="utf-8")
                excerpt = content[:2000]
                if len(content) > 2000:
                    excerpt += "..."
                context_parts.append(f"--- {txt_file.stem} ---\n{excerpt}")
            
            return "\n\n".join(context_parts)
        except Exception:
            return ""
    
    def _copy_to_clipboard(self, text: str) -> bool:
        """Copy text to clipboard using pbcopy (macOS)."""
        try:
            process = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
                env={**os.environ, "LANG": "en_US.UTF-8"}
            )
            process.communicate(text.encode("utf-8"))
            return process.returncode == 0
        except Exception:
            return False
    
    def _get_answer(self, question: str) -> None:
        """Build prompt with context and copy to clipboard."""
        try:
            from wve.store import load_entry
            
            entry = load_entry(self.current_slug)
            display_name = entry.display_name if entry else self.current_slug
            
            context = self._build_context(question)
            
            if not context:
                self._add_message("assistant", "No transcripts found for this worldview.")
                self.is_loading = False
                self._render_conversation()
                return
            
            prompt = f"""Based on {display_name}'s worldview from these transcripts:

{context}

Question: {question}

Please answer based on what this person would likely think or say, drawing from the context provided."""
            
            if self._copy_to_clipboard(prompt):
                agent = os.environ.get("WVE_AGENT") or get_config().defaults.get("agent")
                if agent:
                    self._add_message(
                        "assistant",
                        f"Prompt copied to clipboard. Opening {agent}..."
                    )
                    self._launch_agent(agent, prompt)
                else:
                    self._add_message(
                        "assistant",
                        "Prompt copied to clipboard. Paste into your AI assistant."
                    )
            else:
                self._add_message("assistant", "Failed to copy to clipboard.")
        except Exception as e:
            self._add_message("assistant", f"Error: {str(e)}")
        finally:
            self.is_loading = False
            self._render_conversation()
    
    def _launch_agent(self, agent: str, prompt: str) -> None:
        """Launch configured agent."""
        agent_urls = {
            "claude": "https://claude.ai/new",
            "chatgpt": "https://chat.openai.com/",
            "gemini": "https://gemini.google.com/",
        }
        
        url = agent_urls.get(agent.lower())
        if url:
            try:
                subprocess.run(["open", url], check=False)
            except Exception:
                pass
    
    def _clear_conversation(self) -> None:
        """Clear the conversation."""
        self.messages.clear()
        container = self.query_one("#conversation", ScrollableContainer)
        children = list(container.children)
        for child in children:
            child.remove()
        container.mount(Static(
            "[dim]Ask a question about the selected worldview...[/dim]",
            classes="empty-state placeholder",
        ))
    
    def action_back(self) -> None:
        self.app.pop_screen()
    
    def action_clear(self) -> None:
        self._clear_conversation()
