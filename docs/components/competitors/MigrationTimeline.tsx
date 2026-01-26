/**
 * MigrationTimeline Component
 *
 * Visual timeline showing the migration process from competitor to Upstream.
 * Emphasizes speed and simplicity of switching.
 *
 * Usage:
 * ```tsx
 * import MigrationTimeline from '@/components/competitors/MigrationTimeline';
 *
 * <MigrationTimeline
 *   competitorName="Adonis Intelligence"
 *   timeline="30"
 *   fastTrack={true}
 * />
 * ```
 */

import React from 'react';
import { Check, Clock, Zap, Users, Settings, Rocket } from 'lucide-react';

interface TimelinePhase {
  phase: string;
  days: string;
  title: string;
  activities: string[];
  icon: React.ReactNode;
  color: string;
}

interface MigrationTimelineProps {
  competitorName: string;
  timeline?: string; // Default "30"
  fastTrack?: boolean;
  parallelOperation?: boolean;
}

const MigrationTimeline: React.FC<MigrationTimelineProps> = ({
  competitorName,
  timeline = '30',
  fastTrack = true,
  parallelOperation = true,
}) => {
  const phases: TimelinePhase[] = [
    {
      phase: '1',
      days: 'Days 1-7',
      title: 'Kickoff & Data Connection',
      activities: [
        'Initial onboarding call with dedicated specialist',
        'Connect data feed from clearinghouse or set up CSV upload',
        'Verify historical claims data visibility (3-6 months preferred)',
        'No EHR vendor coordination required',
      ],
      icon: <Rocket className="w-6 h-6" />,
      color: 'blue',
    },
    {
      phase: '2',
      days: 'Days 8-20',
      title: 'Configuration & Specialty Rules Setup',
      activities: [
        'Configure specialty-specific rules (dialysis, ABA, imaging, home health)',
        'Set alert thresholds based on your denial tolerance',
        'Train staff on DriftWatch™ and DenialScope™ dashboards (1 day)',
        'Customize alert delivery (email, in-app, Slack integration)',
      ],
      icon: <Settings className="w-6 h-6" />,
      color: 'indigo',
    },
    {
      phase: '3',
      days: 'Days 21-30',
      title: 'Testing & Launch',
      activities: [
        'Test alert delivery and notification workflows',
        'Review first batch of early-warning alerts with onboarding specialist',
        'Go live with production monitoring',
        `Optionally run in parallel with ${competitorName} for validation`,
      ],
      icon: <Zap className="w-6 h-6" />,
      color: 'green',
    },
    {
      phase: '4',
      days: 'Ongoing',
      title: 'Support & Optimization',
      activities: [
        'Quarterly business reviews to refine alert rules',
        'Monitor denial rate improvements',
        'Adjust specialty-specific configurations as payer policies change',
        `Decide to cancel ${competitorName} after validating performance`,
      ],
      icon: <Users className="w-6 h-6" />,
      color: 'purple',
    },
  ];

  const getColorClasses = (color: string) => {
    const colors = {
      blue: {
        bg: 'bg-blue-100',
        border: 'border-blue-600',
        text: 'text-blue-900',
        icon: 'text-blue-600',
        badge: 'bg-blue-600',
      },
      indigo: {
        bg: 'bg-indigo-100',
        border: 'border-indigo-600',
        text: 'text-indigo-900',
        icon: 'text-indigo-600',
        badge: 'bg-indigo-600',
      },
      green: {
        bg: 'bg-green-100',
        border: 'border-green-600',
        text: 'text-green-900',
        icon: 'text-green-600',
        badge: 'bg-green-600',
      },
      purple: {
        bg: 'bg-purple-100',
        border: 'border-purple-600',
        text: 'text-purple-900',
        icon: 'text-purple-600',
        badge: 'bg-purple-600',
      },
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };

  return (
    <div className="migration-timeline w-full">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900">
          Migration from {competitorName}
        </h2>
        <p className="mt-2 text-lg text-gray-600">
          {timeline}-day implementation with no downtime
        </p>
        {fastTrack && (
          <div className="mt-3 inline-flex items-center px-4 py-2 rounded-full bg-yellow-100 border border-yellow-300">
            <Zap className="w-4 h-4 text-yellow-600 mr-2" />
            <span className="text-sm font-semibold text-yellow-900">
              Fast-track available: 2-week implementation for urgent needs
            </span>
          </div>
        )}
      </div>

      {/* Timeline (Desktop) */}
      <div className="hidden lg:block relative">
        {/* Connecting Line */}
        <div className="absolute top-12 left-0 w-full h-1 bg-gradient-to-r from-blue-300 via-indigo-300 via-green-300 to-purple-300"></div>

        <div className="grid grid-cols-4 gap-6">
          {phases.map((phase, index) => {
            const colorClasses = getColorClasses(phase.color);
            return (
              <div key={index} className="relative">
                {/* Phase Badge */}
                <div
                  className={`absolute -top-3 left-1/2 transform -translate-x-1/2 w-10 h-10 ${colorClasses.badge} text-white rounded-full flex items-center justify-center font-bold text-lg shadow-lg z-10`}
                >
                  {phase.phase}
                </div>

                {/* Phase Card */}
                <div
                  className={`mt-8 p-6 ${colorClasses.bg} border-2 ${colorClasses.border} rounded-lg shadow-lg`}
                >
                  <div className={`flex items-center justify-center mb-3 ${colorClasses.icon}`}>
                    {phase.icon}
                  </div>
                  <p className={`text-xs font-semibold ${colorClasses.text} text-center mb-1`}>
                    {phase.days}
                  </p>
                  <h3
                    className={`text-lg font-bold ${colorClasses.text} text-center mb-3`}
                  >
                    {phase.title}
                  </h3>
                  <ul className="space-y-2">
                    {phase.activities.map((activity, actIndex) => (
                      <li
                        key={actIndex}
                        className="text-sm text-gray-700 flex items-start"
                      >
                        <Check className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                        <span>{activity}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Timeline (Mobile) */}
      <div className="lg:hidden space-y-6">
        {phases.map((phase, index) => {
          const colorClasses = getColorClasses(phase.color);
          return (
            <div key={index} className="relative pl-12">
              {/* Connecting Line */}
              {index < phases.length - 1 && (
                <div
                  className={`absolute left-5 top-12 w-0.5 h-full ${colorClasses.badge}`}
                ></div>
              )}

              {/* Phase Badge */}
              <div
                className={`absolute left-0 top-0 w-10 h-10 ${colorClasses.badge} text-white rounded-full flex items-center justify-center font-bold text-lg shadow-lg`}
              >
                {phase.phase}
              </div>

              {/* Phase Card */}
              <div
                className={`p-4 ${colorClasses.bg} border-2 ${colorClasses.border} rounded-lg shadow-lg`}
              >
                <div className={`flex items-center mb-2 ${colorClasses.icon}`}>
                  {phase.icon}
                  <p className={`ml-2 text-xs font-semibold ${colorClasses.text}`}>
                    {phase.days}
                  </p>
                </div>
                <h3 className={`text-lg font-bold ${colorClasses.text} mb-3`}>
                  {phase.title}
                </h3>
                <ul className="space-y-2">
                  {phase.activities.map((activity, actIndex) => (
                    <li
                      key={actIndex}
                      className="text-sm text-gray-700 flex items-start"
                    >
                      <Check className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                      <span>{activity}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          );
        })}
      </div>

      {/* Key Benefits */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <Clock className="w-6 h-6 text-blue-600 mb-2" />
          <h4 className="text-sm font-bold text-gray-900 mb-1">
            {timeline}-Day Timeline
          </h4>
          <p className="text-xs text-gray-600">
            6x faster than {competitorName}'s 3-6 month EHR integration
          </p>
        </div>

        {parallelOperation && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <Zap className="w-6 h-6 text-green-600 mb-2" />
            <h4 className="text-sm font-bold text-gray-900 mb-1">
              No Downtime
            </h4>
            <p className="text-xs text-gray-600">
              Run in parallel with {competitorName} during transition - validate
              performance before canceling
            </p>
          </div>
        )}

        <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
          <Users className="w-6 h-6 text-purple-600 mb-2" />
          <h4 className="text-sm font-bold text-gray-900 mb-1">
            Dedicated Support
          </h4>
          <p className="text-xs text-gray-600">
            Onboarding specialist guides you through each phase - no IT resources
            required
          </p>
        </div>
      </div>

      {/* What Transfers / Doesn't Transfer */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 bg-white border border-gray-200 rounded-lg shadow">
          <h4 className="text-lg font-bold text-gray-900 mb-3">
            What Transfers
          </h4>
          <ul className="space-y-2">
            <li className="text-sm text-gray-700 flex items-start">
              <Check className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
              <span>
                Historical claims data (3-6 months) used to establish payer behavior
                baseline
              </span>
            </li>
            <li className="text-sm text-gray-700 flex items-start">
              <Check className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
              <span>Your team's domain expertise (translated into custom rules)</span>
            </li>
            <li className="text-sm text-gray-700 flex items-start">
              <Check className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
              <span>
                Denial patterns and pain points (inform alert configuration)
              </span>
            </li>
          </ul>
        </div>

        <div className="p-6 bg-white border border-gray-200 rounded-lg shadow">
          <h4 className="text-lg font-bold text-gray-900 mb-3">
            What Doesn't Transfer
          </h4>
          <ul className="space-y-2">
            <li className="text-sm text-gray-600 flex items-start">
              <span className="text-yellow-600 mr-2 flex-shrink-0 mt-0.5">✗</span>
              <span>
                {competitorName} alert configurations (fresh start with Upstream's
                methodology)
              </span>
            </li>
            <li className="text-sm text-gray-600 flex items-start">
              <span className="text-yellow-600 mr-2 flex-shrink-0 mt-0.5">✗</span>
              <span>
                EHR integration settings ({competitorName}-specific, Upstream is
                EHR-independent)
              </span>
            </li>
            <li className="text-sm text-gray-600 flex items-start">
              <span className="text-yellow-600 mr-2 flex-shrink-0 mt-0.5">✗</span>
              <span>
                Custom workflows in athenahealth/AdvancedMD/eCW (Upstream uses
                separate dashboard)
              </span>
            </li>
          </ul>
        </div>
      </div>

      {/* CTA */}
      <div className="mt-8 p-6 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg text-white text-center">
        <h3 className="text-2xl font-bold mb-2">Ready to Switch?</h3>
        <p className="text-blue-100 mb-4">
          Start your {timeline}-day migration with dedicated onboarding support
        </p>
        <button className="px-6 py-3 bg-white text-blue-600 font-semibold rounded-lg hover:bg-blue-50 transition-colors">
          Schedule Migration Call
        </button>
      </div>
    </div>
  );
};

export default MigrationTimeline;
