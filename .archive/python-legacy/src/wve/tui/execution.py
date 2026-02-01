"""In-TUI execution screen for running extraction pipelines."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static, Log
from textual.worker import Worker, WorkerState

from wve.tui.wizard import WizardState


class ExecutionScreen(Screen):
    """Run extraction pipeline within the TUI."""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("q", "done", "Done", show=False),
    ]
    
    def __init__(self, state: WizardState):
        super().__init__()
        self.state = state
        self._worker: Worker | None = None
        self._done = False
    
    def compose(self) -> ComposeResult:
        yield Vertical(
            Static(f"[bold]Extracting worldview for: {self.state.subject}[/bold]", id="title"),
            Static("", id="status"),
            Log(id="log", auto_scroll=True),
            Static("", id="hints"),
            id="execution-container",
        )
    
    def on_mount(self) -> None:
        self._update_hints()
        self._worker = self.run_worker(self._run_extraction(), exclusive=True)
    
    def _log(self, msg: str) -> None:
        self.query_one("#log", Log).write_line(msg)
    
    def _set_status(self, msg: str) -> None:
        self.query_one("#status", Static).update(f"[cyan]{msg}[/cyan]")
    
    def _update_hints(self) -> None:
        hints = self.query_one("#hints", Static)
        if self._done:
            hints.update("[bold cyan]q[/] close  [bold cyan]esc[/] back to menu")
        else:
            hints.update("[bold cyan]esc[/] cancel")
    
    async def _run_extraction(self) -> None:
        """Run the extraction pipeline."""
        from wve.classify import CandidateSet, VideoCandidate, classify_candidates
        from wve.identity import slugify
        from wve.search import search_videos
        from wve.transcripts import download_transcript
        from wve.store import get_entry_dir, store_worldview
        
        subject = self.state.subject
        
        if self.state.source_type == "search":
            await self._run_search_flow(subject)
        elif self.state.source_type == "channel":
            await self._run_channel_flow(subject, self.state.channel_url)
        elif self.state.source_type == "urls":
            await self._run_urls_flow(subject, self.state.urls)
        else:
            await self._run_local_flow(subject)
        
        self._done = True
        self._update_hints()
    
    async def _run_search_flow(self, subject: str) -> None:
        """Run YouTube search extraction flow."""
        from wve.classify import CandidateSet, VideoCandidate, classify_candidates
        from wve.search import search_videos
        from wve.transcripts import download_transcript
        from wve.store import get_entry_dir
        
        self._set_status("Searching YouTube...")
        self._log(f"Searching for: {subject}")
        
        results = search_videos(subject, max_results=20)
        self._log(f"Found {len(results.videos)} videos")
        
        candidates = [
            VideoCandidate(
                id=v.id,
                url=f"https://youtube.com/watch?v={v.id}",
                title=v.title,
                channel=v.channel,
                duration_seconds=v.duration_seconds,
                published=v.published,
            )
            for v in results.videos
        ]
        
        candidate_set = CandidateSet(subject=subject, candidates=candidates)
        classify_candidates(candidate_set)
        
        likely = [c for c in candidates if c.classification == "likely"]
        self._log(f"Classified: {len(likely)} likely candidates")
        
        if not likely:
            self._set_status("No likely candidates found")
            self._log("[dim]Try a more specific search term[/dim]")
            return
        
        from wve.identity import slugify
        slug = slugify(subject)
        output_dir = get_entry_dir(slug) / "transcripts"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self._set_status("Downloading transcripts...")
        succeeded = 0
        for i, c in enumerate(likely, 1):
            self._log(f"[{i}/{len(likely)}] {c.title[:50]}...")
            result = download_transcript(c.url, output_dir, "en")
            if result:
                succeeded += 1
        
        self._log(f"Downloaded {succeeded}/{len(likely)} transcripts")
        
        if succeeded > 0:
            self._set_status("Running analysis...")
            await self._run_analysis(subject, str(output_dir))
        else:
            self._set_status("No transcripts downloaded")
    
    async def _run_channel_flow(self, subject: str, channel_url: str) -> None:
        """Run channel extraction flow."""
        import subprocess
        
        self._set_status("Fetching channel videos...")
        self._log(f"Channel: {channel_url}")
        
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--no-warnings",
            "-j",
            channel_url,
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            self._log("[red]Timeout fetching channel[/red]")
            self._set_status("Failed")
            return
        
        if result.returncode != 0 and not result.stdout.strip():
            self._log(f"[red]Failed: {result.stderr}[/red]")
            self._set_status("Failed")
            return
        
        import json
        videos = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("id"):
                    videos.append({
                        "id": data["id"],
                        "title": data.get("title", "Unknown"),
                        "url": f"https://youtube.com/watch?v={data['id']}",
                    })
            except json.JSONDecodeError:
                continue
        
        self._log(f"Found {len(videos)} videos")
        
        from wve.identity import slugify
        from wve.store import get_entry_dir
        from wve.transcripts import download_transcript
        
        slug = slugify(subject)
        output_dir = get_entry_dir(slug) / "transcripts"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self._set_status("Downloading transcripts...")
        succeeded = 0
        for i, v in enumerate(videos[:20], 1):  # Limit to first 20
            self._log(f"[{i}/{min(20, len(videos))}] {v['title'][:50]}...")
            result = download_transcript(v["url"], output_dir, "en")
            if result:
                succeeded += 1
        
        self._log(f"Downloaded {succeeded} transcripts")
        
        if succeeded > 0:
            self._set_status("Running analysis...")
            await self._run_analysis(subject, str(output_dir))
        else:
            self._set_status("No transcripts downloaded")
    
    async def _run_urls_flow(self, subject: str, urls: list[str]) -> None:
        """Run extraction from specific URLs."""
        from wve.identity import slugify
        from wve.store import get_entry_dir
        from wve.transcripts import download_transcript
        
        self._set_status("Downloading transcripts...")
        
        slug = slugify(subject)
        output_dir = get_entry_dir(slug) / "transcripts"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        succeeded = 0
        for i, url in enumerate(urls, 1):
            self._log(f"[{i}/{len(urls)}] {url[:50]}...")
            result = download_transcript(url, output_dir, "en")
            if result:
                succeeded += 1
        
        self._log(f"Downloaded {succeeded}/{len(urls)} transcripts")
        
        if succeeded > 0:
            self._set_status("Running analysis...")
            await self._run_analysis(subject, str(output_dir))
        else:
            self._set_status("No transcripts downloaded")
    
    async def _run_local_flow(self, subject: str) -> None:
        """Run extraction from local files."""
        self._set_status("Running analysis...")
        self._log("Using local transcripts in ./transcripts/")
        await self._run_analysis(subject, "./transcripts/")
    
    async def _run_analysis(self, subject: str, transcript_dir: str) -> None:
        """Run the extraction and synthesis pipeline."""
        from pathlib import Path
        
        from wve.extract import extract_all, load_transcripts, save_extraction
        from wve.cluster import cluster_extraction, save_clusters
        from wve.synthesize import synthesize, save_worldview
        from wve.store import get_entry_dir, store_worldview
        from wve.identity import slugify
        
        slug = slugify(subject)
        entry_dir = get_entry_dir(slug)
        entry_dir.mkdir(parents=True, exist_ok=True)
        
        self._log("Loading transcripts...")
        collection = load_transcripts(Path(transcript_dir))
        self._log(f"Loaded {collection.source_count} sources")
        
        self._log("Extracting patterns...")
        extraction = extract_all(collection, subject=subject)
        save_extraction(extraction, str(entry_dir / "extraction.json"))
        self._log(f"Extracted {len(extraction.keywords)} keywords, {len(extraction.quotes)} quotes")
        
        self._log("Clustering themes...")
        clusters = cluster_extraction(extraction)
        save_clusters(clusters, str(entry_dir / "clusters.json"))
        self._log(f"Found {len(clusters.clusters)} clusters")
        
        self._log("Synthesizing worldview...")
        worldview = synthesize(clusters, extraction, subject)
        save_worldview(worldview, str(entry_dir / "worldview.json"))
        
        self._log("Generating report...")
        from wve.report import generate_report
        report_path = entry_dir / "report.md"
        generate_report(worldview, extraction, clusters, report_path)
        
        store_worldview(slug, subject, worldview, extraction, clusters, str(report_path))
        
        self._set_status("Complete!")
        self._log("")
        self._log(f"[green]Worldview saved: {entry_dir}[/green]")
        self._log(f"[green]Report: {report_path}[/green]")
        self._log("")
        self._log(f"[bold]Top themes for {subject}:[/bold]")
        for i, point in enumerate(worldview.points[:5], 1):
            self._log(f"  {i}. {point.theme}")
    
    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.ERROR:
            self._set_status("Error")
            self._log(f"[red]Error: {event.worker.error}[/red]")
            self._done = True
            self._update_hints()
    
    def action_cancel(self) -> None:
        if self._done:
            self.app.pop_screen()
        elif self._worker:
            self._worker.cancel()
            self._set_status("Cancelled")
            self._done = True
            self._update_hints()
    
    def action_done(self) -> None:
        if self._done:
            self.app.pop_screen()
