'use client';

import React, { useState } from 'react';
import { Check, X, Info, Calculator } from 'lucide-react';

interface PricingTier {
  name: string;
  providers?: string;
  stations?: string;
  monthlyFee: string;
  includes: string[];
}

interface Pricing {
  model: string;
  structure: string;
  transparency: string;
  tiers?: PricingTier[];
  typicalRange?: string;
  paymentTiming: string;
  notes: string[];
}

interface CompetitorData {
  company: {
    name: string;
  };
  pricing: Pricing;
}

interface PricingComparisonProps {
  upstream: CompetitorData;
  competitor: CompetitorData;
  showCalculator?: boolean;
}

export default function PricingComparison({
  upstream,
  competitor,
  showCalculator = true,
}: PricingComparisonProps) {
  const [providers, setProviders] = useState<number>(10);
  const [stations, setStations] = useState<number>(10);

  // Calculate estimated costs (simplified logic - adjust based on actual pricing models)
  const calculateUpstreamCost = () => {
    if (providers <= 5) return { monthly: 1500, annual: 18000 };
    if (providers <= 20) return { monthly: 3500, annual: 42000 };
    return { monthly: 6000, annual: 72000 }; // Large practice estimate
  };

  const calculateCompetitorCost = () => {
    // Competitor uses percentage-based model - estimate based on recovery volume
    const estimatedRecovery = providers * 20000; // $20k recovery per provider (estimate)
    const percentage = 0.125; // 12.5% of recovery (mid-range estimate)
    const monthly = Math.round((estimatedRecovery * percentage) / 12);
    const annual = Math.round(estimatedRecovery * percentage);
    return { monthly, annual };
  };

  const upstreamCost = calculateUpstreamCost();
  const competitorCost = calculateCompetitorCost();
  const savings = {
    monthly: competitorCost.monthly - upstreamCost.monthly,
    annual: competitorCost.annual - upstreamCost.annual,
    percentage: Math.round(
      ((competitorCost.annual - upstreamCost.annual) / competitorCost.annual) * 100
    ),
  };

  return (
    <div className="space-y-8">
      {/* Pricing Model Comparison */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Upstream Pricing Card */}
        <div className="relative rounded-lg border-2 border-green-500 bg-white p-6 shadow-lg">
          <div className="absolute -top-3 left-6 bg-green-500 px-3 py-1 rounded-full">
            <span className="text-xs font-semibold text-white">Transparent Pricing</span>
          </div>

          <div className="mt-2">
            <h3 className="text-xl font-bold text-gray-900">{upstream.company.name}</h3>
            <p className="mt-2 text-sm text-gray-600">{upstream.pricing.model}</p>
          </div>

          <div className="mt-6 space-y-4">
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold text-gray-900">
                ${upstreamCost.monthly.toLocaleString()}
              </span>
              <span className="text-gray-600">/month</span>
            </div>

            <div className="text-sm text-gray-600">
              <span className="font-medium">${upstreamCost.annual.toLocaleString()}</span>{' '}
              per year
            </div>

            <div className="flex items-center gap-2 text-sm">
              <Check className="h-4 w-4 text-green-600" />
              <span className="text-gray-700">Fixed monthly cost - predictable budgeting</span>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <Check className="h-4 w-4 text-green-600" />
              <span className="text-gray-700">No hidden fees or recovery percentages</span>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <Check className="h-4 w-4 text-green-600" />
              <span className="text-gray-700">Published pricing tiers</span>
            </div>
          </div>

          {/* Pricing Tiers */}
          {upstream.pricing.tiers && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-sm font-semibold text-gray-900 mb-3">Pricing Tiers:</h4>
              <div className="space-y-2 text-sm">
                {upstream.pricing.tiers.map((tier, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-gray-700">
                      {tier.name} ({tier.providers || tier.stations})
                    </span>
                    <span className="font-semibold text-gray-900">{tier.monthlyFee}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-semibold text-gray-900 mb-2">Included:</h4>
            <ul className="space-y-1 text-sm text-gray-600">
              {upstream.pricing.notes.map((note, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <Check className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>{note}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Competitor Pricing Card */}
        <div className="rounded-lg border-2 border-gray-300 bg-white p-6 shadow-sm">
          <div className="mt-2">
            <h3 className="text-xl font-bold text-gray-900">{competitor.company.name}</h3>
            <p className="mt-2 text-sm text-gray-600">{competitor.pricing.model}</p>
          </div>

          <div className="mt-6 space-y-4">
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold text-gray-900">
                ~${competitorCost.monthly.toLocaleString()}
              </span>
              <span className="text-gray-600">/month</span>
            </div>

            <div className="text-sm text-gray-600">
              <span className="font-medium">
                ~${competitorCost.annual.toLocaleString()}
              </span>{' '}
              per year (estimated)
            </div>

            <div className="flex items-center gap-2 text-sm">
              <X className="h-4 w-4 text-gray-400" />
              <span className="text-gray-600">
                Variable cost based on denial recovery
              </span>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <X className="h-4 w-4 text-gray-400" />
              <span className="text-gray-600">Pricing not publicly disclosed</span>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <X className="h-4 w-4 text-gray-400" />
              <span className="text-gray-600">Unpredictable monthly costs</span>
            </div>
          </div>

          {/* Transparency Warning */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex items-start gap-2 p-3 bg-yellow-50 rounded-lg">
              <Info className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-yellow-800">
                <p className="font-medium">Low Pricing Transparency</p>
                <p className="mt-1">
                  {competitor.pricing.structure} Costs vary month-to-month, making
                  budgeting difficult.
                </p>
              </div>
            </div>
          </div>

          {/* Notes */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-semibold text-gray-900 mb-2">
              Considerations:
            </h4>
            <ul className="space-y-1 text-sm text-gray-600">
              {competitor.pricing.notes.map((note, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-gray-400">•</span>
                  <span>{note}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Savings Calculator */}
      {showCalculator && savings.annual > 0 && (
        <div className="rounded-lg border-2 border-green-500 bg-green-50 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Calculator className="h-6 w-6 text-green-700" />
            <h3 className="text-lg font-bold text-green-900">
              Estimated Annual Savings with Upstream
            </h3>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg p-4 text-center">
              <div className="text-sm font-medium text-gray-600 mb-1">Monthly Savings</div>
              <div className="text-2xl font-bold text-green-700">
                ${savings.monthly.toLocaleString()}
              </div>
            </div>

            <div className="bg-white rounded-lg p-4 text-center">
              <div className="text-sm font-medium text-gray-600 mb-1">Annual Savings</div>
              <div className="text-2xl font-bold text-green-700">
                ${savings.annual.toLocaleString()}
              </div>
            </div>

            <div className="bg-white rounded-lg p-4 text-center">
              <div className="text-sm font-medium text-gray-600 mb-1">Cost Reduction</div>
              <div className="text-2xl font-bold text-green-700">
                {savings.percentage}%
              </div>
            </div>
          </div>

          <div className="mt-4 text-sm text-green-800">
            <p className="flex items-start gap-2">
              <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>
                Calculations based on {providers} providers. Actual savings depend on
                practice size, denial volume, and recovery rates. {competitor.company.name}'s
                percentage-based model means higher denial rates result in higher costs.
              </span>
            </p>
          </div>
        </div>
      )}

      {/* Interactive Calculator */}
      {showCalculator && (
        <div className="rounded-lg border border-gray-300 bg-white p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">
            Calculate Your Estimated Costs
          </h3>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label
                htmlFor="providers"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Number of Providers (or BCBAs)
              </label>
              <input
                type="range"
                id="providers"
                min="1"
                max="50"
                value={providers}
                onChange={(e) => setProviders(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-sm text-gray-600 mt-1">
                <span>1</span>
                <span className="font-semibold text-gray-900">{providers}</span>
                <span>50+</span>
              </div>
            </div>

            <div>
              <label
                htmlFor="stations"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Dialysis Stations (if applicable)
              </label>
              <input
                type="range"
                id="stations"
                min="0"
                max="50"
                value={stations}
                onChange={(e) => setStations(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-sm text-gray-600 mt-1">
                <span>0</span>
                <span className="font-semibold text-gray-900">{stations}</span>
                <span>50+</span>
              </div>
            </div>
          </div>

          <div className="mt-6 text-sm text-gray-600">
            <p>
              Based on {providers} providers, your estimated costs would be:
            </p>
            <ul className="mt-2 space-y-1">
              <li>
                <span className="font-medium text-green-700">Upstream:</span> $
                {upstreamCost.annual.toLocaleString()}/year (fixed)
              </li>
              <li>
                <span className="font-medium text-blue-700">
                  {competitor.company.name}:
                </span>{' '}
                ~${competitorCost.annual.toLocaleString()}/year (variable estimate)
              </li>
            </ul>
          </div>
        </div>
      )}

      {/* Total Cost of Ownership */}
      <div className="rounded-lg border border-gray-300 bg-gray-50 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">
          Total Cost of Ownership Comparison
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-300">
                <th className="text-left py-2 font-semibold text-gray-900">Cost Factor</th>
                <th className="text-left py-2 font-semibold text-gray-900">
                  {upstream.company.name}
                </th>
                <th className="text-left py-2 font-semibold text-gray-900">
                  {competitor.company.name}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="py-3 text-gray-700">Monthly Subscription/Fees</td>
                <td className="py-3">${upstreamCost.monthly.toLocaleString()} (fixed)</td>
                <td className="py-3">
                  ~${competitorCost.monthly.toLocaleString()} (variable)
                </td>
              </tr>
              <tr>
                <td className="py-3 text-gray-700">Implementation Costs</td>
                <td className="py-3">Included in subscription</td>
                <td className="py-3">May apply (EHR integration)</td>
              </tr>
              <tr>
                <td className="py-3 text-gray-700">EHR Vendor Fees</td>
                <td className="py-3">None (EHR-independent)</td>
                <td className="py-3">Possible (EHR coordination)</td>
              </tr>
              <tr>
                <td className="py-3 text-gray-700">Training & Onboarding</td>
                <td className="py-3">1 day (included)</td>
                <td className="py-3">2-3 days (included)</td>
              </tr>
              <tr>
                <td className="py-3 text-gray-700">Time to Value</td>
                <td className="py-3">30 days</td>
                <td className="py-3">3-6 months</td>
              </tr>
              <tr className="font-semibold bg-gray-100">
                <td className="py-3 text-gray-900">First Year Total</td>
                <td className="py-3 text-green-700">
                  ${upstreamCost.annual.toLocaleString()}
                </td>
                <td className="py-3 text-blue-700">
                  ~${competitorCost.annual.toLocaleString()}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="mt-4 text-sm text-gray-600">
          <p className="flex items-start gap-2">
            <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <span>
              {upstream.company.name}'s fixed pricing enables predictable annual budgeting.{' '}
              {competitor.company.name}'s percentage-based model means costs fluctuate with
              denial volume, making CFO approval and budget planning more challenging.
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}
