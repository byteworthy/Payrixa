/**
 * SocialProof Component
 *
 * Displays customer testimonials, case studies, ratings, and logos.
 * Emphasizes customers who switched from competitor to Upstream.
 *
 * Usage:
 * ```tsx
 * import SocialProof from '@/components/competitors/SocialProof';
 *
 * <SocialProof
 *   type="testimonials"
 *   competitorName="Adonis Intelligence"
 *   testimonials={[...]}
 * />
 * ```
 */

import React from 'react';
import { Star, Quote, TrendingUp, Building, Users } from 'lucide-react';

type SocialProofType = 'testimonials' | 'case-studies' | 'ratings' | 'logos' | 'stats';

interface Testimonial {
  quote: string;
  author: string;
  title: string;
  company: string;
  specialty: 'dialysis' | 'aba' | 'imaging' | 'home-health' | 'other';
  switchedFrom?: string;
  result?: string;
  avatar?: string;
}

interface CaseStudy {
  title: string;
  specialty: string;
  challenge: string;
  solution: string;
  results: string[];
  metrics?: {
    label: string;
    value: string;
    improvement: string;
  }[];
}

interface Rating {
  platform: string;
  rating: number;
  maxRating: number;
  reviewCount: number;
  logo?: string;
}

interface CompanyLogo {
  name: string;
  logo: string;
  specialty: string;
}

interface Stat {
  label: string;
  value: string;
  description: string;
  icon: React.ReactNode;
}

interface SocialProofProps {
  type: SocialProofType;
  competitorName?: string;
  testimonials?: Testimonial[];
  caseStudies?: CaseStudy[];
  ratings?: Rating[];
  logos?: CompanyLogo[];
  stats?: Stat[];
}

const SocialProof: React.FC<SocialProofProps> = ({
  type,
  competitorName,
  testimonials,
  caseStudies,
  ratings,
  logos,
  stats,
}) => {
  const renderTestimonials = () => {
    if (!testimonials || testimonials.length === 0) return null;

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h3 className="text-2xl font-bold text-gray-900">
            What Customers Say
          </h3>
          {competitorName && (
            <p className="mt-2 text-gray-600">
              Practices who switched from {competitorName} to Upstream
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              className="p-6 bg-white border border-gray-200 rounded-lg shadow-lg hover:shadow-xl transition-shadow"
            >
              {/* Quote Icon */}
              <Quote className="w-8 h-8 text-blue-600 mb-4" />

              {/* Switched Badge */}
              {testimonial.switchedFrom && (
                <div className="mb-3 inline-flex items-center px-3 py-1 rounded-full bg-green-100 border border-green-300">
                  <TrendingUp className="w-4 h-4 text-green-600 mr-2" />
                  <span className="text-xs font-semibold text-green-800">
                    Switched from {testimonial.switchedFrom}
                  </span>
                </div>
              )}

              {/* Quote */}
              <blockquote className="text-sm text-gray-700 mb-4 italic">
                "{testimonial.quote}"
              </blockquote>

              {/* Result (if provided) */}
              {testimonial.result && (
                <div className="mb-4 p-3 bg-green-50 rounded border border-green-200">
                  <p className="text-xs font-semibold text-green-900">
                    Result: {testimonial.result}
                  </p>
                </div>
              )}

              {/* Author */}
              <div className="border-t border-gray-200 pt-4">
                <div className="flex items-center">
                  {testimonial.avatar ? (
                    <img
                      src={testimonial.avatar}
                      alt={testimonial.author}
                      className="w-10 h-10 rounded-full mr-3"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center mr-3">
                      <span className="text-blue-600 font-bold text-sm">
                        {testimonial.author.charAt(0)}
                      </span>
                    </div>
                  )}
                  <div>
                    <p className="text-sm font-semibold text-gray-900">
                      {testimonial.author}
                    </p>
                    <p className="text-xs text-gray-600">{testimonial.title}</p>
                    <p className="text-xs text-gray-500">
                      {testimonial.company} ({testimonial.specialty})
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderCaseStudies = () => {
    if (!caseStudies || caseStudies.length === 0) return null;

    return (
      <div className="space-y-8">
        <div className="text-center">
          <h3 className="text-2xl font-bold text-gray-900">Case Studies</h3>
          <p className="mt-2 text-gray-600">
            Real-world results from practices using Upstream
          </p>
        </div>

        {caseStudies.map((study, index) => (
          <div
            key={index}
            className="p-8 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg shadow-lg"
          >
            <div className="flex items-start space-x-4">
              <Building className="w-8 h-8 text-blue-600 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h4 className="text-xl font-bold text-gray-900 mb-2">
                  {study.title}
                </h4>
                <p className="text-sm text-blue-800 font-semibold mb-4">
                  {study.specialty}
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  {/* Challenge */}
                  <div>
                    <p className="text-xs font-semibold text-gray-900 mb-2">
                      Challenge
                    </p>
                    <p className="text-sm text-gray-700">{study.challenge}</p>
                  </div>

                  {/* Solution */}
                  <div>
                    <p className="text-xs font-semibold text-gray-900 mb-2">
                      Solution
                    </p>
                    <p className="text-sm text-gray-700">{study.solution}</p>
                  </div>

                  {/* Results */}
                  <div>
                    <p className="text-xs font-semibold text-gray-900 mb-2">
                      Results
                    </p>
                    <ul className="space-y-1">
                      {study.results.map((result, resultIndex) => (
                        <li
                          key={resultIndex}
                          className="text-sm text-gray-700 flex items-start"
                        >
                          <span className="text-green-600 mr-2">✓</span>
                          <span>{result}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Metrics */}
                {study.metrics && study.metrics.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {study.metrics.map((metric, metricIndex) => (
                      <div
                        key={metricIndex}
                        className="p-4 bg-white rounded border border-blue-200"
                      >
                        <p className="text-xs text-gray-600 mb-1">
                          {metric.label}
                        </p>
                        <p className="text-2xl font-bold text-blue-900">
                          {metric.value}
                        </p>
                        <p className="text-xs text-green-600 font-semibold mt-1">
                          {metric.improvement}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderRatings = () => {
    if (!ratings || ratings.length === 0) return null;

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h3 className="text-2xl font-bold text-gray-900">
            Ratings & Reviews
          </h3>
          <p className="mt-2 text-gray-600">
            See what customers say on trusted review platforms
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {ratings.map((rating, index) => (
            <div
              key={index}
              className="p-6 bg-white border border-gray-200 rounded-lg shadow text-center"
            >
              {/* Platform Logo or Name */}
              {rating.logo ? (
                <img
                  src={rating.logo}
                  alt={rating.platform}
                  className="h-8 mx-auto mb-4"
                />
              ) : (
                <p className="text-lg font-bold text-gray-900 mb-4">
                  {rating.platform}
                </p>
              )}

              {/* Star Rating */}
              <div className="flex items-center justify-center mb-2">
                {Array.from({ length: rating.maxRating }).map((_, starIndex) => (
                  <Star
                    key={starIndex}
                    className={`w-6 h-6 ${
                      starIndex < Math.floor(rating.rating)
                        ? 'text-yellow-500 fill-yellow-500'
                        : starIndex < rating.rating
                        ? 'text-yellow-500'
                        : 'text-gray-300'
                    }`}
                  />
                ))}
              </div>

              {/* Rating Value */}
              <p className="text-2xl font-bold text-gray-900 mb-1">
                {rating.rating}/{rating.maxRating}
              </p>
              <p className="text-sm text-gray-600">
                Based on {rating.reviewCount} reviews
              </p>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderLogos = () => {
    if (!logos || logos.length === 0) return null;

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h3 className="text-2xl font-bold text-gray-900">
            Trusted by Leading Practices
          </h3>
          <p className="mt-2 text-gray-600">
            Dialysis centers, ABA clinics, imaging centers, and home health agencies
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {logos.map((logo, index) => (
            <div
              key={index}
              className="p-6 bg-white border border-gray-200 rounded-lg flex flex-col items-center justify-center hover:shadow-lg transition-shadow"
            >
              <img
                src={logo.logo}
                alt={logo.name}
                className="h-12 mb-3 object-contain"
              />
              <p className="text-xs text-gray-600 text-center">{logo.specialty}</p>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderStats = () => {
    if (!stats || stats.length === 0) return null;

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h3 className="text-2xl font-bold text-gray-900">By the Numbers</h3>
          <p className="mt-2 text-gray-600">
            Results from practices using Upstream
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg text-center"
            >
              <div className="flex justify-center mb-3 text-blue-600">
                {stat.icon}
              </div>
              <p className="text-3xl font-bold text-gray-900 mb-1">{stat.value}</p>
              <p className="text-sm font-semibold text-gray-900 mb-2">
                {stat.label}
              </p>
              <p className="text-xs text-gray-600">{stat.description}</p>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="social-proof w-full">
      {type === 'testimonials' && renderTestimonials()}
      {type === 'case-studies' && renderCaseStudies()}
      {type === 'ratings' && renderRatings()}
      {type === 'logos' && renderLogos()}
      {type === 'stats' && renderStats()}
    </div>
  );
};

export default SocialProof;
