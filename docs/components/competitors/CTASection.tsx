/**
 * CTASection Component
 *
 * Call-to-action component with multiple variants for competitor pages.
 * Optimized for conversion with clear value propositions.
 *
 * Usage:
 * ```tsx
 * import CTASection from '@/components/competitors/CTASection';
 *
 * <CTASection
 *   variant="demo"
 *   heading="See Upstream in Action"
 *   subheading="30-day implementation | Transparent pricing | Specialty-specific intelligence"
 *   competitorName="Adonis Intelligence"
 * />
 * ```
 */

import React from 'react';
import {
  ArrowRight,
  Calendar,
  Download,
  MessageCircle,
  Zap,
  FileText,
} from 'lucide-react';

type CTAVariant =
  | 'demo'
  | 'trial'
  | 'comparison-pdf'
  | 'talk-to-sales'
  | 'migration-call'
  | 'parallel-trial';

interface CTASectionProps {
  variant: CTAVariant;
  heading: string;
  subheading?: string;
  competitorName?: string;
  benefits?: string[];
  customCTA?: string;
  secondaryCTA?: {
    text: string;
    href: string;
  };
}

const CTASection: React.FC<CTASectionProps> = ({
  variant,
  heading,
  subheading,
  competitorName,
  benefits,
  customCTA,
  secondaryCTA,
}) => {
  const getVariantConfig = () => {
    switch (variant) {
      case 'demo':
        return {
          icon: <Calendar className="w-6 h-6" />,
          primaryCTA: customCTA || 'Schedule Demo',
          primaryHref: '/demo',
          bgGradient: 'from-blue-600 to-indigo-600',
          secondaryCTA: secondaryCTA || {
            text: 'See Pricing',
            href: '/pricing',
          },
        };
      case 'trial':
        return {
          icon: <Zap className="w-6 h-6" />,
          primaryCTA: customCTA || 'Start Free Trial',
          primaryHref: '/trial',
          bgGradient: 'from-green-600 to-emerald-600',
          secondaryCTA: secondaryCTA || {
            text: 'Talk to Sales',
            href: '/contact',
          },
        };
      case 'comparison-pdf':
        return {
          icon: <Download className="w-6 h-6" />,
          primaryCTA: customCTA || 'Download Comparison PDF',
          primaryHref: '/downloads/upstream-vs-competitor.pdf',
          bgGradient: 'from-purple-600 to-pink-600',
          secondaryCTA: secondaryCTA || {
            text: 'Schedule Demo',
            href: '/demo',
          },
        };
      case 'talk-to-sales':
        return {
          icon: <MessageCircle className="w-6 h-6" />,
          primaryCTA: customCTA || 'Talk to Sales',
          primaryHref: '/contact',
          bgGradient: 'from-indigo-600 to-purple-600',
          secondaryCTA: secondaryCTA || {
            text: 'See Pricing',
            href: '/pricing',
          },
        };
      case 'migration-call':
        return {
          icon: <ArrowRight className="w-6 h-6" />,
          primaryCTA: customCTA || 'Schedule Migration Call',
          primaryHref: '/migration',
          bgGradient: 'from-blue-600 to-cyan-600',
          secondaryCTA: secondaryCTA || {
            text: 'Download Migration Guide',
            href: '/downloads/migration-guide.pdf',
          },
        };
      case 'parallel-trial':
        return {
          icon: <Zap className="w-6 h-6" />,
          primaryCTA:
            customCTA ||
            `Run Parallel Trial with ${competitorName || 'Competitor'}`,
          primaryHref: '/parallel-trial',
          bgGradient: 'from-yellow-600 to-orange-600',
          secondaryCTA: secondaryCTA || {
            text: 'Talk to Sales',
            href: '/contact',
          },
        };
      default:
        return {
          icon: <Calendar className="w-6 h-6" />,
          primaryCTA: customCTA || 'Get Started',
          primaryHref: '/get-started',
          bgGradient: 'from-blue-600 to-indigo-600',
          secondaryCTA: secondaryCTA || {
            text: 'Learn More',
            href: '/about',
          },
        };
    }
  };

  const config = getVariantConfig();

  const defaultBenefits = [
    '30-day implementation',
    'Transparent fixed pricing',
    'Specialty-specific intelligence for dialysis, ABA, imaging, home health',
    'Dedicated onboarding support',
  ];

  const displayBenefits = benefits || defaultBenefits;

  return (
    <div className="cta-section w-full">
      <div
        className={`relative overflow-hidden rounded-2xl shadow-2xl bg-gradient-to-r ${config.bgGradient} text-white`}
      >
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <svg
            className="w-full h-full"
            viewBox="0 0 100 100"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              <pattern
                id="grid"
                width="10"
                height="10"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M 10 0 L 0 0 0 10"
                  fill="none"
                  stroke="white"
                  strokeWidth="0.5"
                />
              </pattern>
            </defs>
            <rect width="100" height="100" fill="url(#grid)" />
          </svg>
        </div>

        {/* Content */}
        <div className="relative p-8 md:p-12">
          <div className="max-w-4xl mx-auto">
            {/* Icon */}
            <div className="flex justify-center mb-6">{config.icon}</div>

            {/* Heading */}
            <h2 className="text-3xl md:text-4xl font-bold text-center mb-3">
              {heading}
            </h2>

            {/* Subheading */}
            {subheading && (
              <p className="text-lg md:text-xl text-center text-blue-100 mb-8">
                {subheading}
              </p>
            )}

            {/* Benefits Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-8 max-w-2xl mx-auto">
              {displayBenefits.map((benefit, index) => (
                <div
                  key={index}
                  className="flex items-start bg-white/10 backdrop-blur-sm rounded-lg p-3"
                >
                  <div className="flex-shrink-0 w-5 h-5 rounded-full bg-white/20 flex items-center justify-center mr-3 mt-0.5">
                    <span className="text-xs font-bold">✓</span>
                  </div>
                  <span className="text-sm">{benefit}</span>
                </div>
              ))}
            </div>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row justify-center items-center space-y-3 sm:space-y-0 sm:space-x-4">
              {/* Primary CTA */}
              <a
                href={config.primaryHref}
                className="inline-flex items-center px-8 py-4 bg-white text-blue-600 font-bold rounded-lg hover:bg-blue-50 transition-all hover:scale-105 shadow-lg"
              >
                <span>{config.primaryCTA}</span>
                <ArrowRight className="ml-2 w-5 h-5" />
              </a>

              {/* Secondary CTA */}
              {config.secondaryCTA && (
                <a
                  href={config.secondaryCTA.href}
                  className="inline-flex items-center px-6 py-3 border-2 border-white text-white font-semibold rounded-lg hover:bg-white/10 transition-all"
                >
                  {config.secondaryCTA.text}
                </a>
              )}
            </div>

            {/* Trust Signal */}
            <div className="mt-8 text-center">
              <p className="text-sm text-blue-100">
                {variant === 'trial' && '✓ No credit card required'}
                {variant === 'demo' && '✓ 30-minute personalized demo'}
                {variant === 'comparison-pdf' && '✓ Instant download, no signup'}
                {variant === 'parallel-trial' &&
                  `✓ Run alongside ${competitorName || 'competitor'} - no switching required`}
                {variant === 'migration-call' && '✓ Dedicated migration specialist'}
                {variant === 'talk-to-sales' && '✓ Custom pricing available'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Additional Context (Optional) */}
      {competitorName && variant === 'parallel-trial' && (
        <div className="mt-6 p-6 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start">
            <FileText className="w-6 h-6 text-blue-600 mr-3 flex-shrink-0 mt-1" />
            <div>
              <h4 className="text-sm font-bold text-gray-900 mb-1">
                Run Upstream & {competitorName} in Parallel
              </h4>
              <p className="text-sm text-gray-700">
                Many customers start by running both systems side-by-side for 60-90
                days. Compare performance, alert accuracy, and ROI before deciding
                which to keep. No commitment required.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CTASection;
