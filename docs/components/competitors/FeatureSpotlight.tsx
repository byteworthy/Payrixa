/**
 * FeatureSpotlight Component
 *
 * Highlights specific differentiating features with visual emphasis.
 * Acknowledges competitor strengths fairly while emphasizing Upstream advantages.
 *
 * Usage:
 * ```tsx
 * import FeatureSpotlight from '@/components/competitors/FeatureSpotlight';
 *
 * <FeatureSpotlight
 *   feature="earlyWarningDetection"
 *   upstreamAdvantage={true}
 *   title="Early-Warning Behavioral Drift Detection"
 *   description="Detects payer changes 2-4 weeks before denials appear"
 *   upstreamDetails={{...}}
 *   competitorDetails={{...}}
 * />
 * ```
 */

import React from 'react';
import { Check, X, AlertTriangle, TrendingUp, Clock, Target } from 'lucide-react';

interface FeatureDetails {
  companyName: string;
  rating: number;
  description: string;
  examples?: string[];
  limitations?: string[];
}

interface FeatureSpotlightProps {
  feature: string;
  upstreamAdvantage: boolean;
  title: string;
  description: string;
  icon?: React.ReactNode;
  upstreamDetails: FeatureDetails;
  competitorDetails: FeatureDetails;
  caseStudy?: {
    title: string;
    result: string;
    quote?: string;
  };
}

const FeatureSpotlight: React.FC<FeatureSpotlightProps> = ({
  feature,
  upstreamAdvantage,
  title,
  description,
  icon,
  upstreamDetails,
  competitorDetails,
  caseStudy,
}) => {
  const getIcon = () => {
    if (icon) return icon;
    // Default icons based on feature type
    if (feature.includes('early') || feature.includes('warning'))
      return <AlertTriangle className="w-8 h-8" />;
    if (feature.includes('specialty') || feature.includes('specific'))
      return <Target className="w-8 h-8" />;
    if (feature.includes('implementation') || feature.includes('speed'))
      return <Clock className="w-8 h-8" />;
    return <TrendingUp className="w-8 h-8" />;
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 4) return 'text-green-600';
    if (rating >= 3) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRatingIcon = (rating: number) => {
    if (rating >= 4) return <Check className="w-5 h-5" />;
    if (rating >= 3) return <AlertTriangle className="w-5 h-5" />;
    return <X className="w-5 h-5" />;
  };

  return (
    <div className="feature-spotlight w-full">
      {/* Header */}
      <div
        className={`p-6 rounded-t-lg ${
          upstreamAdvantage
            ? 'bg-gradient-to-r from-blue-600 to-indigo-600'
            : 'bg-gradient-to-r from-gray-700 to-gray-900'
        } text-white`}
      >
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">{getIcon()}</div>
          <div>
            <h3 className="text-2xl font-bold">{title}</h3>
            <p className="mt-2 text-blue-100">{description}</p>
            {upstreamAdvantage && (
              <div className="mt-3 inline-flex items-center px-3 py-1 rounded-full bg-white/20 backdrop-blur-sm">
                <Check className="w-4 h-4 mr-2" />
                <span className="text-sm font-semibold">Upstream Advantage</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Comparison Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
        {/* Upstream Details */}
        <div
          className={`p-6 border-t-4 ${
            upstreamAdvantage
              ? 'border-blue-600 bg-blue-50'
              : 'bg-gray-50 border-gray-300'
          }`}
        >
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-bold text-gray-900">
              {upstreamDetails.companyName}
            </h4>
            <div
              className={`flex items-center space-x-2 ${getRatingColor(
                upstreamDetails.rating
              )}`}
            >
              {getRatingIcon(upstreamDetails.rating)}
              <span className="text-sm font-semibold">
                {upstreamDetails.rating}/5
              </span>
            </div>
          </div>

          <p className="text-sm text-gray-700 mb-4">
            {upstreamDetails.description}
          </p>

          {/* Examples */}
          {upstreamDetails.examples && upstreamDetails.examples.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-semibold text-gray-900 mb-2">Examples:</p>
              <ul className="space-y-2">
                {upstreamDetails.examples.map((example, index) => (
                  <li
                    key={index}
                    className="text-sm text-gray-700 flex items-start"
                  >
                    <Check className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                    <span>{example}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Limitations (honest) */}
          {upstreamDetails.limitations &&
            upstreamDetails.limitations.length > 0 && (
              <div className="pt-3 border-t border-blue-200">
                <p className="text-xs font-semibold text-gray-900 mb-2">
                  Limitations:
                </p>
                <ul className="space-y-1">
                  {upstreamDetails.limitations.map((limitation, index) => (
                    <li
                      key={index}
                      className="text-xs text-gray-600 flex items-start"
                    >
                      <AlertTriangle className="w-3 h-3 text-yellow-600 mr-2 flex-shrink-0 mt-0.5" />
                      <span>{limitation}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
        </div>

        {/* Competitor Details */}
        <div className="p-6 bg-white border-l border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-bold text-gray-900">
              {competitorDetails.companyName}
            </h4>
            <div
              className={`flex items-center space-x-2 ${getRatingColor(
                competitorDetails.rating
              )}`}
            >
              {getRatingIcon(competitorDetails.rating)}
              <span className="text-sm font-semibold">
                {competitorDetails.rating}/5
              </span>
            </div>
          </div>

          <p className="text-sm text-gray-700 mb-4">
            {competitorDetails.description}
          </p>

          {/* Examples */}
          {competitorDetails.examples && competitorDetails.examples.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-semibold text-gray-900 mb-2">Examples:</p>
              <ul className="space-y-2">
                {competitorDetails.examples.map((example, index) => (
                  <li
                    key={index}
                    className="text-sm text-gray-700 flex items-start"
                  >
                    <Check className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                    <span>{example}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Limitations */}
          {competitorDetails.limitations &&
            competitorDetails.limitations.length > 0 && (
              <div className="pt-3 border-t border-gray-200">
                <p className="text-xs font-semibold text-gray-900 mb-2">
                  Limitations:
                </p>
                <ul className="space-y-1">
                  {competitorDetails.limitations.map((limitation, index) => (
                    <li
                      key={index}
                      className="text-xs text-gray-600 flex items-start"
                    >
                      <AlertTriangle className="w-3 h-3 text-yellow-600 mr-2 flex-shrink-0 mt-0.5" />
                      <span>{limitation}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
        </div>
      </div>

      {/* Case Study (if provided) */}
      {caseStudy && (
        <div className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 border-t-4 border-green-600 rounded-b-lg">
          <div className="flex items-start space-x-3">
            <TrendingUp className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
            <div>
              <p className="text-sm font-semibold text-gray-900 mb-1">
                Real-World Impact
              </p>
              <p className="text-sm font-bold text-green-900 mb-2">
                {caseStudy.title}
              </p>
              <p className="text-sm text-gray-700 mb-3">{caseStudy.result}</p>
              {caseStudy.quote && (
                <blockquote className="border-l-4 border-green-600 pl-4 py-2 bg-white/50 rounded">
                  <p className="text-sm italic text-gray-700">
                    "{caseStudy.quote}"
                  </p>
                </blockquote>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FeatureSpotlight;
