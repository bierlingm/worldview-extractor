/**
 * Mock worldview data for development
 */

import type { Worldview } from '../types';

export const MOCK_WORLDVIEWS: Worldview[] = [
  {
    subject: 'Skinner Layne',
    points: [
      {
        point: 'Focus on job, piece, and related concepts',
        confidence: 0.5547427163718383,
        evidence: ['job', 'piece', 'game', 'work', 'action'],
        sources: [],
      },
      {
        point: 'Focus on the world, history, and related concepts',
        confidence: 0.5378009548544719,
        evidence: [
          'the world',
          'history',
          'science',
          'in the world',
          'information',
        ],
        sources: [],
      },
      {
        point: 'Focus on and we, but we, and related concepts',
        confidence: 0.5846007883454607,
        evidence: [
          'and we',
          'but we',
          'that we',
          'what we',
          'that we have',
        ],
        sources: [],
      },
      {
        point: 'Focus on is that, you re, and related concepts',
        confidence: 0.5470351399933164,
        evidence: ['is that', 'you re', 'this is', 'kind of', 'they re'],
        sources: [],
      },
      {
        point: 'Focus on want to, need to, and related concepts',
        confidence: 0.567848664812966,
        evidence: ['want to', 'need to', 'to do', 'have to', 'need'],
        sources: [],
      },
    ],
    method: 'quick',
    depth: 'quick',
    generated_at: '2026-01-02T22:34:57.465334',
    source_videos: [],
  },
  {
    subject: 'Carl Jung',
    points: [
      {
        point: 'The unconscious mind contains archetypes and universal symbols',
        confidence: 0.8234,
        evidence: [
          'unconscious',
          'archetypes',
          'symbols',
          'collective',
          'dream',
        ],
        sources: [],
      },
      {
        point:
          'Human development involves individuation and integration of shadow self',
        confidence: 0.7892,
        evidence: [
          'individuation',
          'shadow',
          'development',
          'integration',
          'self',
        ],
        sources: [],
      },
      {
        point: 'Synchronicity connects psychology with deeper meaning in life',
        confidence: 0.6123,
        evidence: ['synchronicity', 'meaning', 'connection', 'coincidence', 'fate'],
        sources: [],
      },
      {
        point: 'Personality types reveal patterns in how people engage with world',
        confidence: 0.7654,
        evidence: ['personality', 'type', 'pattern', 'preference', 'function'],
        sources: [],
      },
      {
        point: 'Spirituality and religion are necessary expressions of psyche',
        confidence: 0.6789,
        evidence: ['spirituality', 'religion', 'sacred', 'transcendent', 'meaning'],
        sources: [],
      },
    ],
    method: 'analytical',
    depth: 'deep',
    generated_at: '2026-01-01T10:15:30.000000',
    source_videos: ['jung-lecture-1', 'jung-interview-2'],
  },
  {
    subject: 'Alan Turing',
    points: [
      {
        point: 'Computation can be mechanically reduced to symbol manipulation',
        confidence: 0.9234,
        evidence: ['computation', 'machine', 'symbol', 'logic', 'algorithm'],
        sources: [],
      },
      {
        point: 'Intelligence is behavior that can be tested and verified',
        confidence: 0.8765,
        evidence: ['intelligence', 'test', 'behavior', 'measure', 'verification'],
        sources: [],
      },
      {
        point: 'Artificial machines could potentially exhibit human-like thinking',
        confidence: 0.7234,
        evidence: [
          'artificial',
          'machine',
          'thinking',
          'imitate',
          'human',
          'intelligence',
        ],
        sources: [],
      },
      {
        point: 'Morphogenesis and pattern formation follow mathematical principles',
        confidence: 0.6789,
        evidence: [
          'pattern',
          'formation',
          'mathematics',
          'chemical',
          'diffusion',
        ],
        sources: [],
      },
      {
        point: 'Logical systems and their limitations define what can be computed',
        confidence: 0.8901,
        evidence: ['logic', 'system', 'computation', 'limit', 'decidable'],
        sources: [],
      },
    ],
    method: 'theoretical',
    depth: 'deep',
    generated_at: '2025-12-20T14:22:10.000000',
    source_videos: [],
  },
];
