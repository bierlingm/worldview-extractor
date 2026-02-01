import React from 'react';
import type { Belief } from '../types';

interface BeliefCardProps {
  belief: Belief;
  index?: number;
  compact?: boolean;
}

export const BeliefCard: React.FC<BeliefCardProps> = ({
  belief,
  index,
  compact = false,
}) => {
  const confidence = belief.confidence;
  const confidencePercent = Math.round(confidence * 100);

  const getConfidenceClass = () => {
    if (confidence >= 0.7) return 'high-confidence';
    if (confidence >= 0.5) return 'medium-confidence';
    return 'low-confidence';
  };

  const getConfidenceBadgeClass = () => {
    if (confidence >= 0.7) return 'confidence-high';
    if (confidence >= 0.5) return 'confidence-medium';
    return 'confidence-low';
  };

  if (compact) {
    return (
      <div className={`belief-card ${getConfidenceClass()} mb-3`}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-800 line-clamp-2">
              {belief.point}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {belief.evidence.length} evidence items
            </p>
          </div>
          <div className={`confidence-badge ${getConfidenceBadgeClass()} flex-shrink-0`}>
            {confidencePercent}%
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`belief-card ${getConfidenceClass()} mb-4`}>
      {index !== undefined && (
        <div className="text-xs font-semibold text-gray-500 mb-2">
          Belief #{index + 1}
        </div>
      )}

      <div className="flex items-start justify-between gap-4 mb-3">
        <h3 className="text-lg font-semibold text-gray-900 flex-1">
          {belief.point}
        </h3>
        <div className={`confidence-badge ${getConfidenceBadgeClass()}`}>
          {confidencePercent}%
        </div>
      </div>

      {belief.elaboration && (
        <p className="text-gray-700 mb-3 text-sm">{belief.elaboration}</p>
      )}

      <div className="space-y-2">
        <div>
          <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">
            Evidence ({belief.evidence.length})
          </h4>
          <div className="flex flex-wrap gap-2">
            {belief.evidence.map((item, idx) => (
              <span
                key={idx}
                className="inline-block bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-xs"
              >
                {item}
              </span>
            ))}
          </div>
        </div>

        {belief.sources && belief.sources.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">
              Sources ({belief.sources.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {belief.sources.map((source, idx) => (
                <span
                  key={idx}
                  className="inline-block bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-xs border border-blue-200"
                >
                  {source}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
