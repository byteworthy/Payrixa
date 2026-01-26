/**
 * PricingComparison Component
 *
 * Side-by-side pricing comparison with interactive calculator.
 * Highlights transparent pricing advantage and total cost scenarios.
 *
 * Usage:
 * ```tsx
 * import PricingComparison from '@/components/competitors/PricingComparison';
 *
 * <PricingComparison
 *   upstream={upstreamData}
 *   competitor={competitorData}
 *   showCalculator={true}
 * />
 * ```
 */

import React, { useState } from 'react';
import { DollarSign, TrendingDown, AlertCircle, Calculator } from 'lucide-react';

interface PricingTier {
  name: string;
  providers?: string;
  stations?: string;
  monthlyFee: string;
  includes: string[];
}

interface ProductData {
  company: {
    name: string;
  };
  pricing: {
    model: string;
    structure: string;
    transparency: string;
    tiers?: PricingTier[];
    notes?: string[];
  };
}

interface PricingComparisonProps {
  upstream: ProductData;
  competitor: ProductData;
  showCalculator?: boolean;
}

const PricingComparison: React.FC<PricingComparisonProps> = ({
  upstream,
  competitor,
  showCalculator = true,
}) => {
  const [practiceSize, setPracticeSize] = useState<'small' | 'medium' | 'large'>('medium');
  const [monthlyClaimsVolume, setMonthlyClaimsVolume] = useState<number>(500000);
  const [denialRate, setDenialRate] = useState<number>(11.8);

  // Calculate estimated costs
  const calculateUpstreamCost = () => {
    if (practiceSize === 'small') return 1500;
    if (practiceSize === 'medium') return 3500;
    return 6000; // large (average of 5000-7000)
  };

  const calculateCompetitorCost = () => {
    const monthlyDenials = monthlyClaimsVolume * (denialRate / 100);
    const recoveryRate = 0.6; // Assume 60% recovery
    const monthlyRecovery = monthlyDenials * recoveryRate;
    const percentage = 0.125; // Assume 12.5% of recovery (mid-range of 10-15%)
    return monthlyRecovery * percentage;
  };

  const upstreamMonthlyCost = calculateUpstreamCost();
  const competitorMonthlyCost = calculateCompetitorCost();
  const upstreamAnnualCost = upstreamMonthlyCost * 12;
  const competitorAnnualCost = competitorMonthlyCost * 12;
  const annualSavings = competitorAnnualCost - upstreamAnnualCost;
  const savingsPercentage = (annualSavings / competitorAnnualCost) * 100;

  return (
    <div className="pricing-comparison w-full space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900">Pricing Comparison</h2>
        <p className="mt-2 text-lg text-gray-600">
          Transparent fixed pricing vs. variable percentage-based fees
        </p>
      </div>

      {/* Pricing Cards (Side-by-Side) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upstream Pricing Card */}
        <div className="relative bg-white border-2 border-blue-600 rounded-lg shadow-lg overflow-hidden">
          <div className="absolute top-0 right-0 bg-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-bl-lg">
            Recommended
          </div>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">
                {upstream.company.name}
              </h3>
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>

            <div className="mb-4">
              <p className="text-sm font-semibold text-gray-700">Pricing Model</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {upstream.pricing.model}
              </p>
              <div className="flex items-center mt-2 space-x-2">
                <div className="flex-shrink-0 w-3 h-3 rounded-full bg-green-500"></div>
                <span className="text-sm text-gray-600">
                  {upstream.pricing.transparency} transparency
                </span>
              </div>
            </div>

            {/* Pricing Tiers */}
            <div className="space-y-3 mb-6">
              {upstream.pricing.tiers?.map((tier, index) => (
                <div
                  key={index}
                  className="p-3 bg-blue-50 rounded-lg border border-blue-200"
                >
                  <p className="text-sm font-semibold text-gray-900">{tier.name}</p>
                  <p className="text-xs text-gray-600 mt-1">
                    {tier.providers || tier.stations}
                  </p>
                  <p className="text-lg font-bold text-blue-900 mt-2">
                    {tier.monthlyFee}/month
                  </p>
                  <ul className="mt-2 space-y-1">
                    {tier.includes.slice(0, 3).map((item, idx) => (
                      <li key={idx} className="text-xs text-gray-600 flex items-start">
                        <span className="text-green-600 mr-1">✓</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            {/* Key Advantages */}
            <div className="border-t border-gray-200 pt-4">
              <p className="text-sm font-semibold text-gray-900 mb-2">
                Key Advantages
              </p>
              <ul className="space-y-2">
                {upstream.pricing.notes?.map((note, index) => (
                  <li key={index} className="text-xs text-gray-600 flex items-start">
                    <TrendingDown className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Competitor Pricing Card */}
        <div className="bg-white border border-gray-300 rounded-lg shadow-lg overflow-hidden">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">
                {competitor.company.name}
              </h3>
              <AlertCircle className="w-6 h-6 text-yellow-600" />
            </div>

            <div className="mb-4">
              <p className="text-sm font-semibold text-gray-700">Pricing Model</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {competitor.pricing.model}
              </p>
              <div className="flex items-center mt-2 space-x-2">
                <div className="flex-shrink-0 w-3 h-3 rounded-full bg-yellow-500"></div>
                <span className="text-sm text-gray-600">
                  {competitor.pricing.transparency} transparency
                </span>
              </div>
            </div>

            {/* Pricing Structure */}
            <div className="mb-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <p className="text-sm font-semibold text-gray-900 mb-2">
                {competitor.pricing.structure}
              </p>
              <p className="text-xs text-gray-600">
                Typical range: {competitor.pricing.model}
              </p>
              <div className="mt-3 p-3 bg-white rounded border border-yellow-300">
                <p className="text-xs text-gray-700 font-medium">
                  ⚠️ Variable Monthly Costs
                </p>
                <p className="text-xs text-gray-600 mt-1">
                  Costs fluctuate based on denial volume and recovery performance.
                  Difficult to budget accurately.
                </p>
              </div>
            </div>

            {/* Key Considerations */}
            <div className="border-t border-gray-200 pt-4">
              <p className="text-sm font-semibold text-gray-900 mb-2">
                Key Considerations
              </p>
              <ul className="space-y-2">
                {competitor.pricing.notes?.map((note, index) => (
                  <li key={index} className="text-xs text-gray-600 flex items-start">
                    <AlertCircle className="w-4 h-4 text-yellow-600 mr-2 flex-shrink-0 mt-0.5" />
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Cost Calculator */}
      {showCalculator && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg shadow-lg p-6">
          <div className="flex items-center mb-4">
            <Calculator className="w-6 h-6 text-blue-600 mr-3" />
            <h3 className="text-xl font-bold text-gray-900">
              Cost Comparison Calculator
            </h3>
          </div>

          <p className="text-sm text-gray-600 mb-6">
            Adjust the inputs below to see estimated costs for your practice size.
          </p>

          {/* Calculator Inputs */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {/* Practice Size */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Practice Size
              </label>
              <select
                value={practiceSize}
                onChange={(e) =>
                  setPracticeSize(e.target.value as 'small' | 'medium' | 'large')
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="small">Small (1-5 providers)</option>
                <option value="medium">Medium (6-20 providers)</option>
                <option value="large">Large (20+ providers)</option>
              </select>
            </div>

            {/* Monthly Claims Volume */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Monthly Claims ($)
              </label>
              <input
                type="number"
                value={monthlyClaimsVolume}
                onChange={(e) => setMonthlyClaimsVolume(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                step="50000"
              />
            </div>

            {/* Denial Rate */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Current Denial Rate (%)
              </label>
              <input
                type="number"
                value={denialRate}
                onChange={(e) => setDenialRate(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                step="0.1"
                min="0"
                max="100"
              />
            </div>
          </div>

          {/* Results */}
          <div className="bg-white rounded-lg p-6 shadow">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* Upstream Cost */}
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">
                  {upstream.company.name}
                </p>
                <p className="text-3xl font-bold text-blue-900">
                  ${upstreamMonthlyCost.toLocaleString()}/mo
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  ${upstreamAnnualCost.toLocaleString()}/year (fixed)
                </p>
              </div>

              {/* Competitor Cost */}
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">
                  {competitor.company.name} (estimated)
                </p>
                <p className="text-3xl font-bold text-yellow-900">
                  ${competitorMonthlyCost.toLocaleString()}/mo
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  ${competitorAnnualCost.toLocaleString()}/year (variable)
                </p>
              </div>
            </div>

            {/* Savings */}
            <div className="border-t border-gray-200 pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-700">
                    Annual Savings with {upstream.company.name}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    Based on {savingsPercentage.toFixed(0)}% cost reduction
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-green-600">
                    ${annualSavings.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">per year</p>
                </div>
              </div>
            </div>

            <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-xs text-blue-900 font-medium">
                💡 Plus: Additional ROI from Denial Prevention
              </p>
              <p className="text-xs text-blue-800 mt-1">
                If {upstream.company.name} reduces your denials by 25-35%, you'll save
                an additional $
                {(
                  monthlyClaimsVolume *
                  12 *
                  (denialRate / 100) *
                  0.3
                ).toLocaleString()}
                /year through prevention.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Hidden Costs Callout */}
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
        <div className="flex">
          <AlertCircle className="h-5 w-5 text-yellow-400 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">
              Hidden Costs with Percentage-Based Pricing
            </h3>
            <div className="mt-2 text-sm text-yellow-700">
              <ul className="list-disc list-inside space-y-1">
                <li>Variable monthly costs make budgeting difficult</li>
                <li>Higher denial rates = higher vendor fees (misaligned incentives)</li>
                <li>
                  Lack of pricing transparency can lead to unexpected bills
                </li>
                <li>Appeals overhead increases total cost of recovery</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingComparison;
