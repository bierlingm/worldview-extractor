# Weave Web UI

A modern React + TypeScript web dashboard for exploring and comparing intellectual worldviews extracted from video content.

## Features

- **Worldview Browser**: Browse all stored worldviews with search filtering
- **Interactive Inspector**: View detailed beliefs with confidence scores, evidence, and sources
- **Concept Map**: Force-directed graph visualization showing relationships between beliefs and evidence concepts
- **Comparison Tool**: Side-by-side comparison of two worldviews with agreements, tensions, and unique beliefs highlighted

## Technology Stack

- **Frontend Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Visualization**: D3.js v7 (force-directed graphs)
- **HTTP Client**: Axios
- **Routing**: React Router v6

## Prerequisites

- Node.js 18+
- npm 9+

## Installation

1. Install dependencies:
```bash
npm install
```

2. Configure API endpoint (optional):
   - Copy `.env.example` to `.env`
   - Update `VITE_API_BASE` if your backend runs on a different port:
   ```
   VITE_API_BASE=http://localhost:3030
   ```

## Development

Run the development server with hot module replacement:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Building for Production

Create an optimized production build:

```bash
npm run build
```

Output will be in the `dist/` directory.

Preview the production build locally:

```bash
npm run preview
```

## Project Structure

```
src/
├── components/
│   ├── Header.tsx           # Navigation header with route links
│   ├── BeliefCard.tsx       # Reusable belief display component
│   └── ForceGraph.tsx       # D3.js force-directed graph
├── pages/
│   ├── HomePage.tsx         # Worldview listing with search
│   ├── WorldviewPage.tsx    # Single worldview inspector
│   └── ComparePage.tsx      # Comparison tool
├── services/
│   ├── api.ts              # API client with mock fallbacks
│   └── mockData.ts         # Sample worldviews for development
├── types/
│   └── index.ts            # TypeScript interfaces
├── App.tsx                 # Main app with routing
├── main.tsx                # React entry point
└── index.css               # Global styles (Tailwind + custom CSS)
```

## API Integration

The frontend currently uses mock data for development. To integrate with the Rust backend:

1. Ensure your Rust backend is serving on `http://localhost:3030` (configurable via `.env`)
2. Implement these endpoints:

### Endpoints

- `GET /api/worldviews` - List all worldviews
- `GET /api/worldviews/:slug` - Get a specific worldview
- `GET /api/worldviews/:slug/graph` - Get graph data for worldview
- `GET /api/compare?a=:slug&b=:slug` - Compare two worldviews

See `src/services/api.ts` for the interface contracts.

## Data Schema

### Worldview JSON

```json
{
  "subject": "Subject Name",
  "points": [
    {
      "point": "Main belief statement",
      "elaboration": "Optional details",
      "confidence": 0.75,
      "evidence": ["keyword1", "keyword2", ...],
      "sources": ["source1", ...]
    }
  ],
  "method": "quick",
  "depth": "quick",
  "generated_at": "2026-01-02T22:34:57.465334",
  "source_videos": []
}
```

## Component Overview

### Header
Navigation between main views (Worldviews, Compare). Sticky positioning for easy access.

### BeliefCard
Displays a single belief with:
- Confidence percentage badge (color-coded)
- Evidence tags (concepts mentioned in source material)
- Source citations
- Hover effects for better UX

### ForceGraph
Interactive D3.js visualization:
- Blue nodes = beliefs
- Green nodes = evidence concepts
- Edge weight = confidence level
- Draggable nodes with physics simulation
- Mouse wheel to zoom
- Smooth animations

### HomePage
- Grid layout of worldviews
- Search/filter by subject name
- Click to navigate to full worldview view
- Loading and error states

### WorldviewPage
- Subject metadata and statistics
- Tabbed interface (Beliefs / Concept Map)
- Full belief details with evidence
- Interactive force graph

### ComparePage
- Select two worldviews to compare
- Similarity score with visual progress bar
- Side-by-side unique beliefs display
- Agreements and tensions sections

## Styling

The app uses a combination of:
- **Tailwind CSS**: Responsive utility-first framework
- **Custom CSS**: Graph styling, animations, custom layouts
- **CSS Variables**: Could be added for theming

All components use semantic HTML and follow accessibility best practices.

## Development Notes

### TypeScript Configuration
- `verbatimModuleSyntax` enabled for strict module imports
- React JSX handling via Vite's automatic import
- D3.js types included via `@types/d3`

### Common Issues
- **D3 type errors**: Use `as any` when TypeScript conflicts with D3 v7's complex generics
- **Tailwind in CSS**: Use standard CSS instead of `@apply` directives for complex styles
- **PostCSS**: Using `@tailwindcss/postcss` for v4 compatibility

### Mock Data
Three pre-configured worldviews are available in `src/services/mockData.ts`:
- Skinner Layne
- Carl Jung
- Alan Turing

Remove the mock fallbacks in `api.ts` once backend is ready.

## Future Enhancements

- [ ] Export worldviews as JSON/PDF
- [ ] Timeline view showing worldview evolution
- [ ] Filtering by confidence levels or evidence keywords
- [ ] Custom color themes
- [ ] Dark mode
- [ ] Network analysis metrics (centrality, clustering)
- [ ] Belief similarity scoring
- [ ] Source material transcript integration
- [ ] Collaborative annotations

## License

Part of the Weave project.
