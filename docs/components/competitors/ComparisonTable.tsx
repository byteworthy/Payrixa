/**
 * ComparisonTable Component
 *
 * Displays side-by-side feature comparison between Upstream and competitor.
 * Responsive design with mobile-friendly collapsible categories.
 *
 * Usage:
 * ```tsx
 * import ComparisonTable from '@/components/competitors/ComparisonTable';
 * import upstreamData from '@/content/competitors/data/upstream.json';
 * import competitorData from '@/content/competitors/data/adonis-intelligence.json';
 * import comparisonFramework from '@/content/competitors/data/comparison-framework.json';
 *
 * <ComparisonTable
 *   upstream={upstreamData}
 *   competitor={competitorData}
 *   categories={comparisonFramework.comparisonCategories}
 *   highlightUpstream={true}
 * />
 * ```
 */

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Check, X, Minus } from 'lucide-react';

interface ProductData {
  company: {
    name: string;
  };
  features: Record<string, any>;
}

interface ComparisonDimension {
  id: string;
  name: string;
  description: string;
  importance: 'critical' | 'high' | 'medium' | 'low';
  upstreamAdvantage?: boolean;
  upstreamValue?: string;
  competitorComparison?: string;
}

interface ComparisonCategory {
  id: string;
  name: string;
  weight: 'high' | 'medium' | 'low';
  description: string;
  dimensions: ComparisonDimension[];
}

interface ComparisonTableProps {
  upstream: ProductData;
  competitor: ProductData;
  categories: ComparisonCategory[];
  highlightUpstream?: boolean;
}

const ComparisonTable: React.FC<ComparisonTableProps> = ({
  upstream,
  competitor,
  categories,
  highlightUpstream = true,
}) => {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(categories.map((cat) => cat.id))
  );

  const toggleCategory = (categoryId: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId);
    } else {
      newExpanded.add(categoryId);
    }
    setExpandedCategories(newExpanded);
  };

  const getRatingIcon = (rating: number) => {
    if (rating >= 4) {
      return <Check className="w-5 h-5 text-green-600" />;
    } else if (rating >= 3) {
      return <Minus className="w-5 h-5 text-yellow-600" />;
    } else {
      return <X className="w-5 h-5 text-red-600" />;
    }
  };

  const getRatingText = (rating: number) => {
    if (rating === 5) return 'Excellent';
    if (rating === 4) return 'Good';
    if (rating === 3) return 'Adequate';
    if (rating === 2) return 'Limited';
    return 'Not available';
  };

  const getFeatureData = (product: ProductData, dimensionId: string) => {
    // Navigate nested features object to find rating and description
    // This is a simplified example - adjust based on actual JSON structure
    const parts = dimensionId.split('-');
    let featureData = product.features;

    for (const part of parts) {
      if (featureData[part]) {
        featureData = featureData[part];
      }
    }

    return {
      rating: featureData.rating || 0,
      description: featureData.description || '',
      available: featureData.available !== false,
    };
  };

  return (
    <div className="comparison-table w-full overflow-hidden rounded-lg border border-gray-200 shadow-lg">
      {/* Desktop View */}
      <div className="hidden lg:block">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-50">
              <th className="w-1/3 px-6 py-4 text-left text-sm font-semibold text-gray-900">
                Feature
              </th>
              <th
                className={`w-1/3 px-6 py-4 text-center text-sm font-semibold ${
                  highlightUpstream
                    ? 'bg-blue-50 text-blue-900 border-l-4 border-blue-600'
                    : 'text-gray-900'
                }`}
              >
                {upstream.company.name}
                {highlightUpstream && (
                  <span className="block text-xs font-normal text-blue-700 mt-1">
                    Our Solution
                  </span>
                )}
              </th>
              <th className="w-1/3 px-6 py-4 text-center text-sm font-semibold text-gray-900">
                {competitor.company.name}
              </th>
            </tr>
          </thead>
          <tbody>
            {categories.map((category, catIndex) => (
              <React.Fragment key={category.id}>
                {/* Category Header */}
                <tr
                  className="bg-gray-100 hover:bg-gray-200 cursor-pointer transition-colors"
                  onClick={() => toggleCategory(category.id)}
                >
                  <td
                    colSpan={3}
                    className="px-6 py-4 text-sm font-semibold text-gray-900"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span>{category.name}</span>
                        <span
                          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                            category.weight === 'high'
                              ? 'bg-red-100 text-red-800'
                              : category.weight === 'medium'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-gray-200 text-gray-700'
                          }`}
                        >
                          {category.weight} priority
                        </span>
                      </div>
                      {expandedCategories.has(category.id) ? (
                        <ChevronUp className="w-5 h-5 text-gray-600" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-600" />
                      )}
                    </div>
                    <p className="mt-1 text-xs font-normal text-gray-600">
                      {category.description}
                    </p>
                  </td>
                </tr>

                {/* Dimension Rows */}
                {expandedCategories.has(category.id) &&
                  category.dimensions.map((dimension, dimIndex) => {
                    const upstreamFeature = getFeatureData(upstream, dimension.id);
                    const competitorFeature = getFeatureData(competitor, dimension.id);

                    return (
                      <tr
                        key={dimension.id}
                        className={`border-t border-gray-200 hover:bg-gray-50 transition-colors ${
                          dimension.upstreamAdvantage && highlightUpstream
                            ? 'bg-blue-50/30'
                            : ''
                        }`}
                      >
                        {/* Feature Name & Description */}
                        <td className="px-6 py-4 text-sm text-gray-900">
                          <div>
                            <p className="font-medium">{dimension.name}</p>
                            <p className="mt-1 text-xs text-gray-600">
                              {dimension.description}
                            </p>
                            {dimension.importance === 'critical' && (
                              <span className="inline-flex mt-2 items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
                                Critical
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Upstream Feature */}
                        <td
                          className={`px-6 py-4 text-center ${
                            highlightUpstream ? 'bg-blue-50/50' : ''
                          }`}
                        >
                          <div className="flex flex-col items-center space-y-2">
                            {getRatingIcon(upstreamFeature.rating)}
                            <span className="text-sm font-medium text-gray-900">
                              {getRatingText(upstreamFeature.rating)}
                            </span>
                            {dimension.upstreamValue && (
                              <span className="text-xs text-gray-600">
                                {dimension.upstreamValue}
                              </span>
                            )}
                            <p className="text-xs text-gray-600 max-w-xs">
                              {upstreamFeature.description}
                            </p>
                            {dimension.upstreamAdvantage && highlightUpstream && (
                              <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                                ✓ Upstream Advantage
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Competitor Feature */}
                        <td className="px-6 py-4 text-center">
                          <div className="flex flex-col items-center space-y-2">
                            {getRatingIcon(competitorFeature.rating)}
                            <span className="text-sm font-medium text-gray-900">
                              {getRatingText(competitorFeature.rating)}
                            </span>
                            {dimension.competitorComparison && (
                              <span className="text-xs text-gray-600">
                                {dimension.competitorComparison}
                              </span>
                            )}
                            <p className="text-xs text-gray-600 max-w-xs">
                              {competitorFeature.description}
                            </p>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile View */}
      <div className="lg:hidden">
        {categories.map((category) => (
          <div key={category.id} className="border-b border-gray-200">
            {/* Category Header */}
            <button
              onClick={() => toggleCategory(category.id)}
              className="w-full px-4 py-3 bg-gray-100 hover:bg-gray-200 transition-colors text-left"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">
                    {category.name}
                  </h3>
                  <p className="mt-1 text-xs text-gray-600">
                    {category.description}
                  </p>
                </div>
                {expandedCategories.has(category.id) ? (
                  <ChevronUp className="w-5 h-5 text-gray-600 flex-shrink-0 ml-2" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-600 flex-shrink-0 ml-2" />
                )}
              </div>
            </button>

            {/* Dimension Cards (Mobile) */}
            {expandedCategories.has(category.id) && (
              <div className="px-4 py-3 space-y-4">
                {category.dimensions.map((dimension) => {
                  const upstreamFeature = getFeatureData(upstream, dimension.id);
                  const competitorFeature = getFeatureData(competitor, dimension.id);

                  return (
                    <div
                      key={dimension.id}
                      className="border border-gray-200 rounded-lg p-4 space-y-3"
                    >
                      {/* Feature Name */}
                      <div>
                        <h4 className="text-sm font-semibold text-gray-900">
                          {dimension.name}
                        </h4>
                        <p className="mt-1 text-xs text-gray-600">
                          {dimension.description}
                        </p>
                      </div>

                      {/* Upstream */}
                      <div
                        className={`p-3 rounded ${
                          highlightUpstream ? 'bg-blue-50' : 'bg-gray-50'
                        }`}
                      >
                        <p className="text-xs font-semibold text-gray-900 mb-2">
                          {upstream.company.name}
                        </p>
                        <div className="flex items-center space-x-2">
                          {getRatingIcon(upstreamFeature.rating)}
                          <span className="text-sm font-medium text-gray-900">
                            {getRatingText(upstreamFeature.rating)}
                          </span>
                        </div>
                        <p className="mt-2 text-xs text-gray-600">
                          {upstreamFeature.description}
                        </p>
                        {dimension.upstreamAdvantage && (
                          <span className="inline-flex mt-2 items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                            ✓ Advantage
                          </span>
                        )}
                      </div>

                      {/* Competitor */}
                      <div className="p-3 bg-gray-50 rounded">
                        <p className="text-xs font-semibold text-gray-900 mb-2">
                          {competitor.company.name}
                        </p>
                        <div className="flex items-center space-x-2">
                          {getRatingIcon(competitorFeature.rating)}
                          <span className="text-sm font-medium text-gray-900">
                            {getRatingText(competitorFeature.rating)}
                          </span>
                        </div>
                        <p className="mt-2 text-xs text-gray-600">
                          {competitorFeature.description}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ComparisonTable;
