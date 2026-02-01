import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { worldviewAPI } from '../services/api';
import type { WorldviewMetadata } from '../types';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [worldviews, setWorldviews] = useState<WorldviewMetadata[]>([]);
  const [filteredWorldviews, setFilteredWorldviews] = useState<WorldviewMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadWorldviews();
  }, []);

  const loadWorldviews = async () => {
    try {
      setLoading(true);
      const data = await worldviewAPI.listWorldviews();
      setWorldviews(data);
      setFilteredWorldviews(data);
      setError(null);
    } catch (err) {
      setError('Failed to load worldviews');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredWorldviews(worldviews);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredWorldviews(
        worldviews.filter(
          (wv) =>
            wv.subject.toLowerCase().includes(query) ||
            wv.slug.toLowerCase().includes(query)
        )
      );
    }
  }, [searchQuery, worldviews]);

  const handleViewWorldview = (slug: string) => {
    navigate(`/worldview/${slug}`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Worldview Explorer
          </h2>
          <p className="text-gray-600">
            Browse and compare intellectual worldviews extracted from video content.
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <input
            type="text"
            placeholder="Search worldviews by name or subject..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center h-64">
            <div className="spinner"></div>
            <span className="ml-2 text-gray-600">Loading worldviews...</span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800 font-medium">Error</p>
            <p className="text-red-700 text-sm">{error}</p>
            <button
              onClick={loadWorldviews}
              className="mt-2 px-3 py-1 bg-red-100 text-red-800 rounded text-sm hover:bg-red-200 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Worldviews Grid */}
        {!loading && !error && (
          <div>
            {filteredWorldviews.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">
                  {searchQuery ? 'No worldviews match your search.' : 'No worldviews found.'}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredWorldviews.map((wv) => (
                  <div
                    key={wv.slug}
                    className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-200 overflow-hidden cursor-pointer"
                    onClick={() => handleViewWorldview(wv.slug)}
                  >
                    <div className="p-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">
                        {wv.subject}
                      </h3>
                      <p className="text-sm text-gray-600 mb-4">
                        {wv.belief_count} beliefs
                      </p>
                      <p className="text-xs text-gray-500 mb-4">
                        Generated {formatDate(wv.generated_at)}
                      </p>
                      <button className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-lg transition-colors">
                        Explore
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Results Count */}
            {filteredWorldviews.length > 0 && (
              <div className="mt-8 text-center text-gray-600 text-sm">
                Showing {filteredWorldviews.length} of {worldviews.length} worldviews
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
