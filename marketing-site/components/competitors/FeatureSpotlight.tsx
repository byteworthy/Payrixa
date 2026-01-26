'use client';

import React from 'react';
import { Check, X, Zap, Clock, Target, DollarSign } from 'lucide-react';

interface FeatureHighlight {
  title: string;
  description: string;
  upstreamValue: string;
  competitorValue: string;
  winner: 'upstream' | 'competitor';
  icon: 'speed' | 'focus' | 'pricing' | 'prevention';
}

interface FeatureSpotlightProps {
  features: FeatureHighlight[];
  upstreamName?: string;
  competitorName?: string;
}

const iconMap = {
  speed: Clock,
  focus: Target,
  pricing: DollarSign,
  prevention: Zap,
};

export default function FeatureSpotlight({
  features,
  upstreamName = 'Upstream',
  competitorName = 'Competitor',
}: FeatureSpotlightProps) {
  return (
    <div className="grid md:grid-cols-2 gap-6">
      {features.map((feature, idx) => {
        const Icon = iconMap[feature.icon];
        const isUpstreamWinner = feature.winner === 'upstream';

        return (
          <div
            key={idx}
            className={`relative rounded-lg border-2 p-6 ${
              isUpstreamWinner
                ? 'border-green-500 bg-green-50'
                : 'border-blue-500 bg-blue-50'
            }`}
          >
            <div className="absolute -top-3 right-6">
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                  isUpstreamWinner
                    ? 'bg-green-500 text-white'
                    : 'bg-blue-500 text-white'
                }`}
              >
                {isUpstreamWinner ? upstreamName : competitorName} Advantage
              </span>
            </div>

            <div className="flex items-start gap-4 mb-4">
              <div
                className={`p-3 rounded-lg ${
                  isUpstreamWinner ? 'bg-green-100' : 'bg-blue-100'
                }`}
              >
                <Icon
                  className={`h-6 w-6 ${
                    isUpstreamWinner ? 'text-green-700' : 'text-blue-700'
                  }`}
                />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">{feature.title}</h3>
                <p className="text-sm text-gray-600 mt-1">{feature.description}</p>
              </div>
            </div>

            <div className="space-y-3 mt-4">
              <div className="flex items-start gap-2">
                {isUpstreamWinner ? (
                  <Check className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                ) : (
                  <X className="h-5 w-5 text-gray-400 mt-0.5 flex-shrink-0" />
                )}
                <div>
                  <div className="font-medium text-gray-900">{upstreamName}:</div>
                  <div className="text-sm text-gray-700">{feature.upstreamValue}</div>
                </div>
              </div>

              <div className="flex items-start gap-2">
                {!isUpstreamWinner ? (
                  <Check className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                ) : (
                  <X className="h-5 w-5 text-gray-400 mt-0.5 flex-shrink-0" />
                )}
                <div>
                  <div className="font-medium text-gray-900">{competitorName}:</div>
                  <div className="text-sm text-gray-700">{feature.competitorValue}</div>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Example usage in your MDX or page:
/*
<FeatureSpotlight
  upstreamName="Upstream"
  competitorName="Adonis Intelligence"
  features={[
    {
      title: "Implementation Speed",
      description: "Time from contract to go-live",
      upstreamValue: "30 days - EHR-independent deployment",
      competitorValue: "3-6 months - requires EHR integration",
      winner: "upstream",
      icon: "speed"
    },
    {
      title: "Specialty Focus",
      description: "Vertical-specific intelligence",
      upstreamValue: "Built for dialysis, ABA, imaging, home health with specialty-specific rules",
      competitorValue: "General specialty practices - no vertical-specific intelligence",
      winner: "upstream",
      icon: "focus"
    },
    {
      title: "Pricing Transparency",
      description: "Budgeting predictability",
      upstreamValue: "Fixed monthly subscription - transparent published pricing",
      competitorValue: "Percentage of recovery - pricing not disclosed",
      winner: "upstream",
      icon: "pricing"
    },
    {
      title: "Prevention vs. Recovery",
      description: "When alerts fire",
      upstreamValue: "Early-warning alerts 2-4 weeks before denials appear",
      competitorValue: "Real-time alerts 24-48 hours after claim submission",
      winner: "upstream",
      icon: "prevention"
    }
  ]}
/>
*/
