# Quick Start Guide

Get the Weave Web UI up and running in minutes.

## 1. Install Dependencies

```bash
npm install
```

## 2. Start Development Server

```bash
npm run dev
```

Open your browser to http://localhost:5173

The app loads with mock worldviews:
- Skinner Layne
- Carl Jung
- Alan Turing

## 3. Explore Features

### Homepage
- Browse worldviews in a card grid
- Search by subject name
- Click any card to view full worldview

### Worldview Inspector
- View all beliefs for a subject
- See confidence scores (color-coded badges)
- View evidence keywords
- **Concept Map tab**: Interactive force-directed graph showing belief-concept relationships
  - Drag nodes to explore
  - Scroll to zoom
  - Blue = beliefs, Green = evidence concepts

### Comparison Tool
- Select two different worldviews
- Get similarity score with visual progress bar
- View agreements and tensions between worldviews
- See beliefs unique to each

## 4. Build for Production

```bash
npm run build
```

Output in `dist/` directory ready for deployment.

## 5. Connect to Rust Backend (Optional)

Currently, the frontend uses mock data. To connect to your Rust backend:

1. Ensure backend runs on http://localhost:3030
2. Update `.env` file:
   ```
   VITE_API_BASE=http://localhost:3030
   ```
3. Implement these endpoints in your backend:
   - `GET /api/worldviews` - List all worldviews
   - `GET /api/worldviews/:slug` - Get specific worldview
   - `GET /api/worldviews/:slug/graph` - Graph data
   - `GET /api/compare?a=:slug&b=:slug` - Compare two

See `SERVER.md` for full backend implementation guide.

## Project Layout

```
wve-web/
├── src/                  # React components and logic
├── dist/                 # Built static files (production)
├── public/               # Static assets
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript config
├── vite.config.ts        # Vite build config
├── README.md             # Full documentation
├── SERVER.md             # Backend integration guide
└── QUICKSTART.md         # This file
```

## Available Scripts

- `npm run dev` - Start development server with HMR
- `npm run build` - Create production build
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint (if configured)

## Troubleshooting

**Build fails with TypeScript errors:**
- Run `npm install` again to ensure all dependencies installed
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`

**Port 5173 already in use:**
- Change dev port: `npm run dev -- --port 3000`

**Mock data not appearing:**
- Check browser console for errors (F12)
- Verify `src/services/mockData.ts` is present

**Graph visualization not showing:**
- Ensure D3.js is installed: `npm list d3`
- Check browser console for rendering errors

## Performance Tips

- Development builds are not optimized; use `npm run build` to see production performance
- Graph visualization smoothness depends on number of beliefs (optimized for <50 beliefs per worldview)
- Mobile responsiveness works but graph is best on larger screens

## Next Steps

1. Read `README.md` for complete feature documentation
2. Check `SERVER.md` to integrate with Rust backend
3. Explore `src/services/api.ts` to understand data flow
4. Customize styles in `src/index.css`
5. Add new pages by creating files in `src/pages/`

## Questions?

Check the inline comments in source files for detailed explanations of components and utilities.
