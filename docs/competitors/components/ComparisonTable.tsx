'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Check, X, Info } from 'lucide-react';

// Import types from your data structure
interface FeatureRating {
  rating: number;
  description: string;
  details?: string[];
}

interface CompetitorFeatures {
  [key: string]: FeatureRating;
}

interface CompetitorData {
  company: {
    name: string;
  };
  features: CompetitorFeatures;
}

interface ComparisonCategory {
  id: string;
  name: string;
  weight: string;
  description: string;
  dimensions: {
    id: string;
    name: string;
    description: string;
    importance: string;
    upstreamAdvantage?: boolean | null;
    upstreamValue?: string;
    competitorComparison?: string;
    note?: string;
  }[];
}

interface ComparisonTableProps {
  upstream: CompetitorData;
  competitor: CompetitorData;
  categories: ComparisonCategory[];
  highlightUpstream?: boolean;
}

export default function ComparisonTable({
  upstream,
  competitor,
  categories,
  highlightUpstream = true,
}: ComparisonTableProps) {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(categories.map((c) => c.id))
  );

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(categoryId)) {
        next.delete(categoryId);
      } else {
        next.add(categoryId);
      }
      return next;
    });
  };

  const getRatingDisplay = (rating: number) => {
    const stars = '⭐'.repeat(rating);
    return (
      <span className="flex items-center gap-1">
        <span>{stars}</span>
        <span className="text-sm text-gray-600">({rating}/5)</span>
      </span>
    );
  };

  const getWinnerBadge = (upstreamAdvantage?: boolean | null) => {
    if (upstreamAdvantage === true) {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
          Upstream
        </span>
      );
    } else if (upstreamAdvantage === false) {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {competitor.company.name}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        Similar
      </span>
    );
  };

  return (
    <div className="w-full overflow-hidden rounded-lg border border-gray-200 shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full divide-y divide-gray-200">
          {/* Table Header */}
          <thead className="bg-gray-50">
            <tr>
              <th
                scope="col"
                className="px-6 py-4 text-left text-sm font-semibold text-gray-900"
              >
                Feature
              </th>
              <th
                scope="col"
                className={`px-6 py-4 text-left text-sm font-semibold ${
                  highlightUpstream ? 'bg-green-50 text-green-900' : 'text-gray-900'
                }`}
              >
                Upstream
              </th>
              <th
                scope="col"
                className="px-6 py-4 text-left text-sm font-semibold text-gray-900"
              >
                {competitor.company.name}
              </th>
              <th
                scope="col"
                className="px-6 py-4 text-left text-sm font-semibold text-gray-900"
              >
                Winner
              </th>
            </tr>
          </thead>

          {/* Table Body */}
          <tbody className="divide-y divide-gray-200 bg-white">
            {categories.map((category) => (
              <React.Fragment key={category.id}>
                {/* Category Header Row */}
                <tr className="bg-gray-50 hover:bg-gray-100 cursor-pointer">
                  <td
                    colSpan={4}
                    onClick={() => toggleCategory(category.id)}
                    className="px-6 py-4"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {expandedCategories.has(category.id) ? (
                          <ChevronUp className="h-5 w-5 text-gray-500" />
                        ) : (
                          <ChevronDown className="h-5 w-5 text-gray-500" />
                        )}
                        <div>
                          <h3 className="text-base font-semibold text-gray-900">
                            {category.name}
                          </h3>
                          <p className="text-sm text-gray-600">{category.description}</p>
                        </div>
                      </div>
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-200 text-gray-800">
                        {category.weight} priority
                      </span>
                    </div>
                  </td>
                </tr>

                {/* Dimension Rows */}
                {expandedCategories.has(category.id) &&
                  category.dimensions.map((dimension) => (
                    <tr
                      key={dimension.id}
                      className={`hover:bg-gray-50 ${
                        highlightUpstream && dimension.upstreamAdvantage
                          ? 'bg-green-50'
                          : ''
                      }`}
                    >
                      {/* Feature Name */}
                      <td className="px-6 py-4">
                        <div className="flex items-start gap-2">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {dimension.name}
                            </div>
                            <div className="text-sm text-gray-600">
                              {dimension.description}
                            </div>
                            {dimension.importance === 'critical' && (
                              <span className="mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                                Critical
                              </span>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Upstream Value */}
                      <td
                        className={`px-6 py-4 ${
                          highlightUpstream && dimension.upstreamAdvantage
                            ? 'bg-green-50'
                            : ''
                        }`}
                      >
                        <div className="text-sm text-gray-900">
                          {dimension.upstreamValue || '—'}
                        </div>
                      </td>

                      {/* Competitor Value */}
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">
                          {dimension.competitorComparison || '—'}
                        </div>
                      </td>

                      {/* Winner Badge */}
                      <td className="px-6 py-4">
                        {getWinnerBadge(dimension.upstreamAdvantage)}
                      </td>
                    </tr>
                  ))}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile-Friendly Alternative View */}
      <div className="block lg:hidden divide-y divide-gray-200">
        {categories.map((category) => (
          <div key={category.id} className="p-4">
            <button
              onClick={() => toggleCategory(category.id)}
              className="w-full flex items-center justify-between text-left"
            >
              <div className="flex items-center gap-2">
                {expandedCategories.has(category.id) ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
                <h3 className="font-semibold">{category.name}</h3>
              </div>
              <span className="text-xs px-2 py-1 bg-gray-200 rounded-full">
                {category.weight}
              </span>
            </button>

            {expandedCategories.has(category.id) && (
              <div className="mt-4 space-y-4">
                {category.dimensions.map((dimension) => (
                  <div key={dimension.id} className="border-l-4 border-gray-200 pl-3">
                    <h4 className="font-medium text-sm mb-2">{dimension.name}</h4>
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="font-medium text-green-700">Upstream:</span>{' '}
                        {dimension.upstreamValue || '—'}
                      </div>
                      <div>
                        <span className="font-medium text-blue-700">
                          {competitor.company.name}:
                        </span>{' '}
                        {dimension.competitorComparison || '—'}
                      </div>
                      <div>{getWinnerBadge(dimension.upstreamAdvantage)}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="border-t border-gray-200 bg-gray-50 px-6 py-4">
        <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 bg-green-100 rounded"></span>
            <span>Upstream Advantage</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 bg-blue-100 rounded"></span>
            <span>Competitor Advantage</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 bg-gray-100 rounded"></span>
            <span>Similar Capability</span>
          </div>
        </div>
      </div>
    </div>
  );
}
