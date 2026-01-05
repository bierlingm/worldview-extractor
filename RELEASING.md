# Releasing wve (Worldview Extractor)

## Version Scheme

Following SemVer: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes to CLI interface or data models
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, documentation

Current: `0.2.0` (pre-1.0, API may change)

## Pre-Release Checklist

### 1. Run Full Test Suite
```bash
source .venv/bin/activate
pytest tests/ -v --cov=wve --cov-report=term-missing
```

All tests must pass. Current: 207 tests.

### 2. Check Type Safety
```bash
mypy src/wve/
```

### 3. Lint
```bash
ruff check src/ tests/
ruff format --check src/ tests/
```

### 4. Manual Smoke Test
```bash
# Identity workflow
wve identity create "Test Person" --slug test
wve identity list
wve identity delete test -y

# Discovery workflow (requires network)
wve discover "Tim Ferriss" --max-results 5 --json | head -20

# Quote extraction (with sample transcripts)
mkdir -p /tmp/wve-test
echo "I believe education is fundamentally broken. Most people think credentials matter, but actually skills matter more." > /tmp/wve-test/sample.txt
wve quotes /tmp/wve-test/ --json
wve report /tmp/wve-test/ -s "Test" --json
rm -rf /tmp/wve-test
```

### 5. Update Version

Edit `src/wve/__init__.py`:
```python
__version__ = "0.2.0"
```

Edit `pyproject.toml`:
```toml
version = "0.2.0"
```

### 6. Update Changelog

Create/update `CHANGELOG.md`:
```markdown
## [0.2.0] - 2026-01-02

### Added
- Identity management (create, list, show, add-channel, add-video, delete)
- Discovery with classification (discover, confirm, fetch)
- Source commands (from-channel, from-urls, from-rss)
- Quote-grounded analysis (quotes, themes, contrast, report)
- Interactive refinement (refine)

### Changed
- Default workflow is now identity-first, not search-first
- Synthesis now requires quotes as evidence

### Fixed
- Identity resolution for common names
- Keyword extraction losing signal (now uses quotes)
```

## Release Process

### Option A: GitHub Release (Recommended)

1. **Create release branch:**
   ```bash
   git checkout -b release/v0.2.0
   ```

2. **Commit version bump:**
   ```bash
   git add -A
   git commit -m "Release v0.2.0"
   ```

3. **Tag:**
   ```bash
   git tag -a v0.2.0 -m "v0.2.0 - Identity-first discovery and quote-grounded synthesis"
   ```

4. **Push:**
   ```bash
   git push origin release/v0.2.0
   git push origin v0.2.0
   ```

5. **Create GitHub Release:**
   - Go to GitHub > Releases > Draft new release
   - Select tag v0.2.0
   - Title: "v0.2.0 - Identity-First Discovery"
   - Body: Copy from CHANGELOG.md
   - Attach wheel if desired

### Option B: PyPI Release

1. **Build:**
   ```bash
   pip install build twine
   python -m build
   ```

2. **Test on TestPyPI:**
   ```bash
   twine upload --repository testpypi dist/*
   pip install -i https://test.pypi.org/simple/ worldview-extractor
   ```

3. **Upload to PyPI:**
   ```bash
   twine upload dist/*
   ```

## Post-Release

1. **Merge release branch** to main
2. **Bump version** to next dev version (e.g., `0.2.1.dev0`)
3. **Announce** if applicable

## CI/CD (Future)

Consider adding GitHub Actions for:
- Automated testing on PR
- Release on tag push
- Publish to PyPI

Example `.github/workflows/release.yml`:
```yaml
name: Release
on:
  push:
    tags: ['v*']
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install build twine
      - run: python -m build
      - run: twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```
