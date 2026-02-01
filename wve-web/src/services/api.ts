/**
 * API service for Weave backend
 * Currently mocks data - will integrate with Rust backend later
 */

import axios from 'axios';
import type { Worldview, WorldviewMetadata, ComparisonResult, GraphData } from '../types';
import { MOCK_WORLDVIEWS } from './mockData';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3030';

const client = axios.create({
  baseURL: API_BASE,
});

export const worldviewAPI = {
  /**
   * List all available worldviews
   */
  async listWorldviews(): Promise<WorldviewMetadata[]> {
    try {
      const response = await client.get('/api/worldviews');
      return response.data;
    } catch (error) {
      // Fallback to mock data during development
      console.warn('Using mock worldview data');
      return MOCK_WORLDVIEWS.map((wv, idx) => ({
        slug: `worldview-${idx}`,
        subject: wv.subject,
        generated_at: wv.generated_at,
        belief_count: wv.points.length,
      }));
    }
  },

  /**
   * Get a specific worldview by slug
   */
  async getWorldview(slug: string): Promise<Worldview> {
    try {
      const response = await client.get(`/api/worldviews/${slug}`);
      return response.data;
    } catch (error) {
      // Mock fallback
      const idx = parseInt(slug.split('-')[1]);
      return MOCK_WORLDVIEWS[idx] || MOCK_WORLDVIEWS[0];
    }
  },

  /**
   * Compare two worldviews
   */
  async compareWorldviews(
    slugA: string,
    slugB: string
  ): Promise<ComparisonResult> {
    try {
      const response = await client.get('/api/compare', {
        params: { a: slugA, b: slugB },
      });
      return response.data;
    } catch (error) {
      // Mock comparison
      const wvA = await this.getWorldview(slugA);
      const wvB = await this.getWorldview(slugB);

      const agreements = wvA.points.filter((p) =>
        wvB.points.some((q) => p.point.includes(q.point.substring(0, 10)))
      );

      return {
        worldview_a_slug: slugA,
        worldview_b_slug: slugB,
        agreements,
        tensions: [],
        unique_to_a: wvA.points.slice(0, 1),
        unique_to_b: wvB.points.slice(0, 1),
        similarity_score: 0.65,
      };
    }
  },

  /**
   * Get graph data for a worldview
   */
  async getWorldviewGraph(slug: string): Promise<GraphData> {
    try {
      const response = await client.get(`/api/worldviews/${slug}/graph`);
      return response.data;
    } catch (error) {
      // Generate mock graph from worldview
      const worldview = await this.getWorldview(slug);
      return generateGraphFromWorldview(worldview);
    }
  },

  /**
   * Search worldviews by subject
   */
  async searchWorldviews(query: string): Promise<WorldviewMetadata[]> {
    const all = await this.listWorldviews();
    return all.filter(
      (wv) =>
        wv.subject.toLowerCase().includes(query.toLowerCase()) ||
        wv.slug.toLowerCase().includes(query.toLowerCase())
    );
  },
};

/**
 * Generate graph data from worldview beliefs
 */
function generateGraphFromWorldview(worldview: Worldview): GraphData {
  const nodes: Array<any> = [
    {
      id: `belief-root`,
      label: worldview.subject,
      type: 'belief',
    },
  ];

  const links: Array<{ source: string; target: string; weight: number }> = [];
  const concepts = new Set<string>();

  worldview.points.forEach((belief, idx) => {
    const beliefId = `belief-${idx}`;
    nodes.push({
      id: beliefId,
      label: belief.point.substring(0, 50) + '...',
      type: 'belief',
      confidence: belief.confidence,
    });

    links.push({
      source: `belief-root`,
      target: beliefId,
      weight: belief.confidence,
    });

    // Add concept nodes
    belief.evidence.slice(0, 3).forEach((evidence) => {
      const conceptId = `concept-${evidence}`;
      if (!concepts.has(evidence)) {
        concepts.add(evidence);
        nodes.push({
          id: conceptId,
          label: evidence,
          type: 'concept',
        });
      }

      links.push({
        source: beliefId,
        target: conceptId,
        weight: 0.5,
      });
    });
  });

  return { nodes, links };
}
