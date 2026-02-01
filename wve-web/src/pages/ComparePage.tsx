import React, { useState, useEffect } from 'react';
import { worldviewAPI } from '../services/api';
import type { WorldviewMetadata, ComparisonResult } from '../types';
import { BeliefCard } from '../components/BeliefCard';

export const ComparePage: React.FC = () => {
  const [worldviews, setWorldviews] = useState<WorldviewMetadata[]>([]);
  const [selectedA, setSelectedA] = useState<string>('');
  const [selectedB, setSelectedB] = useState<string>('');
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWorldviews();
  }, []);

  const loadWorldviews = async () => {
    try {
      const data = await worldviewAPI.listWorldviews();
      setWorldviews(data);
      if (data.length >= 2) {
        setSelectedA(data[0].slug);
        setSelectedB(data[1].slug);
      }
    } catch (err) {
      setError('Failed to load worldviews');
      console.error(err);
    }
  };

  const handleCompare = async () => {
    if (!selectedA || !selectedB) {
      setError('Please select two worldviews to compare');
      return;
    }

    if (selectedA === selectedB) {
      setError('Please select two different worldviews');
      return;
    }

    try {
      setLoading(true);
      const result = await worldviewAPI.compareWorldviews(selectedA, selectedB);
      setComparison(result);
      setError(null);
    } catch (err) {
      setError('Failed to compare worldviews');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getWorldviewName = (slug: string) => {
    return worldviews.find((wv) => wv.slug === slug)?.subject || slug;
  };

  const getSimilarityColor = (score: number) => {
    if (score >= 0.7) return 'text-green-600';
    if (score >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Compare Worldviews
          </h2>
          <p className="text-gray-600">
            Analyze similarities and differences between two worldviews.
          </p>
        </div>

        {/* Selection Controls */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Select A */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                First Worldview
              </label>
              <select
                value={selectedA}
                onChange={(e) => setSelectedA(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select worldview...</option>
                {worldviews.map((wv) => (
                  <option key={wv.slug} value={wv.slug}>
                    {wv.subject}
                  </option>
                ))}
              </select>
            </div>

            {/* VS */}
            <div className="flex items-end justify-center pb-2">
              <span className="text-lg font-semibold text-gray-500">VS</span>
            </div>

            {/* Select B */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Second Worldview
              </label>
              <select
                value={selectedB}
                onChange={(e) => setSelectedB(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select worldview...</option>
                {worldviews.map((wv) => (
                  <option key={wv.slug} value={wv.slug}>
                    {wv.subject}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          <button
            onClick={handleCompare}
            disabled={loading || !selectedA || !selectedB}
            className="mt-6 w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="spinner"></div>
                Comparing...
              </span>
            ) : (
              'Compare'
            )}
          </button>
        </div>

        {/* Comparison Results */}
        {comparison && (
          <div className="space-y-8">
            {/* Similarity Score */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Overall Similarity
              </h3>
              <div className="flex items-center gap-4">
                <div className="text-5xl font-bold">
                  <span className={getSimilarityColor(comparison.similarity_score)}>
                    {Math.round(comparison.similarity_score * 100)}%
                  </span>
                </div>
                <div className="flex-1">
                  <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        comparison.similarity_score >= 0.7
                          ? 'bg-green-500'
                          : comparison.similarity_score >= 0.5
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${comparison.similarity_score * 100}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    {comparison.similarity_score >= 0.7
                      ? 'High similarity'
                      : comparison.similarity_score >= 0.5
                      ? 'Moderate similarity'
                      : 'Low similarity'}
                  </p>
                </div>
              </div>
            </div>

            {/* Side-by-side Comparison */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Column A */}
              <div className="comparison-column">
                <h3 className="text-xl font-bold text-gray-900 mb-4">
                  {getWorldviewName(comparison.worldview_a_slug)}
                </h3>

                {comparison.unique_to_a.length > 0 && (
                  <div className="mb-6">
                    <h4 className="font-semibold text-gray-700 mb-3 text-sm uppercase tracking-wide">
                      Unique to {getWorldviewName(comparison.worldview_a_slug).split(' ')[0]}
                      ({comparison.unique_to_a.length})
                    </h4>
                    <div className="space-y-3">
                      {comparison.unique_to_a.map((belief, idx) => (
                        <BeliefCard key={idx} belief={belief} compact />
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Column B */}
              <div className="comparison-column">
                <h3 className="text-xl font-bold text-gray-900 mb-4">
                  {getWorldviewName(comparison.worldview_b_slug)}
                </h3>

                {comparison.unique_to_b.length > 0 && (
                  <div className="mb-6">
                    <h4 className="font-semibold text-gray-700 mb-3 text-sm uppercase tracking-wide">
                      Unique to {getWorldviewName(comparison.worldview_b_slug).split(' ')[0]}
                      ({comparison.unique_to_b.length})
                    </h4>
                    <div className="space-y-3">
                      {comparison.unique_to_b.map((belief, idx) => (
                        <BeliefCard key={idx} belief={belief} compact />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Agreements */}
            {comparison.agreements.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Agreements ({comparison.agreements.length})
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Beliefs that align across both worldviews.
                </p>
                <div className="space-y-3">
                  {comparison.agreements.map((belief, idx) => (
                    <div
                      key={idx}
                      className="comparison-agreement p-4 rounded-lg"
                    >
                      <p className="font-medium text-gray-900">{belief.point}</p>
                      <p className="text-xs text-gray-600 mt-2">
                        Evidence: {belief.evidence.join(', ')}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tensions */}
            {comparison.tensions.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Tensions ({comparison.tensions.length})
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Beliefs that conflict across worldviews.
                </p>
                <div className="space-y-3">
                  {comparison.tensions.map((belief, idx) => (
                    <div
                      key={idx}
                      className="comparison-tension p-4 rounded-lg"
                    >
                      <p className="font-medium text-gray-900">{belief.point}</p>
                      <p className="text-xs text-gray-600 mt-2">
                        Evidence: {belief.evidence.join(', ')}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!comparison && !loading && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">
              Select two worldviews and click "Compare" to see the results.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
