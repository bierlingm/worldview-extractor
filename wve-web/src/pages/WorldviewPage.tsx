import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { worldviewAPI } from '../services/api';
import type { Worldview, GraphData } from '../types';
import { BeliefCard } from '../components/BeliefCard';
import { ForceGraph } from '../components/ForceGraph';

export const WorldviewPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [worldview, setWorldview] = useState<Worldview | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'beliefs' | 'graph'>('beliefs');

  useEffect(() => {
    loadWorldview();
  }, [slug]);

  const loadWorldview = async () => {
    if (!slug) return;

    try {
      setLoading(true);
      const data = await worldviewAPI.getWorldview(slug);
      setWorldview(data);

      // Load graph data
      const graph = await worldviewAPI.getWorldviewGraph(slug);
      setGraphData(graph);

      setError(null);
    } catch (err) {
      setError('Failed to load worldview');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getConfidenceStats = () => {
    if (!worldview) return null;
    const confidences = worldview.points.map((p) => p.confidence);
    return {
      average: (confidences.reduce((a, b) => a + b, 0) / confidences.length * 100).toFixed(1),
      highest: (Math.max(...confidences) * 100).toFixed(1),
      lowest: (Math.min(...confidences) * 100).toFixed(1),
    };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="spinner"></div>
          <p className="mt-4 text-gray-600">Loading worldview...</p>
        </div>
      </div>
    );
  }

  if (error || !worldview) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <h2 className="text-red-900 font-bold mb-2">Error</h2>
            <p className="text-red-800 mb-4">{error || 'Worldview not found'}</p>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-red-100 text-red-800 rounded-lg hover:bg-red-200 transition-colors font-medium"
            >
              Back to Worldviews
            </button>
          </div>
        </div>
      </div>
    );
  }

  const stats = getConfidenceStats();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header with back button */}
        <button
          onClick={() => navigate('/')}
          className="mb-6 text-blue-500 hover:text-blue-700 font-medium text-sm"
        >
          ← Back to Worldviews
        </button>

        {/* Subject Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            {worldview.subject}
          </h1>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 uppercase font-semibold mb-1">
                Total Beliefs
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {worldview.points.length}
              </p>
            </div>

            {stats && (
              <>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs text-gray-500 uppercase font-semibold mb-1">
                    Avg Confidence
                  </p>
                  <p className="text-2xl font-bold text-blue-600">{stats.average}%</p>
                </div>

                <div className="p-3 bg-green-50 rounded-lg">
                  <p className="text-xs text-gray-500 uppercase font-semibold mb-1">
                    Highest
                  </p>
                  <p className="text-2xl font-bold text-green-600">{stats.highest}%</p>
                </div>

                <div className="p-3 bg-orange-50 rounded-lg">
                  <p className="text-xs text-gray-500 uppercase font-semibold mb-1">
                    Lowest
                  </p>
                  <p className="text-2xl font-bold text-orange-600">{stats.lowest}%</p>
                </div>
              </>
            )}
          </div>

          <p className="text-sm text-gray-600 mt-6">
            Generated on {formatDate(worldview.generated_at)}
          </p>

          {worldview.method && (
            <p className="text-xs text-gray-500 mt-1">
              Method: <span className="font-medium">{worldview.method}</span>
            </p>
          )}
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('beliefs')}
            className={`px-4 py-3 font-medium border-b-2 transition-colors ${
              activeTab === 'beliefs'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Beliefs ({worldview.points.length})
          </button>
          <button
            onClick={() => setActiveTab('graph')}
            className={`px-4 py-3 font-medium border-b-2 transition-colors ${
              activeTab === 'graph'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Concept Map
          </button>
        </div>

        {/* Content */}
        {activeTab === 'beliefs' && (
          <div className="space-y-6">
            <p className="text-gray-600 text-sm">
              Showing {worldview.points.length} core beliefs extracted from the source material.
            </p>
            {worldview.points.map((belief, idx) => (
              <BeliefCard key={idx} belief={belief} index={idx} />
            ))}
          </div>
        )}

        {activeTab === 'graph' && graphData && (
          <div className="space-y-4">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Concept Relationships
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Interactive visualization of how concepts relate to beliefs. Blue nodes are beliefs,
                green nodes are evidence concepts. Drag to reposition, scroll to zoom.
              </p>
              <ForceGraph data={graphData} height={600} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
