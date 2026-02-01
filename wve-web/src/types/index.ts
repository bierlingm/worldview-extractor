/**
 * Worldview data types
 */

export interface Belief {
  point: string;
  elaboration?: string | null;
  confidence: number;
  evidence: string[];
  sources: string[];
}

export interface Worldview {
  slug?: string;
  subject: string;
  points: Belief[];
  method?: string;
  depth?: string;
  generated_at: string;
  source_videos?: string[];
}

export interface WorldviewMetadata {
  slug: string;
  subject: string;
  generated_at: string;
  belief_count: number;
}

export interface ComparisonResult {
  worldview_a_slug: string;
  worldview_b_slug: string;
  agreements: Belief[];
  tensions: Belief[];
  unique_to_a: Belief[];
  unique_to_b: Belief[];
  similarity_score: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'concept' | 'belief';
  confidence?: number;
  [key: string]: string | number | undefined;
}

export interface GraphLink {
  source: string;
  target: string;
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}
